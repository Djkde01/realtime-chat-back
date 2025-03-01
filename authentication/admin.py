from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

User = get_user_model()


class UserAdmin(BaseUserAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "created_at",
    )

    # Fix the fieldsets format - each 'fields' value must be a list or tuple
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Profile Info", {"fields": ("profile_img", "bio", "phone")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    readonly_fields = ("created_at", "updated_at")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("-date_joined",)


admin.site.register(User, UserAdmin)
