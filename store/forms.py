from django import forms
from .models import Product, ReviewRating
from category.models import Category


class ReviewForm(forms.ModelForm):
    class Meta:
        model = ReviewRating
        fields = ['subject', 'review', 'rating']


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['product_name', 'description', 'price', 'old_price', 'stock', 'images', 'Category', 'is_available', 'is_on_sale', 'gross_weight', 'length', 'length_unit', 'width', 'width_unit', 'height', 'height_unit']
        labels = {
            'product_name': 'Nombre del Producto',
            'description': 'Descripción',
            'price': 'Precio ($)',
            'old_price': 'Precio Original ($)',
            'gross_weight': 'Peso Bruto (kg)',
            'length': 'Largo',
            'length_unit': 'Unidad (Largo)',
            'width': 'Ancho',
            'width_unit': 'Unidad (Ancho)',
            'height': 'Alto',
            'height_unit': 'Unidad (Alto)',
            'stock': 'Stock',
            'images': 'Imagen',
            'Category': 'Categoría',
            'is_available': 'Disponible',
            'is_on_sale': '¿En Oferta?',
        }

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        for field_name in self.fields:
            if field_name in ['is_available', 'is_on_sale']:
                continue
            if field_name == 'images':
                self.fields[field_name].widget.attrs['class'] = 'ap-input'
                self.fields[field_name].widget.attrs['accept'] = 'image/*'
            elif field_name in ['Category', 'length_unit', 'width_unit', 'height_unit']:
                self.fields[field_name].widget.attrs['class'] = 'ap-select'
                if field_name == 'Category':
                    self.fields[field_name].empty_label = 'Seleccionar categoría'
            elif field_name == 'description':
                self.fields[field_name].widget = forms.Textarea(attrs={
                    'class': 'ap-input',
                    'rows': 4,
                    'placeholder': 'Descripción del producto...'
                })
            else:
                self.fields[field_name].widget.attrs['class'] = 'ap-input'
            
            # Enforce non-negative values for numeric fields on the frontend
            if field_name in ['gross_weight', 'length', 'width', 'height', 'stock', 'price', 'old_price']:
                self.fields[field_name].widget.attrs['min'] = '0'
