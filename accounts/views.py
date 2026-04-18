from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .forms import SignUpForm, ProfileForm
from .models import User


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'accounts/signup.html', {'form': form})


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def toggle_theme(request):
    if request.method == 'POST':
        user = request.user
        user.theme = 'light' if user.theme == 'dark' else 'dark'
        user.save(update_fields=['theme'])
        return JsonResponse({'theme': user.theme})
    return JsonResponse({'error': 'POST required'}, status=405)


@login_required
def user_search(request):
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'users': []})
    users = User.objects.filter(
        username__icontains=query
    ).exclude(id=request.user.id)[:10]
    return JsonResponse({
        'users': [
            {'id': u.id, 'username': u.username, 'initials': u.get_initials(), 'color': u.avatar_color}
            for u in users
        ]
    })
