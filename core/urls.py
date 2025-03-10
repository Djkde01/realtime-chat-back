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
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


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


schema_view = get_schema_view(
    openapi.Info(
        title="Besage Chat API",
        default_version="v1",
        description="Real-time chat API with WebSockets",
        contact=openapi.Contact(email="djkde.co@gmail.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
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
    path(
        "swagger<format>/", schema_view.without_ui(cache_timeout=0), name="schema-json"
    ),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]
