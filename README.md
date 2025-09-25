# LegalAI Pro

## AI-Powered Legal Solutions for Modern Law Practices

LegalAI Pro is a comprehensive AI-powered legal technology platform that empowers legal professionals with cutting-edge AI technology for contract analysis, legal assistance, and case prediction. Our advanced algorithms and machine learning models are specifically designed for the legal domain to enhance efficiency and accuracy in legal practice.

## 🚀 Features

### 1. Smart Contract Analyzer
- **AI-Powered Analysis**: Upload PDF contracts for comprehensive AI-powered analysis using InLegalBERT
- **Risk Assessment**: Automated risk scoring and identification with detailed risk level categorization
- **Key Terms Extraction**: Extract important contract terms, dates, parties, and durations
- **Contract Type Detection**: Automatically classify contract types (NDAs, Lease Agreements, Employment, etc.)
- **Interactive Chat**: Contract-specific AI chat support using Google Gemini for detailed Q&A

### 2. Virtual Legal Assistant
- **24/7 Legal Support**: Get instant answers to legal questions across multiple domains
- **Conversation Memory**: Maintains conversation history and context for better assistance
- **Professional Guidance**: Clear, point-wise responses with recommendations to consult qualified attorneys
- **Multi-Domain Expertise**: Covers various areas of law and legal procedures

### 3. Case Outcome Prediction
- **AI-Driven Analysis**: Predict case outcomes using historical data and legal precedents
- **Confidence Scoring**: Provides confidence percentages and detailed analysis
- **Strategic Recommendations**: Offers strategic decision support and recommendations
- **Timeline Estimation**: Estimates case duration and potential settlement ranges

## 🛠️ Technology Stack

### Backend
- **Framework**: Flask (Python)
- **AI/ML**: 
  - PyTorch for deep learning
  - Transformers (InLegalBERT) for legal text analysis
  - Google Generative AI (Gemini) for conversational AI
  - LangChain for RAG implementation
- **Document Processing**: 
  - PyMuPDF for PDF parsing
  - pdfplumber for text extraction
- **Vector Database**: FAISS for document embeddings
- **API**: RESTful API with CORS support

### Frontend
- **HTML5**: Modern semantic markup
- **CSS3**: Responsive design with animations
- **JavaScript**: Interactive UI components
- **File Upload**: Drag & drop interface for contracts

### AI Models
- **InLegalBERT**: Specialized BERT model for legal text understanding
- **Google Gemini**: For conversational AI and general legal assistance
- **Custom Risk Scoring**: Proprietary algorithm for contract risk assessment

## 📁 Project Structure

```
LegalAI-Pro/
├── backend/
│   ├── app.py                    # Main Flask application
│   ├── legal_bert_service.py     # Contract analysis service with InLegalBERT
│   ├── contract_bot.py           # Gemini-powered contract chatbot
│   ├── general_legal_bot.py      # General legal assistant
│   ├── globals.py                # Global variables store
│   └── uploads/                  # Contract upload directory
├── frontend/
│   ├── index.html               # Homepage
│   ├── contract-analyzer.html   # Contract analysis interface
│   ├── virtual-assistant.html   # Legal assistant chat
│   ├── case-prediction.html     # Case prediction interface
│   ├── about.html              # About page
│   └── contact.html            # Contact information
└── README.md
```

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8+
- pip package manager
- Google API Key for Gemini

### 1. Clone the Repository
```bash
git clone https://github.com/algo-aryan/legalAI-pro.git
cd legalAI-pro
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Setup
Create a `.env` file in the backend directory:
```env
GOOGLE_API_KEY=your_google_api_key_here
LEGAL_MODEL=law-ai/InLegalBERT
BATCH_SIZE=16
```

### 4. Run the Application
```bash
cd backend
python app.py
```

The application will be available at:
- **Frontend**: http://localhost:5000
- **API**: http://localhost:5000/api/

## 📋 Required Dependencies

```
flask
flask-cors
torch
transformers
numpy
pdfplumber
PyMuPDF
langchain
langchain-google-genai
faiss-cpu
google-generativeai
tqdm
werkzeug
uuid
```

## 🔧 API Endpoints

### General Endpoints
- `GET /api/health` - Health check
- `POST /api/cleanup` - Session cleanup

### Contract Analysis
- `POST /api/contract/upload` - Upload and analyze contract
- `POST /api/contract/chat` - Chat about uploaded contract
- `POST /api/contract/analyze` - Re-analyze contract

### Legal Assistant
- `POST /api/chat/general` - General legal questions

### Case Prediction
- `POST /api/case/predict` - Predict case outcomes

## 🎯 Key Features in Detail

### Contract Analysis Pipeline
1. **PDF Processing**: Extract text from uploaded PDF contracts
2. **BERT Embeddings**: Generate embeddings using InLegalBERT
3. **Contract Classification**: Identify contract type using semantic similarity
4. **Entity Extraction**: Extract parties, dates, durations using regex patterns
5. **Risk Assessment**: Calculate risk scores based on keyword analysis
6. **Key Terms Identification**: Find important clauses and terms
7. **Interactive Chat**: Enable Q&A about the contract using Gemini

### Risk Scoring Algorithm
- Uses weighted keyword matching for risk factors
- Considers: indemnity, liability, penalty, termination, warranty, disputes
- Provides normalized risk scores (0-100) with LOW/MEDIUM/HIGH categories

### Security Features
- File upload validation (PDF only, size limits)
- Session-based contract storage
- Automatic cleanup capabilities
- CORS protection

## 🎨 User Interface

- **Responsive Design**: Works on desktop and mobile devices
- **Modern UI**: Clean, professional interface
- **Drag & Drop**: Easy file upload experience
- **Real-time Chat**: Interactive chat interfaces
- **Progress Indicators**: Visual feedback during processing
- **Downloadable Results**: Analysis results and recommendations

## 👥 Team

**Made by:**
- **Aryan Bansal** - Backend Development & AI Integration
- **Anushka Gupta** - Frontend Development & UI/UX Design  
- **Aryan Gupta** - AI Model Implementation & Testing

## 🔒 Privacy & Security

- Enterprise-grade security measures
- Local file processing
- Session-based data management
- No permanent storage of sensitive documents
- Compliance with legal industry standards

## 🚀 Future Enhancements

- Integration with more legal databases
- Advanced ML models for case prediction
- Multi-language support
- Real-time collaboration features
- Integration with legal practice management systems
- Mobile application development

## ⚖️ Legal Disclaimer

LegalAI Pro is a technology tool designed to assist legal professionals. It does not provide legal advice and should not replace professional legal consultation. Always consult with qualified attorneys for specific legal matters.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Transform your legal practice with AI-powered intelligence. Experience the future of legal technology with LegalAI Pro.**
