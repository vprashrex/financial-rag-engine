# AI Chat Assistant - Frontend

A modern, aesthetic frontend application for the AI Chat Assistant backend, built with HTML, CSS, and JavaScript.

## Features

### 🎨 Modern Design
- Gradient backgrounds and smooth animations
- Responsive design for all screen sizes
- Clean, intuitive user interface
- Real-time message updates

### 💬 Chat Functionality
- Create new chat sessions
- View chat history
- Real-time messaging with AI
- Response time tracking
- Message persistence

### 📄 Document Upload
- PDF file upload support
- File size validation (max 10MB)
- Upload progress tracking
- Document list per chat session

### 📈 Market Data Integration
- Fetch latest stock market data
- Update status tracking
- One-click data refresh

## Getting Started

### Prerequisites
- Python 3.11 or higher
- FastAPI backend server running
- Modern web browser

### Installation

1. **Ensure your backend is set up**
   ```bash
   # Make sure you're in the task-i directory
   cd d:\task-i
   
   # Activate virtual environment
   .\env\Scripts\activate
   
   # Install dependencies if not already done
   pip install -r requirements.txt
   ```

2. **Run the full-stack application**
   ```bash
   # Option 1: Run with frontend server (Recommended)
   python frontend_server.py
   
   # Option 2: Run backend only and serve frontend separately
   python -m uvicorn server:app --host 0.0.0.0 --port 8000
   ```

3. **Access the application**
   - Open your browser and go to: `http://localhost:8000`
   - The frontend will automatically connect to the backend API

### Alternative Setup (Backend + Frontend Separately)

If you prefer to run them separately:

1. **Start the backend server**
   ```bash
   python -m uvicorn server:app --host 0.0.0.0 --port 8000
   ```

2. **Serve the frontend**
   ```bash
   # Using Python's built-in server
   cd frontend
   python -m http.server 3000
   
   # Then access: http://localhost:3000
   ```

## Usage Guide

### Starting a New Chat
1. Click the "➕ New Chat" button in the sidebar
2. Type your message in the input field at the bottom
3. Press Enter or click the send button

### Uploading Documents
1. Select a chat from the chat history
2. Click the "📎 Attach File" button
3. Choose a PDF file (max 10MB)
4. Wait for upload and processing to complete

### Fetching Market Data
1. Click the "📈 Fetch Market Data" button at the bottom of the sidebar
2. Wait for the update to complete
3. The last updated timestamp will be shown

### Chat History
- All previous chats are shown in the left sidebar
- Click on any chat to view its messages
- Chat titles show the most recent message preview

## API Endpoints Used

The frontend connects to these backend endpoints:

- `GET /api/chat/history` - Get all chat sessions
- `GET /api/chat/history/{chat_id}` - Get specific chat messages
- `POST /api/chat/usermessage/{chat_id}` - Send a message
- `POST /api/document_upload/upload/{chat_id}` - Upload document
- `GET /api/document_upload/documents/{chat_id}` - Get uploaded documents
- `POST /api/stock_market/update_stock_data` - Update market data

## File Structure

```
frontend/
├── index.html          # Main HTML structure
├── styles.css          # Modern CSS styling
├── script.js           # JavaScript functionality
└── README.md           # This file

d:\task-i/
├── frontend_server.py  # Combined frontend + backend server
└── ...                 # Your existing backend files
```

## Customization

### Colors and Styling
- Edit `styles.css` to modify the color scheme
- CSS custom properties are defined in the `:root` selector
- Change `--primary-color` and related variables for different themes

### Functionality
- Modify `script.js` to add new features
- The `ChatApp` class contains all the main functionality
- API endpoints can be customized in the `baseUrl` property

## Browser Compatibility

- Chrome 60+ ✅
- Firefox 60+ ✅
- Safari 12+ ✅
- Edge 79+ ✅

## Troubleshooting

### Common Issues

1. **Chat not loading**
   - Check if backend server is running on port 8000
   - Verify API endpoints are accessible
   - Check browser console for errors

2. **File upload failing**
   - Ensure file is PDF format
   - Check file size is under 10MB
   - Verify chat session is selected

3. **Messages not sending**
   - Check network connection
   - Verify backend server is responding
   - Ensure chat session is active

### Debug Mode
Open browser developer tools (F12) to see console logs and network requests.

## Performance Tips

- The app automatically handles message history and pagination
- Large chat histories are loaded efficiently
- File uploads show progress indicators
- Background API calls don't block the UI

## Security Notes

- File uploads are validated on both frontend and backend
- All API calls use proper error handling
- CORS is configured for development (restrict in production)

---

**Note**: This frontend is designed to work seamlessly with your existing FastAPI backend. Make sure all backend services are running before accessing the frontend.
