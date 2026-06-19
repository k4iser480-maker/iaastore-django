from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from store.models import Product, Wishlist
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Ticket

from django.db import models
from django.db.models import Avg, Count, Q

def home(request):
    # Productos Populares: order by highest average rating and review count
    popular_products = Product.objects.filter(is_available=True).annotate(
        avg_rating=Avg('reviewrating__rating', filter=Q(reviewrating__status=True)),
        review_count=Count('reviewrating', filter=Q(reviewrating__status=True))
    ).order_by('-avg_rating', '-review_count')[:8]

    # Productos Recientes: order by creation date
    recent_products = Product.objects.filter(is_available=True).order_by('-created_date')[:8]

    # Productos en Oferta: random products on sale
    sale_products = Product.objects.filter(is_available=True, is_on_sale=True).order_by('?')[:8]

    wishlist_ids = []
    if request.user.is_authenticated:
        wishlist_ids = list(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True))

    context = {
        'popular_products': popular_products,
        'recent_products': recent_products,
        'sale_products': sale_products,
        'wishlist_ids': wishlist_ids,
    }

    return render(request, 'home.html', context)

def about(request):
    return render(request, 'about.html')

def set_currency(request):
    currency = request.GET.get('currency', 'USD')
    if currency in ['USD', 'VES']:
        request.session['currency'] = currency
    # Redirect to previous page or home
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('home')

def contact_form(request):
    if request.method == 'POST':
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        message = request.POST.get('message', '')

        subject = f'Nuevo mensaje de contacto de {name}'
        body = (
            f'Nombre: {name}\n'
            f'Correo: {email}\n'
            f'Teléfono: {phone}\n\n'
            f'Mensaje:\n{message}'
        )

        try:
            send_mail(
                subject,
                body,
                settings.EMAIL_HOST_USER,
                [settings.EMAIL_HOST_USER],  # envía al correo de la empresa
                fail_silently=False,
            )
            messages.success(request, '¡Tu mensaje ha sido enviado exitosamente! Te responderemos a la brevedad.')
        except Exception:
            messages.error(request, 'Ocurrió un error al enviar tu mensaje. Por favor, intenta de nuevo más tarde.')

        return redirect('about')

    return redirect('about')

def help_page(request):
    return render(request, 'help.html')

@api_view(['POST'])
def create_ticket(request):
    data = request.data
    
    ticket = Ticket.objects.create(
        name=data.get('name'),
        email=data.get('email'),
        order_id=data.get('order_id', ''),
        issue=data.get('issue')
    )

    return Response({"status": "ok", "ticket_id": ticket.id})


import json
import time
from django.http import JsonResponse
from .chatbot_engine import ChatEngine
from .models import ChatSession, ChatMessage

def chat_message(request):
    """Endpoint principal del chatbot Helper."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    # --- Parse input ---
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    user_message = data.get('message', '').strip()
    button_value = data.get('button', '').strip()
    message = button_value or user_message

    if not message or len(message) > 500:
        return JsonResponse({'error': 'Invalid message'}, status=400)

    # --- Get or create session ---
    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key

    chat_session, created = ChatSession.objects.get_or_create(
        session_key=session_key,
        defaults={
            'user': request.user if request.user.is_authenticated else None
        }
    )

    # Fusión anón → user (si el usuario hizo login después)
    if request.user.is_authenticated and not chat_session.user:
        chat_session.user = request.user
        chat_session.save()

    # --- Rate limiting (30 msgs/min, stored in DB) ---
    now = time.time()
    timestamps = chat_session.message_timestamps or []
    timestamps = [t for t in timestamps if now - t < 60]
    if len(timestamps) >= 30:
        return JsonResponse({'error': 'Demasiados mensajes. Espera un momento.'}, status=429)
    timestamps.append(now)
    chat_session.message_timestamps = timestamps
    chat_session.save()

    # --- Log user message ---
    ChatMessage.objects.create(
        session=chat_session, sender='user', text=message
    )

    # --- Process ---
    engine = ChatEngine()
    response = engine.process(message, chat_session)

    # --- Log bot responses ---
    intent = response.get('intent', '')
    confidence = response.get('confidence', 0.0)
    for msg in response.get('messages', []):
        ChatMessage.objects.create(
            session=chat_session, sender='bot', text=msg['text'],
            intent_detected=intent, confidence=confidence,
        )

    return JsonResponse(response)

