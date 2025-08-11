// Virtual Assistant Module - Fixed Version
class VirtualAssistant {
    constructor(apiUtils) {
        this.apiUtils = apiUtils;
        this.chatHistory = [];
        this.init();
    }
    
    init() {
        this.setupVirtualAssistant();
    }
    
    setupVirtualAssistant() {
        const chatInput = document.getElementById("chat-input");
        const sendBtn = document.getElementById("chat-send-btn");
        if (!chatInput || !sendBtn) return;

        // Send message handlers
        sendBtn.addEventListener("click", () => this.sendChatMessage());
        chatInput.addEventListener("keypress", (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                this.sendChatMessage();
            }
        });

        // Suggestion buttons
        document.querySelectorAll(".suggestion-btn").forEach((btn) => {
            btn.addEventListener("click", () => {
                if (chatInput) {
                    chatInput.value = btn.textContent;
                    this.sendChatMessage();
                }
            });
        });

        // Mobile sidebar toggle - Fixed to prevent disappearing sidebar
        const sidebarToggle = document.getElementById("mobile-sidebar-toggle");
        const sidebar = document.querySelector(".chat-sidebar");
        if (sidebarToggle) {
            sidebarToggle.addEventListener("click", (e) => {
                e.preventDefault();
                e.stopPropagation();
                sidebar?.classList.toggle("active");
            });
        }
    }

    async sendChatMessage() {
        const chatInput = document.getElementById("chat-input");
        const sendBtn = document.getElementById("chat-send-btn");
        if (!chatInput) return;

        const message = chatInput.value.trim();
        if (!message) return;

        // Clear input immediately to prevent double messages
        chatInput.value = "";

        // Disable input during processing
        chatInput.disabled = true;
        sendBtn.disabled = true;

        // Add user message with animation
        this.addChatMessage("user", message);

        // Show typing indicator
        this.showTypingIndicator();

        try {
            // Send to backend API
            const response = await this.apiUtils.apiCall("/chat/general", "POST", {
                message: message
            });

            this.hideTypingIndicator();
            this.addChatMessage("assistant", response.response);
        } catch (error) {
            console.error("Chat error:", error);
            this.hideTypingIndicator();
            this.addChatMessage(
                "assistant", 
                "I apologize, but I'm experiencing technical difficulties. Please try again later."
            );
        } finally {
            // Re-enable input
            chatInput.disabled = false;
            sendBtn.disabled = false;
            chatInput.focus();
        }
    }

    addChatMessage(sender, message) {
        const chatMessages = document.getElementById("chat-messages");
        if (!chatMessages) return;

        const messageElement = document.createElement("div");
        messageElement.className = `message ${sender}-message`;
        messageElement.style.animation = "fadeIn 0.3s ease-in";

        const avatar = sender === "user" ? "U" : '<i class="fas fa-robot"></i>';

        messageElement.innerHTML = `
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">
                <p>${this.formatMessage(message)}</p>
            </div>
        `;

        chatMessages.appendChild(messageElement);
        
        // Force scroll to bottom - Fixed scrolling issue
        setTimeout(() => {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }, 10);

        // Add to chat history
        this.chatHistory.push({ sender, message });
    }

    formatMessage(message) {
        // Enhanced message formatting with line breaks and lists
        return message
            .replace(/\n\n/g, "</p><p>")
            .replace(/\n•/g, "</p><p>•")
            .replace(/\n/g, "<br>");
    }

    showTypingIndicator() {
        const typingIndicator = document.getElementById("typing-indicator");
        if (typingIndicator) {
            typingIndicator.classList.remove("hidden");
            
            // Scroll to show typing indicator
            const chatMessages = document.getElementById("chat-messages");
            if (chatMessages) {
                setTimeout(() => {
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                }, 10);
            }
        }
    }

    hideTypingIndicator() {
        const typingIndicator = document.getElementById("typing-indicator");
        if (typingIndicator) {
            typingIndicator.classList.add("hidden");
        }
    }

    showNotification(message, type) {
        this.apiUtils.showNotification(message, type);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (window.location.pathname.includes('virtual-assistant') || document.getElementById('virtual-assistant')) {
        if (window.APIUtils) {
            const apiUtils = new window.APIUtils();
            window.virtualAssistant = new VirtualAssistant(apiUtils);
        }
    }
});

// Export for global access
window.VirtualAssistant = VirtualAssistant;