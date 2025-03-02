from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from authentication.views import RegisterView, LoginView, LogoutView, UserViewSet
from chat.views import ChatViewSet, MessageViewSet
from reactions.views import ReactionViewSet
from django.http import HttpResponse
from django.http import JsonResponse
from django.db import connection
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def health_check(request):
    """Health check endpoint that verifies database connectivity"""
    try:
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()

        db_status = "connected" if result and result[0] == 1 else "error"

        return JsonResponse(
            {
                "status": "healthy",
                "database": db_status,
                "version": "1.0.0",
            }
        )
    except Exception as e:
        return JsonResponse(
            {"status": "unhealthy", "database": "error", "error": str(e)}, status=500
        )


router = DefaultRouter()
router.register("users", UserViewSet)
router.register("chats", ChatViewSet, basename="chat")
router.register("messages", MessageViewSet, basename="message")
router.register("reactions", ReactionViewSet, basename="reaction")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/register/", RegisterView.as_view(), name="register"),
    path("api/auth/login/", LoginView.as_view(), name="login"),
    path("api/auth/logout/", LogoutView.as_view(), name="logout"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/health/", health_check, name="health_check"),
    path("api/", include(router.urls)),
]
