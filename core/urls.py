from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from authentication.views import RegisterView, LoginView, LogoutView, UserViewSet
from chat.views import ChatViewSet, MessageViewSet
from reactions.views import ReactionViewSet

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
    path("api/", include(router.urls)),
]
