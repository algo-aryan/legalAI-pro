// Case Prediction Module
class CasePrediction {
    constructor(apiUtils) {
        this.apiUtils = apiUtils;
        this.init();
    }
    
    init() {
        this.setupCasePrediction();
    }
    
    setupCasePrediction() {
        const nextBtns = document.querySelectorAll(".next-step");
        const prevBtns = document.querySelectorAll(".prev-step");
        const analyzeBtn = document.querySelector(".analyze-case");

        // Step navigation
        nextBtns.forEach((btn) => {
            btn.addEventListener("click", () => this.nextFormStep());
        });

        prevBtns.forEach((btn) => {
            btn.addEventListener("click", () => this.prevFormStep());
        });

        // Analysis
        analyzeBtn?.addEventListener("click", (e) => {
            e.preventDefault();
            this.analyzeCaseOutcome();
        });
    }

    nextFormStep() {
        const currentStep = document.querySelector(".form-step.active");
        if (!currentStep) return;

        // Validate current step
        if (!this.validateFormStep(currentStep)) {
            this.showNotification("Please fill in all required fields", "warning");
            return;
        }

        const currentStepNum = parseInt(currentStep.getAttribute("data-step"));
        const nextStepNum = currentStepNum + 1;

        if (nextStepNum <= 2) {
            currentStep.classList.remove("active");
            const nextStep = document.querySelector(`[data-step="${nextStepNum}"].form-step`);
            if (nextStep) {
                nextStep.classList.add("active");
            }

            // Update progress with animation
            this.updateStepProgress(currentStepNum, nextStepNum);
        }
    }

    prevFormStep() {
        const currentStep = document.querySelector(".form-step.active");
        if (!currentStep) return;

        const currentStepNum = parseInt(currentStep.getAttribute("data-step"));
        const prevStepNum = currentStepNum - 1;

        if (prevStepNum >= 1) {
            currentStep.classList.remove("active");
            const prevStep = document.querySelector(`[data-step="${prevStepNum}"].form-step`);
            if (prevStep) {
                prevStep.classList.add("active");
            }

            // Update progress
            this.updateStepProgress(currentStepNum, prevStepNum, true);
        }
    }

    validateFormStep(stepElement) {
        const requiredFields = stepElement.querySelectorAll("[required]");
        let isValid = true;

        requiredFields.forEach((field) => {
            if (!field.value.trim()) {
                field.style.borderColor = "var(--color-error)";
                isValid = false;
            } else {
                field.style.borderColor = "";
            }
        });

        return isValid;
    }

    updateStepProgress(currentStepNum, targetStepNum, isGoingBack = false) {
        const currentStepIndicator = document.querySelector(`[data-step="${currentStepNum}"].step`);
        const targetStepIndicator = document.querySelector(`[data-step="${targetStepNum}"].step`);

        if (isGoingBack) {
            if (currentStepIndicator) currentStepIndicator.classList.remove("active");
            if (targetStepIndicator) targetStepIndicator.classList.remove("completed");
        } else {
            if (currentStepIndicator) currentStepIndicator.classList.add("completed");
            if (targetStepIndicator) targetStepIndicator.classList.add("active");
        }
    }

    async analyzeCaseOutcome() {
        const form = document.getElementById("case-form");
        if (!form) return;
    
        const formData = new FormData(form);
        const caseData = Object.fromEntries(formData.entries());
    
        // Enhanced validation
        if (!caseData.case_type || !caseData.case_description || !caseData.jurisdiction) {
            this.showNotification("Please fill in all required fields", "warning");
            return;
        }
    
        const analyzeBtn = document.querySelector(".analyze-case");
        const loadingOverlay = document.getElementById("loading-overlay");
    
        if (analyzeBtn) {
            analyzeBtn.textContent = "Analyzing...";
            analyzeBtn.disabled = true;
        }
        if (loadingOverlay) {
            loadingOverlay.classList.remove("hidden");
        }
    
        try {
            // Mock prediction data
            const mockPrediction = {
                outcome: "Favorable Settlement Likely",
                confidence: 78,
                factors: [
                    "Strong documentary evidence in client's favor",
                    "Similar precedents in the jurisdiction support the claim",
                    "Opposing party's key witness credibility in question"
                ],
                recommendations: [
                    "Negotiate with opposing counsel for early settlement",
                    "Prepare motions for summary judgment",
                    "Continue gathering corroborative witness statements"
                ]
            };
    
            setTimeout(() => {
                this.displayCasePrediction(mockPrediction);
                this.showNotification("Case analysis completed", "info");
    
                // ✅ Reset UI states here
                if (analyzeBtn) {
                    analyzeBtn.textContent = "Analyze Case";
                    analyzeBtn.disabled = false;
                }
                if (loadingOverlay) {
                    loadingOverlay.classList.add("hidden");
                }
            }, 6000);
    
        } catch (error) {
            console.error("Case prediction error:", error);
            this.showNotification(`Analysis failed: ${error.message}`, "error");
    
            // Reset states on error
            if (analyzeBtn) {
                analyzeBtn.textContent = "Analyze Case";
                analyzeBtn.disabled = false;
            }
            if (loadingOverlay) {
                loadingOverlay.classList.add("hidden");
            }
        }
    }    

    displayCasePrediction(predictionRaw) {
        // Handle both backend response shapes ('.prediction' or '.caseAnalysis')
        let prediction = predictionRaw;
        if (!prediction || typeof prediction !== "object") prediction = {};
    
        // If the backend wrapped in .caseAnalysis or .prediction
        if ("prediction" in prediction) prediction = prediction.prediction;
        if ("caseAnalysis" in prediction) prediction = prediction.caseAnalysis;
    
        // Hide placeholder, show content
        const predictionPlaceholder = document.getElementById("prediction-placeholder");
        const predictionContent = document.getElementById("prediction-content");
        if (predictionPlaceholder) predictionPlaceholder.classList.add("hidden");
        if (predictionContent) predictionContent.classList.remove("hidden");
    
        // Animate confidence score if present
        const scoreElement = document.getElementById("confidence-score");
        if (scoreElement) {
            if (prediction.confidence || typeof prediction.confidence === "number") {
                this.animateConfidenceScore(scoreElement, prediction.confidence);
            } else {
                scoreElement.textContent = "N/A";
            }
        }
    
        // Show predicted outcome or outcome-like field
        const predictedOutcome = document.getElementById("predicted-outcome");
        if (predictedOutcome) {
            if (prediction.outcome) {
                predictedOutcome.textContent = prediction.outcome;
            } else if (prediction.caseType && prediction.description) {
                // Fallback for caseAnalysis
                predictedOutcome.textContent = `${prediction.caseType} (${prediction.jurisdiction || ''}) — ${prediction.description}`;
            } else if (prediction.caseType) {
                predictedOutcome.textContent = prediction.caseType;
            } else {
                predictedOutcome.textContent = "N/A";
            }
        }
    
        // Key factors (array of reasons or explanations)
        const factorsList = document.getElementById("key-factors");
        if (factorsList) {
            factorsList.innerHTML = "";
            if (Array.isArray(prediction.factors) && prediction.factors.length > 0) {
                prediction.factors.forEach((factor, index) => {
                    const li = document.createElement("li");
                    li.textContent = factor;
                    li.style.animationDelay = `${index * 0.1}s`;
                    factorsList.appendChild(li);
                });
            } else if (prediction.reasoning) {
                const li = document.createElement("li");
                li.textContent = prediction.reasoning;
                factorsList.appendChild(li);
            } else {
                const li = document.createElement("li");
                li.textContent = "N/A";
                factorsList.appendChild(li);
            }
        }
    
        // Recommendations (array)
        const recommendationsList = document.getElementById("recommendations");
        if (recommendationsList) {
            recommendationsList.innerHTML = "";
            if (Array.isArray(prediction.recommendations) && prediction.recommendations.length > 0) {
                prediction.recommendations.forEach((rec, index) => {
                    const li = document.createElement("li");
                    li.textContent = rec;
                    li.style.animationDelay = `${index * 0.1}s`;
                    recommendationsList.appendChild(li);
                });
            } else {
                const li = document.createElement("li");
                li.textContent = "N/A";
                recommendationsList.appendChild(li);
            }
        }
    
        // Fallback: if nothing shown, display JSON for debugging
        if (
            (!prediction.outcome && !prediction.confidence && !prediction.factors && !prediction.recommendations) &&
            predictedOutcome && predictedOutcome.textContent === "N/A"
        ) {
            predictedOutcome.textContent = JSON.stringify(prediction, null, 2);
        }
    }
    

    animateConfidenceScore(element, targetScore) {
        let currentScore = 0;
        const increment = targetScore / 50; // Animate over 50 steps

        const interval = setInterval(() => {
            currentScore += increment;
            if (currentScore >= targetScore) {
                currentScore = targetScore;
                clearInterval(interval);
            }
            element.textContent = `${Math.round(currentScore)}%`;
        }, 20);
    }

    showNotification(message, type) {
        this.apiUtils.showNotification(message, type);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (window.location.pathname.includes('case-prediction') || document.getElementById('case-prediction')) {
        if (window.APIUtils) {
            const apiUtils = new window.APIUtils();
            window.casePrediction = new CasePrediction(apiUtils);
        }
    }
});

// Export for global access
window.CasePrediction = CasePrediction;