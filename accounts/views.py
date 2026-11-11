from django.shortcuts import render, redirect
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from .models import User


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'authentication/register.html', {'form': form})


def profile(request):
    return render(request, 'accounts/profile.html')

def logout_view(request):
    auth_logout(request)
    return redirect('login')
