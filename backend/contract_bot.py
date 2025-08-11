# backend/contract_bot.py

import os
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import shutil

from langchain.vectorstores import FAISS
from langchain.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

# -------- Contract Analyzer Class --------
class ContractAnalyzer:
    def __init__(self, api_key=None):
        if api_key:
            os.environ["GOOGLE_API_KEY"] = api_key
        elif not os.environ.get("GOOGLE_API_KEY"):
            os.environ["GOOGLE_API_KEY"] = "AIzaSyAWjNzPom70z6u9P3ZkuCXo5bC6Yr-3D0w"  # Replace

        self.embedding_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        self.llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.3)

        self.vectorstore = None
        self.qa_chain = None
        self.documents = None
        self.document_path = None

        self.setup_prompt_template()

    def setup_prompt_template(self):
        template = """
        You are a legal contract analysis assistant.
        Use the provided context to answer the user's question.
        Rules:
        - If relevant context exists, first write the main answer without any references.
        - After the main answer, in a new paragraph, list references (page numbers, article numbers, etc.) in parentheses like (Page X), (Article Y).
        - Never make up references. Only use those present in the provided context.
        - Be precise and professional in your responses.

        Context:
        {context}

        Question:
        {question}

        Answer:
        """
        self.prompt = PromptTemplate(template=template, input_variables=["context", "question"])

    def load_document(self, file_path):
        try:
            self.document_path = file_path
            loader = PyMuPDFLoader(file_path)
            self.documents = loader.load()

            splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=300)
            docs = splitter.split_documents(self.documents)

            self.vectorstore = FAISS.from_documents(docs, self.embedding_model)
            retriever = self.vectorstore.as_retriever(search_kwargs={"k": 20})

            self.qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                retriever=retriever,
                chain_type="stuff",
                return_source_documents=True,
                chain_type_kwargs={"prompt": self.prompt, "verbose": False}
            )
            return True
        except Exception as e:
            print(f"Error loading document: {str(e)}")
            return False

    def ask_question(self, query):
        if not self.qa_chain:
            return "Please upload a contract first before asking questions."
        try:
            result = self.qa_chain({"query": query})
            return result["result"]
        except Exception as e:
            print(f"Error processing query: {str(e)}")
            return "Sorry, I encountered an error while processing your question."

    def analyze_contract(self):
        return {"message": "Contract loaded. Ready for questions."}


# -------- FastAPI Setup --------
app = FastAPI()
bot = ContractAnalyzer()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change to your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionRequest(BaseModel):
    question: str

@app.post("/upload_contract")
async def upload_contract(file: UploadFile = File(...)):
    try:
        os.makedirs("uploads", exist_ok=True)
        file_path = f"uploads/{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        if bot.load_document(file_path):
            return {"message": "Contract uploaded and processed successfully."}
        else:
            return {"error": "Failed to process contract."}
    except Exception as e:
        return {"error": str(e)}

@app.post("/ask_question")
async def ask_question(request: QuestionRequest):
    answer = bot.ask_question(request.question)
    return {"answer": answer}