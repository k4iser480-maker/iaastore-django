from django.shortcuts import render, get_object_or_404, redirect
from .models import Product
from category.models import Category

def store(request, category_slug=None):
    selected_category = None
    products = None

    if category_slug is not None:
        selected_category = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(Category=selected_category, is_available=True)
        product_count = products.count()
    else:
        products = Product.objects.filter(is_available=True)
        product_count = products.count()

    context = {
        'products': products,
        'product_count': product_count,
    }

    return render(request, 'store/store.html', context)

def search(request):
    """Basic search handler invoked from the navbar form.

    * if the keyword contains two slash-separated slugs ("categoria/producto")
      attempt to redirect directly to the detail page
    * otherwise perform a simple case‑insensitive match against
      ``product_name`` and render the normal store listing template
    * if the keyword is missing or the lookup fails just fall back to the
      store homepage
    """

    keyword = request.GET.get('keyword', '').strip()
    if not keyword:
        return redirect('store')

    # try to interpret as category/product slugs first
    parts = keyword.strip('/').split('/')
    if len(parts) == 2:
        cat_slug, prod_slug = parts
        if cat_slug and prod_slug:
            try:
                # redirect will trigger the product_detail view which now uses
                # the correct field name and loads the object into context
                return redirect('product_detail', category_slug=cat_slug, product_slug=prod_slug)
            except Exception:
                # if the slug combination doesn't resolve, fall through and
                # render the search results below rather than crashing
                pass

    # generic product name search
    products = Product.objects.filter(product_name__icontains=keyword, is_available=True)
    product_count = products.count()
    context = {'products': products, 'product_count': product_count}
    return render(request, 'store/store.html', context)



def product_detail(request, category_slug, product_slug):
    # ensure we query using the actual foreign‑key name (capital "Category").
    # ``get_object_or_404`` returns a proper 404 instead of raising a generic
    # exception and it keeps the template context intact.
    single_product = get_object_or_404(
        Product,
        Category__slug=category_slug,
        slug=product_slug,
        is_available=True,
    )
    context = {
        'single_product': single_product,
    }
    return render(request, 'store/product_detail.html', context)