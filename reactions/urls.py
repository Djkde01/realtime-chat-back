from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReactionViewSet, ReactionTypeViewSet

router = DefaultRouter()
router.register("types", ReactionTypeViewSet)
router.register("", ReactionViewSet, basename="reaction")

urlpatterns = [
    path("", include(router.urls)),
]
