from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout


def home(request):
    """Landing page"""
    return render(request, 'home.html')


def login_page(request):
    """Login page"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    
    return render(request, 'login.html')


def logout_view(request):
    """Logout"""
    logout(request)
    return redirect('home')


@login_required(login_url='login')
def dashboard(request):
    """Main dashboard"""
    return render(request, 'dashboard.html')


@login_required(login_url='login')
def transactions_page(request):
    """Transactions page"""
    return render(request, 'transactions.html')


@login_required(login_url='login')
def budget_page(request):
    """Budget recommendations page"""
    return render(request, 'budget.html')


@login_required(login_url='login')
def profile_page(request):
    """User profile page"""
    return render(request, 'profile.html')