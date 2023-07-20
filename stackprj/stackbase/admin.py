from django.contrib import admin
from .models import Question, Comment, Tag, Category

admin.site.register(Question)
admin.site.register(Comment)
admin.site.register(Tag)
admin.site.register(Category)
