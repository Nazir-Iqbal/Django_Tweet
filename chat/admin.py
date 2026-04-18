from django.contrib import admin
from .models import Conversation, Message, AIAssist


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'updated_at', 'created_at')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'sender', 'created_at')


@admin.register(AIAssist)
class AIAssistAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'user', 'model_used', 'sentiment', 'created_at')
