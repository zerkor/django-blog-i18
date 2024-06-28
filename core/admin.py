from django.contrib import admin
from .models import Post, Category
from parler.admin import TranslatableAdmin

class PostAdmin(TranslatableAdmin):
    list_display = ('title', 'category', 'created', 'show_image')
    search_fields = [
        'category__translations__name__icontains',
        'translations__title__icontains',
        'translations__content__icontains'
    ]

admin.site.register(Post, PostAdmin)
admin.site.register(Category, TranslatableAdmin)
