def get_websocket_url(server_url, endpoint, token):
    """Generate WebSocket URL with authentication token"""
    if server_url.startswith("http://"):
        ws_protocol = "ws://"
        server_url = server_url[7:]  # Remove http://
    elif server_url.startswith("https://"):
        ws_protocol = "wss://"
        server_url = server_url[8:]  # Remove https://
    else:
        ws_protocol = "ws://"

    return f"{ws_protocol}{server_url}/ws/{endpoint}/?token={token}"


def get_chat_ws_url(server_url, chat_id, token):
    """Get WebSocket URL for a specific chat"""
    return get_websocket_url(server_url, f"chat/{chat_id}", token)


def get_user_ws_url(server_url, token):
    """Get WebSocket URL for user-specific notifications"""
    return get_websocket_url(server_url, "user", token)


# Example usage (for documentation)
"""
# In React Native:
import { TOKEN } from './auth';
const SERVER_URL = 'https://api.example.com';
const chatId = 123;

// Connect to chat WebSocket
const chatWsUrl = `wss://api.example.com/ws/chat/${chatId}/?token=${TOKEN}`;
const chatSocket = new WebSocket(chatWsUrl);

// Connect to user notification WebSocket
const userWsUrl = `wss://api.example.com/ws/user/?token=${TOKEN}`;
const userSocket = new WebSocket(userWsUrl);

// Handle incoming messages
chatSocket.onmessage = (e) => {
  const data = JSON.parse(e.data);
  
  if (data.type === 'chat_message') {
    // Handle new message
    const message = data.message;
    // Update UI with new message
  }
  else if (data.type === 'chat.event') {
    // Handle events like typing, status updates, etc.
    switch (data.event) {
      case 'typing':
        // Show typing indicator
        break;
      case 'mensaje_estado':
        // Update message status indicators
        break;
      // ...other events
    }
  }
};
"""
