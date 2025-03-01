from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from urllib.parse import parse_qs

User = get_user_model()


@database_sync_to_async
def get_user(user_id):
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return AnonymousUser()


# Track active users
active_users = {}


class JWTAuthMiddleware(BaseMiddleware):
    def __init__(self, inner):
        super().__init__(inner)

    async def __call__(self, scope, receive, send):
        # Get query parameters
        query_string = scope.get("query_string", b"").decode()
        query_params = parse_qs(query_string)

        # Get token from query parameters
        token = query_params.get("token", [None])[0]

        if token:
            try:
                # Verify token and get user ID
                access_token = AccessToken(token)
                user_id = access_token.payload.get("user_id")
                if user_id:
                    scope["user"] = await get_user(user_id)

                    # Track connection
                    if user_id not in active_users:
                        active_users[user_id] = 0
                    active_users[user_id] += 1

                    # Handle disconnect to update active users
                    original_receive = receive

                    async def receive_wrapper():
                        message = await original_receive()
                        if message["type"] == "websocket.disconnect":
                            active_users[user_id] -= 1
                            if active_users[user_id] <= 0:
                                active_users.pop(user_id, None)
                        return message

                    receive = receive_wrapper
                else:
                    scope["user"] = AnonymousUser()
            except (InvalidToken, TokenError):
                scope["user"] = AnonymousUser()
        else:
            scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)
