from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

User = get_user_model()


class UserAdmin(BaseUserAdmin):
    list_display = (
        "username",
        "email",
        "is_staff",
        "created_at",
    )
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Profile Info", {"fields": ("profile_img")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
    readonly_fields = ("created_at", "updated_at")
    search_fields = ("username", "email")
    ordering = ("-date_joined",)


admin.site.register(User, UserAdmin)
