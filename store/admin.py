from django.contrib import admin
from .models import Product, ProductFeature, ReviewRating, Wishlist

class ProductFeatureInline(admin.TabularInline):
    model = ProductFeature
    extra = 1

class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'price', 'stock', 'Category', 'modified_date', 'is_available')
    prepopulated_fields = {'slug': ('product_name',)}
    inlines = [ProductFeatureInline]

class ReviewRatingAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'subject', 'rating', 'status', 'created_at')
    list_filter = ('status', 'rating')
    search_fields = ('subject', 'review', 'user__username', 'product__product_name')

admin.site.register(Product, ProductAdmin)
admin.site.register(ReviewRating, ReviewRatingAdmin)

class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'created_at')
    list_filter = ('created_at',)

admin.site.register(Wishlist, WishlistAdmin)
