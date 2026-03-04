from django.shortcuts import render
from store.models import Product

def home(request):
    # grab a handful of available products to show on the landing page; you
    # can replace this with a proper "popular" query later (e.g. by ratings
    # or sales).
    products = Product.objects.filter(is_available=True)[:8]

    context = {
        'products': products,
    }

    return render(request, 'home.html', context)