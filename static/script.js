class ChatApp {
    constructor() {
        this.currentChatId = null;
        this.baseUrl = 'http://localhost:8000/api';
        this.chatHistory = {};
        this.isLoading = false;
        
        this.initializeElements();
        this.bindEvents();
        this.loadChatHistory();
    }

    initializeElements() {
        // Sidebar elements
        this.newChatBtn = document.getElementById('newChatBtn');
        this.chatList = document.getElementById('chatList');
        this.fetchMarketBtn = document.getElementById('fetchMarketBtn');
        this.lastUpdated = document.getElementById('lastUpdated');
        
        // Main content elements
        this.activeChatTitle = document.getElementById('activeChatTitle');
        this.activeChatId = document.getElementById('activeChatId');
        this.documentSection = document.getElementById('documentSection');
        this.uploadBtn = document.getElementById('uploadBtn');
        this.fileInput = document.getElementById('fileInput');
        this.documentsList = document.getElementById('documentsList');
        
        // Chat elements
        this.chatMessages = document.getElementById('chatMessages');
        this.chatInputContainer = document.getElementById('chatInputContainer');
        this.messageInput = document.getElementById('messageInput');
        this.sendBtn = document.getElementById('sendBtn');
        
        // Modal elements
        this.loadingOverlay = document.getElementById('loadingOverlay');
        this.uploadModal = document.getElementById('uploadModal');
        this.progressFill = document.getElementById('progressFill');
        this.uploadStatus = document.getElementById('uploadStatus');
    }

    bindEvents() {
        // Sidebar events
        this.newChatBtn.addEventListener('click', () => this.createNewChat());
        this.fetchMarketBtn.addEventListener('click', () => this.fetchMarketData());
        
        // Upload events
        this.uploadBtn.addEventListener('click', () => this.fileInput.click());
        this.fileInput.addEventListener('change', (e) => this.handleFileUpload(e));
        
        // Chat events
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        this.sendBtn.addEventListener('click', () => this.sendMessage());
          // Input validation
        this.messageInput.addEventListener('input', () => {
            const hasText = this.messageInput.value.trim().length > 0;
            this.sendBtn.disabled = !hasText || this.isLoading;
        });
    }

    async loadChatHistory() {
        try {
            this.showLoading(true);
            const response = await fetch(`${this.baseUrl}/chat/history`);
            const data = await response.json();
            
            if (data.history && typeof data.history === 'object') {
                this.chatHistory = data.history;
                // Ensure each chat has required properties
                Object.keys(this.chatHistory).forEach(chatId => {
                    const chat = this.chatHistory[chatId];
                    if (!chat.messages) {
                        chat.messages = [];
                    }
                    if (!chat.title) {
                        chat.title = 'New Chat';
                    }
                });
                this.renderChatList();
            } else {
                this.chatHistory = {};
                this.renderChatList();
            }
        } catch (error) {            console.error('Error loading chat history:', error);
            this.chatHistory = {};
            this.renderChatList();
            this.showNotification('Failed to load chat history', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    renderChatList() {
        this.chatList.innerHTML = '';
        
        // Sort chats by updated_at in descending order (newest first)
        const sortedChats = Object.values(this.chatHistory).sort((a, b) => {
            const dateA = new Date(a.updated_at || a.created_at);
            const dateB = new Date(b.updated_at || b.created_at);
            return dateB - dateA; // Descending order
        });
        
        sortedChats.forEach(chat => {
            const chatItem = document.createElement('div');
            chatItem.className = `chat-item ${chat.id === this.currentChatId ? 'active' : ''}`;
            chatItem.dataset.chatId = chat.id;
            
            const lastMessage = chat.messages && chat.messages.length > 0 ? chat.messages[chat.messages.length - 1] : null;
            const preview = lastMessage && lastMessage.content ? this.truncateText(lastMessage.content, 50) : 'No messages yet';
            const time = lastMessage ? this.formatTime(lastMessage.timestamp) : this.formatTime(chat.created_at);
            
            chatItem.innerHTML = `
                <div class="chat-item-title">${chat.title || 'New Chat'}</div>
                <div class="chat-item-preview">${preview}</div>
                <div class="chat-item-time">${time}</div>
            `;
              chatItem.addEventListener('click', () => this.selectChat(chat.id));
            this.chatList.appendChild(chatItem);
        });
    }

    async createNewChat() {
        const newChatId = this.generateChatId();
        this.currentChatId = newChatId;
        
        // Add to local chat history
        this.chatHistory[newChatId] = {
            id: newChatId,
            title: 'New Chat',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            messages: []
        };
          this.renderChatList();
        this.selectChat(newChatId);
    }

    async selectChat(chatId) {
        this.currentChatId = chatId;
        this.renderChatList(); // Update active state
        
        // Update header
        const chat = this.chatHistory[chatId];
        this.activeChatTitle.textContent = chat && chat.title ? chat.title : 'Loading...';
        this.activeChatId.textContent = `Chat ID: ${chatId}`;
        
        // Show document section and chat input
        this.documentSection.style.display = 'block';
        this.chatInputContainer.style.display = 'block';
        this.messageInput.disabled = false;
        
        // For new chats, don't try to load messages from server
        if (chat && chat.messages && chat.messages.length === 0) {
            this.renderWelcomeMessage();
            // Only load documents, skip loading messages from server for new chats
            await this.loadDocuments(chatId);
        } else {
            // Load chat messages and documents for existing chats
            await Promise.all([
                this.loadChatMessages(chatId),
                this.loadDocuments(chatId)
            ]);
        }
    }

    async loadChatMessages(chatId) {
        try {
            this.showLoading(true);
            const response = await fetch(`${this.baseUrl}/chat/history/${chatId}`);
            const data = await response.json();
            
            if (data.history) {
                this.renderMessages(data.history);
            } else {
                this.renderWelcomeMessage();
            }
        } catch (error) {
            console.error('Error loading chat messages:', error);
            this.renderWelcomeMessage();
        } finally {
            this.showLoading(false);
        }
    }

    renderMessages(messages) {
        this.chatMessages.innerHTML = '';
        
        messages.forEach(message => {
            this.addMessageToChat(message.role, message.content, message.timestamp, message.metadata);
        });
        
        this.scrollToBottom();
    }

    renderWelcomeMessage() {
        this.chatMessages.innerHTML = `
            <div class="welcome-message">
                <div class="welcome-content">
                    <i class="fas fa-robot welcome-icon"></i>
                    <h2>Start Conversation</h2>
                    <p>Type your message below to begin chatting</p>
                </div>
            </div>
        `;
    }

    addMessageToChat(role, content, timestamp, metadata = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role === 'user' ? 'user' : 'ai'}`;
        
        let metaContent = '';
        if (timestamp) {
            metaContent += `<div class="message-meta">${this.formatTime(timestamp)}`;
            if (metadata && metadata.time_taken) {
                metaContent += `<div class="time-taken">Response time: ${metadata.time_taken}s</div>`;
            }
            metaContent += '</div>';
        }
        
        messageDiv.innerHTML = `
            <div class="message-bubble">
                <div class="message-content">${this.formatMessage(content)}</div>
                ${metaContent}
            </div>
        `;
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || !this.currentChatId || this.isLoading) return;
        
        this.isLoading = true;
        this.sendBtn.disabled = true;
        this.messageInput.disabled = true;
        
        // Add user message immediately
        this.addMessageToChat('user', message, new Date().toISOString());
        this.messageInput.value = '';
        
        // Show typing indicator
        this.showTypingIndicator();
        
        try {
            const response = await fetch(
                `${this.baseUrl}/chat/usermessage/${this.currentChatId}?message=${encodeURIComponent(message)}`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                }
            );
            
            const data = await response.json();
            
            // Remove typing indicator
            this.removeTypingIndicator();
            
            if (data.content) {
                this.addMessageToChat('model', data.content, new Date().toISOString(), data.metadata);
                
                // Update chat history
                if (this.chatHistory[this.currentChatId]) {
                    this.chatHistory[this.currentChatId].messages.push(
                        { role: 'user', content: message, timestamp: new Date().toISOString() },
                        { role: 'model', content: data.content, timestamp: new Date().toISOString(), metadata: data.metadata }
                    );
                    this.chatHistory[this.currentChatId].updated_at = new Date().toISOString();
                }
                
                this.renderChatList();
            } else {
                throw new Error(data.error || 'Failed to get response');
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.removeTypingIndicator();
            this.addMessageToChat('model', 'Sorry, I encountered an error. Please try again.', new Date().toISOString());
            this.showNotification('Failed to send message', 'error');
        } finally {
            this.isLoading = false;
            this.sendBtn.disabled = false;
            this.messageInput.disabled = false;
            this.messageInput.focus();
        }
    }

    showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message ai typing-indicator';
        typingDiv.id = 'typing-indicator';
        typingDiv.innerHTML = `
            <div class="message-bubble">
                <div class="message-content">
                    AI is typing
                    <div class="typing-dots">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            </div>
        `;
        this.chatMessages.appendChild(typingDiv);
        this.scrollToBottom();
    }

    removeTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    async handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file || !this.currentChatId) return;
        
        if (file.type !== 'application/pdf') {
            this.showNotification('Only PDF files are allowed', 'error');
            return;
        }
        
        if (file.size > 10 * 1024 * 1024) { // 10MB
            this.showNotification('File size must be less than 10MB', 'error');
            return;
        }
        
        this.showUploadModal(true);
        
        try {
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await fetch(`${this.baseUrl}/document_upload/upload/${this.currentChatId}`, {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.showNotification('Document uploaded successfully', 'success');
                await this.loadDocuments(this.currentChatId);
            } else {
                throw new Error(data.detail || 'Upload failed');
            }
        } catch (error) {
            console.error('Error uploading file:', error);
            this.showNotification('Failed to upload document', 'error');
        } finally {
            this.showUploadModal(false);
            this.fileInput.value = ''; // Reset file input
        }
    }

    async loadDocuments(chatId) {
        try {
            const response = await fetch(`${this.baseUrl}/document_upload/documents/${chatId}`);
            
            if (response.ok) {
                const data = await response.json();
                this.renderDocuments(data.documents || []);
            } else if (response.status === 404) {
                this.renderDocuments([]);
            } else {
                throw new Error('Failed to load documents');
            }
        } catch (error) {
            console.error('Error loading documents:', error);
            this.renderDocuments([]);
        }
    }

    renderDocuments(documents) {
        this.documentsList.innerHTML = '';
        
        documents.forEach(doc => {
            const docItem = document.createElement('div');
            docItem.className = 'document-item';
            docItem.innerHTML = `
                <i class="fas fa-file-pdf"></i>
                <div class="document-info">
                    <div class="document-name">${doc.name}</div>
                    <div class="document-meta">
                        ${this.formatFileSize(doc.size)} • ${this.formatTime(doc.uploaded_at)}
                    </div>
                </div>
            `;
            this.documentsList.appendChild(docItem);
        });
    }

    async fetchMarketData() {
        try {
            this.showLoading(true);
            this.fetchMarketBtn.disabled = true;
            
            const response = await fetch(`${this.baseUrl}/stock_market/update_stock_data`, {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.showNotification('Market data updated successfully', 'success');
                this.lastUpdated.textContent = this.formatTime(new Date().toISOString());
            } else {
                throw new Error(data.detail || 'Failed to update market data');
            }
        } catch (error) {
            console.error('Error fetching market data:', error);
            this.showNotification('Failed to update market data', 'error');
        } finally {
            this.showLoading(false);
            this.fetchMarketBtn.disabled = false;
        }
    }

    // Utility functions
    generateChatId() {        return Date.now().toString();
    }

    truncateText(text, maxLength) {
        if (!text || typeof text !== 'string') {
            return 'No content';
        }
        return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    }

    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);
        
        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        
        return date.toLocaleDateString();
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    formatMessage(content) {
        // Basic markdown-like formatting
        if (!content || typeof content !== 'string') return '';
        
        // Parse markdown tables
        content = this.parseMarkdownTables(content);
        
        return content
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>');
    }

    parseMarkdownTables(content) {
        // Look for patterns that resemble markdown tables
        const lines = content.split('\n');
        let inTable = false;
        let tableLines = [];
        let result = '';
        
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            
            // Check if this line looks like part of a table
            if (line.trim().startsWith('|') && line.trim().endsWith('|')) {
                if (!inTable) {
                    // Start of a new table
                    inTable = true;
                    tableLines = [line];
                } else {
                    // Continue existing table
                    tableLines.push(line);
                }
            } else if (inTable) {
                // End of table reached
                inTable = false;
                result += this.convertTableLinesToHtml(tableLines) + '\n';
                result += line + '\n';
            } else {
                // Regular line, not in a table
                result += line + '\n';
            }
        }
        
        // If we ended while still in a table
        if (inTable) {
            result += this.convertTableLinesToHtml(tableLines);
        }
        
        return result;
    }

    convertTableLinesToHtml(tableLines) {
        if (tableLines.length < 3) return tableLines.join('\n'); // Not enough rows for a valid table
        
        let html = '<table class="markdown-table">';
        
        // Process header (first line)
        const headerCells = tableLines[0].split('|').filter((cell, i, arr) => i > 0 && i < arr.length - 1);
        html += '<thead><tr>';
        headerCells.forEach(cell => {
            html += `<th>${cell.trim()}</th>`;
        });
        html += '</tr></thead>';
        
        // Skip delimiter row (second line)
        
        // Process data rows (third line onwards)
        html += '<tbody>';
        for (let i = 2; i < tableLines.length; i++) {
            const dataCells = tableLines[i].split('|').filter((cell, i, arr) => i > 0 && i < arr.length - 1);
            html += '<tr>';
            dataCells.forEach(cell => {
                html += `<td>${cell.trim()}</td>`;
            });
            html += '</tr>';
        }
        html += '</tbody></table>';
        
        return html;
    }

    scrollToBottom() {
        setTimeout(() => {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }, 100);
    }

    showLoading(show) {
        this.loadingOverlay.style.display = show ? 'flex' : 'none';
    }

    showUploadModal(show) {
        this.uploadModal.style.display = show ? 'flex' : 'none';
        if (show) {
            // Reset progress
            this.progressFill.style.width = '0%';
            this.uploadStatus.textContent = 'Processing your document...';
            
            // Animate progress
            setTimeout(() => {
                this.progressFill.style.width = '100%';
            }, 100);
        }
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'success' ? 'var(--success-color)' : type === 'error' ? 'var(--error-color)' : 'var(--primary-color)'};
            color: white;
            padding: 12px 24px;
            border-radius: var(--border-radius);
            z-index: 1001;
            box-shadow: var(--shadow-lg);
            animation: slideIn 0.3s ease-out;
            max-width: 300px;
            word-wrap: break-word;
        `;
        
        notification.textContent = message;
        document.body.appendChild(notification);
        
        // Add animation styles
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideIn {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
        `;
        document.head.appendChild(style);
        
        // Remove notification after 3 seconds
        setTimeout(() => {
            notification.style.animation = 'slideIn 0.3s ease-out reverse';
            setTimeout(() => {
                document.body.removeChild(notification);
                document.head.removeChild(style);
            }, 300);
        }, 3000);
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ChatApp();
});
