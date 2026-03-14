from django.shortcuts import render, redirect
from django.contrib import auth, messages
from .models import Account


def register(request):
    if request.method == 'POST':
        first_name = request.POST['first_name']
        last_name  = request.POST['last_name']
        email      = request.POST['email']
        password   = request.POST['password']
        username   = email.split('@')[0]

        if Account.objects.filter(email=email).exists():
            messages.error(request, 'Este correo ya está registrado.')
            return redirect('register')

        user = Account.objects.create_user(
            first_name=first_name, last_name=last_name,
            username=username, email=email, password=password
        )
        messages.success(request, 'Cuenta creada exitosamente. Inicia sesión.')
        return redirect('login')
    return render(request, 'accounts/register.html')


def login(request):
    if request.method == 'POST':
        email    = request.POST['email']
        password = request.POST['password']
        user = auth.authenticate(email=email, password=password)
        if user:
            auth.login(request, user)
            return redirect('home')
        messages.error(request, 'Credenciales inválidas.')
    return render(request, 'accounts/login.html')


def logout(request):
    auth.logout(request)
    return redirect('login')


def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'accounts/dashboard.html')
