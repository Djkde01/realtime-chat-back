# Besage Chat API

A real-time chat backend application built with Django Channels and WebSockets, providing seamless message delivery, read receipts, and user presence functionality.

## Features

- Real-time messaging using WebSockets
- Message delivery and read receipts
- User presence indicators (online/offline status)
- Chat room creation and management
- REST API for message history and user management
- Authentication with JWT tokens
- Scalable architecture ready for production

## Technology Stack

- **Django 5.1.6**: Core web framework
- **Django Channels 4.2.0**: WebSocket support
- **Django REST Framework 3.15.2**: API endpoints
- **PostgreSQL**: Database
- **Redis**: Channel layer for WebSockets
- **JWT Authentication**: Secure API access
- **Gunicorn + Uvicorn**: ASGI production server

## Project Structure

```
besage-chat-back/
├── core/ # Project configuration
├── authentication/ # User authentication app
├── chat/ # Core chat functionality
│ ├── models.py # Chat, Message, and Status models
│ ├── views.py # API views
│ ├── serializers.py # Data serializers
│ └── urls.py # API endpoints
├── socket_handlers/ # WebSocket handling
│ ├── consumers.py # WebSocket consumers
│ ├── middleware.py # JWT auth for WebSockets
│ └── routing.py # WebSocket URL routing
├── reactions/ # Message reactions app
└── requirements.txt # Project dependencies
```

## Prerequisites

- Python 3.11 or higher
- PostgreSQL
- Redis (for production)
- pip and virtualenv
- Instances of Related Services running

# Related Services

This backend application is part of a larger ecosystem and depends on two external services:

### 1. React Native Frontend

The frontend for this chat application is built with React Native. For a complete user experience, you'll need to set up and run the frontend application.

- [Repository](https://github.com/Djkde01/realtime-chat-client)
- Follow the setup instructions in the frontend repository to connect it to this backend

### 2. Cloudflare Worker for Image Storage

This application uses Cloudflare R2 and Workers for secure image storage and delivery:

- [Repository](https://github.com/Djkde01/realtime-chat-cdn)
- Make sure to configure the Cloudflare Worker and update the R2 environment variables in this project:

## Installation

### 1. Clone the repository

```bash
git clone git@github.com:Djkde01/realtime-chat-back.git
cd besage-chat-back
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt

```

### 4. Set up environment variables

Create a .env file in the project root with the following variables:

```bash
# Database configuration
DATABASE_URL=postgresql://user:password@localhost:5432/besage

# Secret key
SECRET_KEY=your-secure-secret-key

# Environment (development or production)
ENVIRONMENT=development

# Allowed hosts
ALLOWED_HOSTS=127.0.0.1,localhost

# CORS settings
ALLOWED_ORIGINS=http://localhost:8081,http://127.0.0.1:8081

# Cloudflare R2 Configuration
R2_ACCESS_KEY_ID=your_r2_access_key
R2_SECRET_ACCESS_KEY=your_r2_secret_key
R2_STORAGE_BUCKET_NAME=besage-chat-imgs
R2_ACCOUNT_ID=your_cloudflare_account_id
R2_WORKER_ENABLED=true
R2_WORKER_DOMAIN=https://your-worker.your-subdomain.workers.dev

# Worker configuration
USE_WORKER_URL=true
WORKER_URL=https://your-worker.your-subdomain.workers.dev
WORKER_AUTH_KEY=your-authentication-key
```

### 5. Run migrations

```bash
python manage.py migrate
```

### 6. Create superuser (optional)

```bash
python manage.py createsuperuser
```

## Running the Application

### Development

For development with auto-reload:

```bash
python run_server.py
```

Or using Uvicorn directly:

```bash
uvicorn core.asgi:application --host 0.0.0.0 --port 8000 --reload
```

### Production

For production environments:

```bash
gunicorn core.asgi:application -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT
```

## API Documentation

This project uses Swagger/OpenAPI for API documentation. You can access to it via `{{base_url}}/swagger`

## WebSocket Events

### Chat WebSocket

Connect to: `ws://<server>/ws/chat/{chat_id}/?token={jwt_token}`

### Incoming Events (Client to Server)

- `chat_message`: Send a new message
- `typing`: Indicate user is typing
- `read_messages`: Mark messages as read
- `delivered_messages`: Mark messages as delivered

### Outgoing Events (Server to Client)

- `chat_message`: New message received
- `chat.event`: Status updates, typing indicators, etc.

### User WebSocket

Connect to: `ws://<server>/ws/user/?token={jwt_token}`

Receives notifications about new chats and mentions.

## Deployment

The application is configured for deployment on Render:

1. Create a PostgreSQL database on Render
2. Set up a Redis instance for channel layers
3. Deploy the web service using the provided `render.yaml` configuration
4. Set the required environment variables
5. Enable automatic migrations during deployment

## Code Formatting

This project uses Black for code formatting to maintain consistent style across the codebase.

### Setting up Black

1. Install Black:

```bash
pip install black
```

## Troubleshooting

### WebSocket Connection Issues

- Ensure your server supports ASGI (run with Uvicorn or Daphne)
- Verify JWT token is valid and properly formatted
- Check CORS and allowed origins settings

### Database Connection Issues

- Verify DATABASE_URL format and credentials
- For production, ensure database service is accessible from web service

### Common Errors

- 404 for WebSocket endpoints: Make sure you're running an ASGI server
- Authentication failures: Check token format and expiration

For questions or support, please open an issue on the project repository.
