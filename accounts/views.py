from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import render, redirect

def login_view(request):
    if request.method=='POST':
        user=authenticate(request,username=request.POST.get('username'),password=request.POST.get('password'))
        if user: login(request,user); return redirect('home')
        messages.error(request,'Invalid username or password.')
    return render(request,'customer/login.html')
def signup(request):
    if request.method=='POST':
        username=request.POST.get('username'); email=request.POST.get('email'); p1=request.POST.get('password'); p2=request.POST.get('confirm_password')
        if p1!=p2: messages.error(request,'Passwords do not match.')
        elif User.objects.filter(username=username).exists(): messages.error(request,'Username already exists.')
        else: User.objects.create_user(username=username,email=email,password=p1); messages.success(request,'Account created. Please login.'); return redirect('login')
    return render(request,'customer/register.html')
def logout_view(request): logout(request); return redirect('home')
def profile(request): return render(request,'customer/profile.html')
