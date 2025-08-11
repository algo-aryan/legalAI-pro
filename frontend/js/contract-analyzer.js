// Contract Analyzer Module
class ContractAnalyzer {
    constructor(apiUtils) {
        this.apiUtils = apiUtils;
        this.uploadedContract = null;
        this.currentSessionId = null;
        this.contractChatHistory = [];
        this.init();
    }

    init() {
        this.setupContractAnalyzer();
    }

    // Utility functions for better formatting
    titleCase(str) {
        return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
    }

    formatDate(dateStr) {
        if (!dateStr || dateStr === 'Not specified') return dateStr;
        const d = new Date(dateStr);
        if (!isNaN(d)) {
          const dd = String(d.getDate()).padStart(2,'0');
          const mm = String(d.getMonth()+1).padStart(2,'0');
          const yyyy = d.getFullYear();
          return `${dd}/${mm}/${yyyy}`;
        }
        return dateStr.trim();
      }      

    setupContractAnalyzer() {
        const uploadZone = document.getElementById("upload-zone");
        const fileInput = document.getElementById("file-input");
        if (!uploadZone || !fileInput) return;

        uploadZone.addEventListener('click', () => fileInput.click());


        uploadZone.addEventListener("dragover", (e) => {
            e.preventDefault();
            uploadZone.classList.add("dragover");
        });

        uploadZone.addEventListener("dragleave", (e) => {
            e.preventDefault();
            uploadZone.classList.remove("dragover");
        });

        uploadZone.addEventListener("drop", (e) => {
            e.preventDefault();
            uploadZone.classList.remove("dragover");
            if (e.dataTransfer.files.length > 0) {
                this.handleFileUpload(e.dataTransfer.files[0]);
            }
        });

        fileInput.addEventListener("change", (e) => {
            console.log("manual file change fired, this =", this);
            if (e.target.files.length > 0) {
                this.handleFileUpload(e.target.files[0]);
            }
        });

        document.querySelectorAll(".tab-btn").forEach((btn) => {
            btn.addEventListener("click", () => {
                this.switchTab(btn.getAttribute("data-tab"));
            });
        });

        const contractChatBtn = document.getElementById("contract-chat-btn");
        contractChatBtn?.addEventListener("click", () => {
            if (this.currentSessionId) {
                this.openContractChat();
            } else {
                this.showNotification("Please upload a contract first before starting a chat.", "warning");
            }
        });
    }

    async handleFileUpload(file) {
        document.getElementById('upload-zone').classList.remove('hidden');
        document.getElementById('upload-progress').classList.add('hidden');
        document.getElementById('file-input').value = '';
        const maxSize = 10 * 1024 * 1024; // 10MB
        const allowedTypes = [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain",
        ];

        if (file.size > maxSize) {
            this.showNotification("File size must be less than 10MB", "error");
            return;
        }
        if (!allowedTypes.includes(file.type)) {
            this.showNotification("Please upload a PDF, DOC, DOCX, or TXT file", "error");
            return;
        }

        this.uploadedContract = { name: file.name, size: file.size, type: file.type };

        const uploadZone = document.getElementById("upload-zone");
        const uploadProgress = document.getElementById("upload-progress");
        uploadZone.classList.add("hidden");
        uploadProgress.classList.remove("hidden");
        this.updateProgress(0, "Uploading...");

        try {
            const response = await Promise.race([
                this.apiUtils.uploadFile(file),
                new Promise((_, reject) =>
                    setTimeout(() => reject(new Error("Server took too long to respond")), 60000)
                )
            ]);

            this.currentSessionId = response.session_id || null;
            const analysisData = response.analysis || response;
            const analysis = {
                summary: analysisData.summary || "",
                risks: analysisData.risks || [],
                terms: analysisData.terms || []
            };

            this.updateProgress(100, "Upload complete!");

            setTimeout(() => {
                if ((!analysis.summary || analysis.summary.trim() === "") && !analysis.risks.length && !analysis.terms.length) {
                    this.updateProgress(0, "Waiting for analysis...");
                } else {
                    this.updateProgress(0, "Analyzing contract...");
                    this.displayContractAnalysis(analysis);
                    document.getElementById("results-placeholder")?.classList.add("hidden");
                    document.getElementById("results-content")?.classList.remove("hidden");
                }

                uploadProgress.classList.add("hidden");
                const contractChatBtn = document.getElementById("contract-chat-btn");
                if (contractChatBtn) {
                    contractChatBtn.style.display = "flex";
                    contractChatBtn.classList.remove("hidden");
                    contractChatBtn.style.animation = "fadeIn 0.3s ease-in";
                }
                this.showNotification("Contract processing started.", "info");
            }, 1000);

        } catch (error) {
            console.error("Upload failed:", error);
            uploadProgress.classList.add("hidden");
            uploadZone.classList.remove("hidden");
            this.showNotification(`Upload failed: ${error.message}`, "error");
        }
    }

    updateProgress(progress, text) {
        document.getElementById("progress-fill").style.width = `${progress}%`;
        document.getElementById("progress-text").textContent = text;
    }

    displayContractAnalysis(analysis) {
        if (!analysis || !analysis.summary) {
            console.error("Invalid analysis data received");
            this.showNotification("Invalid analysis data received", "error");
            return;
        }

        let summaryObj = { type: "", parties: "", date: "", duration: "" };
        if (typeof analysis.summary === "string") {
            const lines = analysis.summary.split("\n");
            lines.forEach(line => {
                const [key, ...rest] = line.split(":");
                const val = rest.join(":").trim();
                if (/contract type/i.test(key)) summaryObj.type = this.titleCase(val);
                else if (/parties/i.test(key)) summaryObj.parties = val;
                else if (/dates?/i.test(key)) summaryObj.date = this.formatDate(val);
                else if (/durations?/i.test(key)) summaryObj.duration = val;
            });
        } else {
            summaryObj = analysis.summary;
            // Format each field
            if (summaryObj.type) summaryObj.type = this.titleCase(summaryObj.type);
            if (summaryObj.date) summaryObj.date = this.formatDate(summaryObj.date);
        }

        document.getElementById("contract-type").textContent = summaryObj.type || "Not specified";
        document.getElementById("contract-parties").textContent = summaryObj.parties || "Not specified";
        document.getElementById("contract-date").textContent = summaryObj.date || "Not specified";
        document.getElementById("contract-duration").textContent = summaryObj.duration || "Not specified";

        const riskItemsContainer = document.getElementById("risk-items");
        if (riskItemsContainer) {
            riskItemsContainer.innerHTML = "";
            if (!analysis.risks || analysis.risks.length === 0) {
                riskItemsContainer.innerHTML = `<div class="empty-state">
                    <i class="fas fa-shield-check" style="color: var(--success-color, #10b981);"></i>
                    <h3>No significant risks identified</h3>
                    <p>The contract appears to have standard terms and conditions.</p>
                </div>`;
            } else {
                analysis.risks.forEach((risk, index) => {
                    const level = (risk.level || "low").toLowerCase();
                    let iconClass;
                    switch (level) {
                        case 'high': iconClass = 'fas fa-exclamation-triangle'; break;
                        case 'medium': iconClass = 'fas fa-exclamation-circle'; break;
                        default: iconClass = 'fas fa-info-circle'; break;
                    }
                    const riskCard = document.createElement("div");
                    riskCard.className = `risk-card ${level}`;
                    riskCard.style.animationDelay = `${index * 0.1}s`;
                    riskCard.innerHTML = `
                        <div class="risk-header">
                            <i class="${iconClass}"></i>
                            <h5>${(risk.level || 'Info').toUpperCase()}: ${this.titleCase(risk.keyword || 'General Finding')}</h5>
                        </div>
                        <p class="risk-context">${risk.context || 'No additional context provided.'}</p>`;
                    riskItemsContainer.appendChild(riskCard);
                });
            }
        }

        const termsListContainer = document.getElementById("terms-list");
        if (termsListContainer) {
            termsListContainer.innerHTML = "";
            if (!analysis.terms || analysis.terms.length === 0) {
                termsListContainer.innerHTML = `<div class="empty-state">
                    <i class="fas fa-search" style="color: var(--primary-color, #007bff);"></i>
                    <h3>No key terms extracted</h3>
                    <p>The document may not contain identifiable key terms or clauses.</p>
                </div>`;
            } else {
                analysis.terms.forEach((term, index) => {
                    const termItem = document.createElement("div");
                    termItem.className = 'term-item';
                    termItem.style.animationDelay = `${index * 0.08}s`;
                    termItem.innerHTML = `
                        <h5 class="term-keyword">${this.titleCase(term.keyword || 'Unnamed Term')}</h5>
                        <p class="term-context">${term.context || 'No context available.'}</p>`;
                    termsListContainer.appendChild(termItem);
                });
            }
        }

                // reset upload zone for next file
        document.getElementById('upload-zone').classList.remove('hidden');
        document.getElementById('upload-progress').classList.add('hidden');

    }

    switchTab(tabName) {
        document.querySelectorAll(".tab-btn").forEach(btn => {
            btn.classList.toggle("active", btn.getAttribute("data-tab") === tabName);
        });
        document.querySelectorAll(".tab-panel").forEach(panel => {
            panel.classList.toggle("active", panel.id === `${tabName}-panel`);
        });
    }

    openContractChat() {
        const modal = document.getElementById("contract-chat-modal");
        if (modal) {
            modal.classList.remove("hidden");
            modal.style.animation = "fadeIn 0.3s ease-in";
        }
        if (this.contractChatHistory.length === 0) {
            this.contractChatHistory.push({
                sender: "assistant",
                message: "Hello! I can answer questions about the contract you've uploaded. What would you like to know?",
            });
            this.displayContractChatHistory();
        }
        const input = document.getElementById("contract-chat-input");
        if (input) setTimeout(() => input.focus(), 300);
        this.setupContractChatHandlers();
    }

    setupContractChatHandlers() {
        const input = document.getElementById("contract-chat-input");
        const sendBtn = document.getElementById("contract-chat-send");
        if (sendBtn && !sendBtn.dataset.handlerAttached) {
            sendBtn.dataset.handlerAttached = "true";
            sendBtn.addEventListener("click", () => this.sendContractChatMessage());
        }
        if (input && !input.dataset.handlerAttached) {
            input.dataset.handlerAttached = "true";
            input.addEventListener("keypress", (e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    this.sendContractChatMessage();
                }
            });
        }
    }

    async sendContractChatMessage() {
        const input = document.getElementById("contract-chat-input");
        const sendBtn = document.getElementById("contract-chat-send");
        if (!input) return;

        const message = input.value.trim();
        if (!message) return;

        input.disabled = true;
        sendBtn.disabled = true;
        this.addContractChatMessage("user", message);
        input.value = "";

        if (!this.currentSessionId) {
            this.addContractChatMessage("assistant", "Please upload a contract first before asking questions.");
            input.disabled = false;
            sendBtn.disabled = false;
            return;
        }

        try {
            const response = await this.apiUtils.apiCall("/contract/chat", "POST", {
                session_id: this.currentSessionId,
                message: message,
            });
            this.addContractChatMessage("assistant", response.response);
        } catch (error) {
            console.error("Contract chat error:", error);
            this.addContractChatMessage("assistant", "Error while processing your question. Please try again.");
        } finally {
            input.disabled = false;
            sendBtn.disabled = false;
            input.focus();
        }
    }

    addContractChatMessage(sender, message) {
        const messagesContainer = document.getElementById("contract-chat-messages");
        if (!messagesContainer) return;

        const el = document.createElement("div");
        el.className = `message ${sender}-message`;
        el.style.animation = "fadeIn 0.3s ease-in";
        el.innerHTML = `
            <div class="message-avatar">${sender === "user" ? "U" : '<i class="fas fa-robot"></i>'}</div>
            <div class="message-content">
                <p>${this.formatMessage(message)}</p>
            </div>
        `;
        messagesContainer.appendChild(el);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        this.contractChatHistory.push({ sender, message });
    }

    displayContractChatHistory() {
        const messagesContainer = document.getElementById("contract-chat-messages");
        if (!messagesContainer) return;
        messagesContainer.innerHTML = "";
        this.contractChatHistory.forEach(msg => this.addContractChatMessage(msg.sender, msg.message));
    }

    formatMessage(message) {
        return message.replace(/\n\n/g, "</p><p>").replace(/\n•/g, "</p><p>•").replace(/\n/g, "<br>");
    }

    showNotification(message, type) {
        this.apiUtils.showNotification(message, type);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname.includes('contract-analyzer') || document.getElementById('contract-analyzer')) {
        if (window.APIUtils) {
            window.contractAnalyzer = new ContractAnalyzer(new window.APIUtils());
        }
    }
});
window.ContractAnalyzer = ContractAnalyzer;