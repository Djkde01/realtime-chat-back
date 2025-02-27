from rest_framework import serializers
from .models import Reaction


class ReactionSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Reaction
        fields = ["id", "message", "user", "username", "type", "reacted_at"]
        read_only_fields = ["user", "reacted_at"]
