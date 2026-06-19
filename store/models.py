import re
import unicodedata
from django.db import models
from django.db.models import Count
from django.urls import reverse
from django.core.validators import MinValueValidator
from category.models import Category

class Product(models.Model):
    product_name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    sku = models.CharField(max_length=50, unique=True, db_index=True)
    description = models.TextField(max_length=500, blank=True)
    price = models.IntegerField()
    images = models.ImageField(upload_to='photos/products', blank=True, null=True)
    stock = models.IntegerField()
    is_available = models.BooleanField(default=True)
    is_on_sale = models.BooleanField(default=False)
    old_price = models.IntegerField(null=True, blank=True)
    gross_weight = models.FloatField(default=0.0, validators=[MinValueValidator(0.0)])
    length = models.FloatField(default=0.0, validators=[MinValueValidator(0.0)])
    width = models.FloatField(default=0.0, validators=[MinValueValidator(0.0)])
    height = models.FloatField(default=0.0, validators=[MinValueValidator(0.0)])
    
    UNIT_CHOICES = [
        ('cm', 'cm'),
        ('m', 'm')
    ]
    length_unit = models.CharField(max_length=2, choices=UNIT_CHOICES, default='cm')
    width_unit = models.CharField(max_length=2, choices=UNIT_CHOICES, default='cm')
    height_unit = models.CharField(max_length=2, choices=UNIT_CHOICES, default='cm')
    
    Category = models.ForeignKey('category.Category', on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    def get_url(self):
        # use the related category slug (``Category`` field is capitalized)
        return reverse('product_detail', args=[self.Category.slug, self.slug])
        
    def save(self, *args, **kwargs):
        if not self.sku:
            self.sku = self._generate_sku()
        super().save(*args, **kwargs)

    def _generate_sku(self):
        if not getattr(self, 'Category', None) or not self.product_name:
            return None
        
        def normalize_text(text):
            text = unicodedata.normalize('NFKD', str(text)).encode('ASCII', 'ignore').decode('utf-8')
            return text.upper()
            
        cat = normalize_text(self.Category.category_name)[:3]
        
        words = normalize_text(self.product_name).split()
        first_word = words[0] if words else "GEN"
        tipo = "TRN" if first_word == 'TORNILLO' else first_word[:3]
        
        name = normalize_text(self.product_name)
        medida = ""
        # Dimensions like 3X5, 4X2
        match = re.search(r'\b\d+\s*[X]\s*\d+\b', name)
        if match:
            medida = match.group(0).replace(' ', '')
        else:
            # Fractions like 1/2
            match = re.search(r'\b\d+/\d+\b', name)
            if match:
                medida = match.group(0).replace('/', '')
            else:
                # Measurements with units
                match = re.search(r'\b(\d+(?:\.\d+)?)\s*(PULGADA|PULGADAS|PULG|IN|CM|MM|M|KG|LBS?)\b', name)
                if match:
                    num = match.group(1).replace('.', '')
                    unit = match.group(2)
                    if unit in ['PULGADA', 'PULGADAS', 'PULG']:
                        unit = 'IN'
                    medida = f"{num}{unit}"
                    
        prefix = f"{cat}-{tipo}-{medida}" if medida else f"{cat}-{tipo}"
        
        last_product = Product.objects.filter(sku__startswith=f"{prefix}-").order_by('-sku').first()
        if last_product and last_product.sku:
            try:
                last_seq = int(last_product.sku.split('-')[-1])
                new_seq = last_seq + 1
            except ValueError:
                new_seq = 1
        else:
            new_seq = 1
            
        return f"{prefix}-{new_seq:04d}"

    def __str__(self):
        return self.product_name

    def countReview(self):
        reviews = ReviewRating.objects.filter(product=self, status=True).aggregate(count=Count('id'))
        count = 0
        if reviews['count'] is not None:
            count = int(reviews['count'])
        return count

    def averageReview(self):
        # Calculate the mode of the ratings (most frequent rating)
        reviews = ReviewRating.objects.filter(product=self, status=True).values('rating').annotate(count=Count('rating')).order_by('-count', '-rating')
        if reviews:
            return float(reviews[0]['rating'])
        return 0

class ProductFeature(models.Model):
    product = models.ForeignKey(Product, related_name='features', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.name}: {self.value}"

from accounts.models import Account

class ReviewRating(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100, blank=True)
    review = models.TextField(max_length=500, blank=True)
    rating = models.FloatField()
    ip = models.CharField(max_length=20, blank=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.subject


class Wishlist(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='wishlist')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlisted_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.email} - {self.product.product_name}"

class ExchangeRate(models.Model):
    currency = models.CharField(max_length=10, unique=True, default='USD')
    rate = models.DecimalField(max_digits=10, decimal_places=4)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.currency}: {self.rate} Bs"
