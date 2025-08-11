// Main LegalAI Application Entry Point
// This file maintains backward compatibility while using the modular structure

class LegalAIApp {
    constructor() {
        this.currentSection = "home";
        this.chatHistory = [];
        this.contractChatHistory = [];
        this.isAnalyzing = false;
        this.uploadedContract = null;
        this.currentSessionId = null;
        this.apiBaseUrl = "https://legalai-pro.onrender.com/api";
        this.currentTheme = localStorage.getItem("theme") || "light";
        
        // Initialize modules based on current page
        this.initModules();
    }
    
    initModules() {
        // Always initialize core functionality
        this.apiUtils = new window.APIUtils(this.apiBaseUrl);
        
        // Initialize page-specific modules
        const path = window.location.pathname;
        
        if (path.includes('contract-analyzer') && window.ContractAnalyzer) {
            this.contractAnalyzer = new window.ContractAnalyzer(this.apiUtils);
        }
        
        if (path.includes('virtual-assistant') && window.VirtualAssistant) {
            this.virtualAssistant = new window.VirtualAssistant(this.apiUtils);
        }
        
        if (path.includes('case-prediction') && window.CasePrediction) {
            this.casePrediction = new window.CasePrediction(this.apiUtils);
        }
    }
    
    // Legacy methods for backward compatibility
    showNotification(message, type) {
        if (window.uiUtils) {
            window.uiUtils.showNotification(message, type);
        } else {
            console.log(`[${type.toUpperCase()}] ${message}`);
        }
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize if modules are available
    if (window.APIUtils) {
        window.legalAIApp = new LegalAIApp();
    }
});