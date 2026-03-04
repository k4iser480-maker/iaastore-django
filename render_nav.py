import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE','ecosite.settings')
django.setup()

from django.template.loader import render_to_string
from category.models import Category

html = render_to_string('includes/navbar.html', {
    'links': Category.objects.all(),
    'cart_count': 0,
    'user': type('U',(object,),{'id':None})(),
})
print(html)
