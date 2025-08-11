from django.contrib import admin
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'name', 'is_staff')
    search_fields = ('username', 'email', 'name')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
