// API Utilities for LegalAI
class APIUtils {
    constructor(baseUrl = "https://legalai-pro.onrender.com/api") {
        this.apiBaseUrl = baseUrl;
    }
    
    async apiCall(endpoint, method = "GET", data = null) {
        try {
            const config = {
                method: method,
                headers: {
                    "Content-Type": "application/json",
                },
            };
            
            if (data && method !== "GET") {
                config.body = JSON.stringify(data);
            }
            
            const response = await fetch(`${this.apiBaseUrl}${endpoint}`, config);
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.error || `HTTP error! status: ${response.status}`);
            }
            
            return result;
        } catch (error) {
            console.error("API call failed:", error);
            this.showNotification("API Error: " + error.message, "error");
            throw error;
        }
    }
    
    async uploadFile(file) {
        try {
            const formData = new FormData();
            formData.append("file", file);
            
            const response = await fetch(`${this.apiBaseUrl}/contract/upload`, {
                method: "POST",
                body: formData,
            });
            
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.error || `HTTP error! status: ${response.status}`);
            }
            
            return result;
        } catch (error) {
            console.error("File upload failed:", error);
            this.showNotification("Upload failed: " + error.message, "error");
            throw error;
        }
    }
    
    showNotification(message, type) {
        // Use global UI utils if available, otherwise console log
        if (window.uiUtils) {
            window.uiUtils.showNotification(message, type);
        } else {
            console.log('[' + type.toUpperCase() + '] ' + message);
        }
    }
}

// Export for use in other files
window.APIUtils = APIUtils;