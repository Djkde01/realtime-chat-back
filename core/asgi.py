import os
import django

# Set Django settings module environment variable
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

# Initialize Django before importing any Django code
django.setup()

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from socket_handlers.middleware import JWTAuthMiddleware
import socket_handlers.routing

# Initialize Django ASGI application
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AllowedHostsOriginValidator(
            JWTAuthMiddleware(URLRouter(socket_handlers.routing.websocket_urlpatterns))
        ),
    }
)
