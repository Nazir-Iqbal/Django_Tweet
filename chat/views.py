import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, StreamingHttpResponse
from django.conf import settings
from .models import Conversation, Message, AIAssist
from accounts.models import User
import openai
import anthropic


@login_required
def home(request):
    conversations = Conversation.objects.filter(participants=request.user)
    return render(request, 'chat/home.html', {
        'conversations': conversations,
        'llm_models': settings.LLM_MODELS,
    })


@login_required
def conversation_view(request, conv_id):
    conversation = get_object_or_404(Conversation, id=conv_id, participants=request.user)
    messages = conversation.messages.select_related('sender').all()
    other = conversation.get_other_participant(request.user)
    return render(request, 'chat/conversation.html', {
        'conversation': conversation,
        'messages': messages,
        'other_user': other,
        'conversations': Conversation.objects.filter(participants=request.user),
        'llm_models': settings.LLM_MODELS,
    })


@login_required
def start_conversation(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        other_user = get_object_or_404(User, id=user_id)
        existing = Conversation.objects.filter(
            participants=request.user
        ).filter(participants=other_user)
        for conv in existing:
            if conv.participants.count() == 2:
                return redirect('conversation', conv_id=conv.id)
        conv = Conversation.objects.create()
        conv.participants.add(request.user, other_user)
        return redirect('conversation', conv_id=conv.id)
    return redirect('home')


@login_required
def send_message(request, conv_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    conversation = get_object_or_404(Conversation, id=conv_id, participants=request.user)
    data = json.loads(request.body)
    content = data.get('content', '').strip()
    if not content:
        return JsonResponse({'error': 'Empty message'}, status=400)

    msg = Message.objects.create(
        conversation=conversation,
        sender=request.user,
        content=content,
    )
    conversation.save()

    return JsonResponse({
        'id': msg.id,
        'content': msg.content,
        'sender': msg.sender.username,
        'initials': msg.sender.get_initials(),
        'color': msg.sender.avatar_color,
        'created_at': msg.created_at.isoformat(),
    })


@login_required
def fetch_messages(request, conv_id):
    conversation = get_object_or_404(Conversation, id=conv_id, participants=request.user)
    after_id = request.GET.get('after', 0)
    messages = conversation.messages.filter(id__gt=after_id).select_related('sender')
    return JsonResponse({
        'messages': [
            {
                'id': m.id,
                'content': m.content,
                'sender': m.sender.username,
                'initials': m.sender.get_initials(),
                'color': m.sender.avatar_color,
                'created_at': m.created_at.isoformat(),
            }
            for m in messages
        ]
    })


# ── AI Assist helpers ──

SENTIMENT_SYSTEM_PROMPT = """You are a chat assistant embedded in a messaging app.
The user is having a conversation with another person. Your job:
1. Analyze the overall SENTIMENT of the conversation (e.g. friendly, tense, romantic, professional, upset, neutral, excited, etc.)
2. Based on that sentiment and the last few messages, suggest a thoughtful reply the user could send.
3. Keep suggestions natural, concise, and matching the conversation tone.

Format your response EXACTLY like this:
SENTIMENT: <one or two words>
CONTEXT: <one sentence summary of the conversation mood>
---
<your suggested reply message — just the message text, nothing else>"""


def _get_provider(model_name):
    for provider, models in settings.LLM_MODELS.items():
        if model_name in models:
            return provider
    return None


def _build_assist_messages(conversation, requesting_user):
    other = conversation.get_other_participant(requesting_user)
    other_name = other.get_full_name() or other.username if other else "the other person"
    recent = conversation.messages.select_related('sender').order_by('-created_at')[:30]
    recent = list(reversed(recent))

    chat_transcript = ""
    for m in recent:
        label = "You" if m.sender == requesting_user else other_name
        chat_transcript += f"{label}: {m.content}\n"

    return [
        {"role": "system", "content": SENTIMENT_SYSTEM_PROMPT},
        {"role": "user", "content": f"Here is the recent conversation between the user and {other_name}:\n\n{chat_transcript}\n\nPlease analyze the sentiment and suggest a reply for the user."},
    ]


def _stream_openai(messages_history, model_name):
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    api_model = settings.LLM_MODEL_MAP.get(model_name, 'gpt-4o-mini')
    stream = client.chat.completions.create(
        model=api_model,
        messages=messages_history,
        stream=True,
    )
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


def _stream_claude(messages_history, model_name):
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    api_model = settings.LLM_MODEL_MAP.get(model_name, 'claude-sonnet-4-20250514')
    system_msg = ""
    filtered = []
    for m in messages_history:
        if m['role'] == 'system':
            system_msg = m['content']
        else:
            filtered.append(m)
    with client.messages.stream(
        model=api_model,
        max_tokens=1024,
        system=system_msg,
        messages=filtered,
    ) as stream:
        for text in stream.text_stream:
            yield text


@login_required
def ai_assist_stream(request, conv_id):
    """Stream AI sentiment analysis + reply suggestion for a conversation."""
    conversation = get_object_or_404(Conversation, id=conv_id, participants=request.user)
    model_name = request.GET.get('model', 'GPT-4o Mini')
    provider = _get_provider(model_name)

    if not provider or provider == 'gemini':
        return JsonResponse({'error': f'Provider not configured for {model_name}'}, status=400)

    if conversation.messages.count() == 0:
        return JsonResponse({'error': 'No messages to analyze yet'}, status=400)

    messages_history = _build_assist_messages(conversation, request.user)

    def event_stream():
        full_response = []
        try:
            streamer = _stream_openai if provider == 'openai' else _stream_claude
            for token in streamer(messages_history, model_name):
                full_response.append(token)
                yield f"data: {json.dumps({'token': token})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

        full_text = ''.join(full_response)
        if full_text:
            sentiment = ""
            context_summary = ""
            suggestion = full_text
            if "SENTIMENT:" in full_text and "---" in full_text:
                header, _, suggestion = full_text.partition("---")
                suggestion = suggestion.strip()
                for line in header.split("\n"):
                    line = line.strip()
                    if line.startswith("SENTIMENT:"):
                        sentiment = line.replace("SENTIMENT:", "").strip()
                    elif line.startswith("CONTEXT:"):
                        context_summary = line.replace("CONTEXT:", "").strip()
            AIAssist.objects.create(
                conversation=conversation,
                user=request.user,
                model_used=model_name,
                sentiment=sentiment,
                suggestion=suggestion,
                context_summary=context_summary,
            )
        yield "data: [DONE]\n\n"

    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response
