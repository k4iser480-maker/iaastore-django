from django.contrib import admin
from .models import Product, ProductFeature

class ProductFeatureInline(admin.TabularInline):
    model = ProductFeature
    extra = 1

class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'price', 'stock', 'Category', 'modified_date', 'is_available')
    prepopulated_fields = {'slug': ('product_name',)}
    inlines = [ProductFeatureInline]

admin.site.register(Product, ProductAdmin)
