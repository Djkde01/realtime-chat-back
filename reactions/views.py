from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import Reaction
from .serializers import ReactionSerializer


class ReactionViewSet(viewsets.ModelViewSet):
    serializer_class = ReactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        message_id = self.request.query_params.get("message_id")
        if message_id:
            return Reaction.objects.filter(message_id=message_id)
        return Reaction.objects.none()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        message_id = request.data.get("message")
        reaction_type = request.data.get("type", "like")

        # Check if user already reacted to this message
        existing_reaction = Reaction.objects.filter(
            message_id=message_id, user=request.user
        ).first()

        if existing_reaction:
            if existing_reaction.type == reaction_type:
                # If same reaction type, remove it (toggle behavior)
                existing_reaction.delete()
                return Response(
                    {"detail": "Reaction removed"}, status=status.HTTP_204_NO_CONTENT
                )
            else:
                # If different reaction type, update it
                existing_reaction.type = reaction_type
                existing_reaction.save()
                return Response(
                    ReactionSerializer(existing_reaction).data,
                    status=status.HTTP_200_OK,
                )

        # Otherwise create new reaction
        return super().create(request, *args, **kwargs)
