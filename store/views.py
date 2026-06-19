from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from .models import Product, ReviewRating, Wishlist
from .forms import ReviewForm
from category.models import Category
from carts.models import CartItem
from django.db.models import Q
from carts.views import _cart_id
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator

def store(request, category_slug=None):
    categories = None
    products = Product.objects.filter(is_available=True).order_by('id')

    if category_slug != None:
        categories = get_object_or_404(Category, slug=category_slug)
        products = products.filter(Category=categories)
        
    get_category = request.GET.get('category')
    if get_category and get_category != 'all':
        categories = get_object_or_404(Category, slug=get_category)
        products = products.filter(Category=categories)

    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    if min_price:
        try:
            products = products.filter(price__gte=float(min_price))
        except ValueError:
            pass

    if max_price:
        try:
            products = products.filter(price__lte=float(max_price))
        except ValueError:
            pass

    paginator = Paginator(products, 9)
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)
    product_count = products.count()

    # Get wishlist product IDs for the current user
    wishlist_ids = []
    if request.user.is_authenticated:
        wishlist_ids = list(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True))

    context = {
        'products': paged_products,
        'product_count': product_count,
        'wishlist_ids': wishlist_ids,
    }
    return render(request, 'store/store.html', context)


def product_detail(request, category_slug, product_slug):
    try:
        single_product = Product.objects.get(Category__slug=category_slug, slug=product_slug)
        if request.user.is_authenticated:
            in_cart = CartItem.objects.filter(user=request.user, product=single_product).exists()
        else:
            in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=single_product).exists()
    except Exception as e:
        raise e

    # Get the reviews
    reviews = ReviewRating.objects.filter(product_id=single_product.id, status=True)

    # Check if in wishlist
    in_wishlist = False
    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(user=request.user, product=single_product).exists()

    context = {
        'single_product': single_product,
        'in_cart': in_cart,
        'reviews': reviews,
        'in_wishlist': in_wishlist,
    }
    return render(request, 'store/product_detail.html', context)


def search(request):
    products = None
    product_count = 0
    
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            products = Product.objects.filter(
                Q(description__icontains=keyword) | Q(product_name__icontains=keyword),
                is_available=True
            ).order_by('-created_date')
            product_count = products.count()
    
    context = {
        'products': products,
        'product_count': product_count,
        'keyword': request.GET.get('keyword', ''),
    }
    return render(request, 'store/store.html', context)

def submit_review(request, product_id):
    url = request.META.get('HTTP_REFERER')
    if request.method == 'POST':
        try:
            reviews = ReviewRating.objects.get(user__id=request.user.id, product__id=product_id)
            form = ReviewForm(request.POST, instance=reviews)
            form.save()
            messages.success(request, '¡Gracias! Tu reseña ha sido actualizada.')
            return redirect(url)
        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data['subject']
                data.rating = form.cleaned_data['rating']
                data.review = form.cleaned_data['review']
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id = product_id
                data.user_id = request.user.id
                data.save()
                messages.success(request, '¡Gracias! Tu reseña ha sido enviada.')
                return redirect(url)
    return redirect(url)


@require_POST
def toggle_wishlist(request, product_id):
    """AJAX toggle: add/remove a product from the user's wishlist."""
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'login_required'}, status=401)

    product = get_object_or_404(Product, id=product_id)
    wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)

    if not created:
        wishlist_item.delete()
        return JsonResponse({'status': 'removed', 'added': False})
    else:
        return JsonResponse({'status': 'added', 'added': True})


@login_required(login_url='login')
def remove_wishlist(request, product_id):
    """Remove from wishlist (used from dashboard page)."""
    product = get_object_or_404(Product, id=product_id)
    Wishlist.objects.filter(user=request.user, product=product).delete()
    messages.success(request, 'Producto eliminado de tu lista de deseos.')
    return redirect('dashboard')