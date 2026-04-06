"""
Views for user authentication.

This module handles user registration, login, and logout.
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.conf import settings
import stripe
import json

from .forms import UserRegistrationForm, UserLoginForm
from .models import UserProfile


def register(request):
    """User registration view."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Account created for {user.username}! You can now log in.')
            return redirect('users:login')
    else:
        form = UserRegistrationForm()

    return render(request, 'users/register.html', {'form': form})


def login_view(request):
    """User login view."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = UserLoginForm()

    return render(request, 'users/login.html', {'form': form})


@login_required
def logout_view(request):
    """User logout view."""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('movies:home')

@login_required
def create_checkout_session(request):
    """Create a Stripe checkout session for Premium subscription."""
    stripe.api_key = settings.STRIPE_SECRET_KEY
    
    if request.method == 'POST':
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price_data': {
                            'currency': 'usd',
                            'unit_amount': 999,  # $9.99/mo
                            'product_data': {
                                'name': 'AI Movie Premium Subscription',
                            },
                        },
                        'quantity': 1,
                    },
                ],
                mode='payment',
                success_url=request.build_absolute_uri('/') + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=request.build_absolute_uri('/'),
                client_reference_id=request.user.id,
            )
            return JsonResponse({'id': checkout_session.id})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return redirect('movies:dashboard')

@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhooks."""
    stripe.api_key = settings.STRIPE_SECRET_KEY
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        # In production use stripe.Webhook.construct_event with endpoint_secret
        event = stripe.Event.construct_from(json.loads(payload), stripe.api_key)
    except Exception as e:
        return HttpResponse(status=400)
        
    if event.type == 'checkout.session.completed':
        session = event.data.object
        user_id = session.get('client_reference_id')
        if user_id:
            try:
                profile = UserProfile.objects.get(user_id=user_id)
                profile.is_premium = True
                profile.stripe_customer_id = session.get('customer')
                profile.save()
            except UserProfile.DoesNotExist:
                pass
                
    return HttpResponse(status=200)
