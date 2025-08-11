# backend/general_legal_bot.py - General Legal Assistant

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate
import os


class GeneralLegalBot:
    def __init__(self, api_key=None):
        """Initialize the general legal bot"""
        # Set API key
        if api_key:
            google_api_key = api_key
        else:
            google_api_key = os.environ.get("GOOGLE_API_KEY", "AIzaSyAWjNzPom70z6u9P3ZkuCXo5bC6Yr-3D0w")
        
        # Initialize the LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=google_api_key,
            temperature=0.2
        )
        
        # Initialize memory for conversation history
        self.memory = ConversationBufferMemory(memory_key="history", return_messages=True)
        
        # Setup prompt template
        self.setup_prompt()
        
        # Initialize conversation chain
        self.conversation = ConversationChain(
            llm=self.llm,
            memory=self.memory,
            prompt=self.prompt,
            verbose=False
        )
    
    def setup_prompt(self):
        """Setup the prompt template for general legal assistance"""
        prompt_template = """You are a helpful legal assistant specializing in providing accurate legal information.

Guidelines:
- Provide clear, concise answers in point-wise format when appropriate.
- Focus on factual legal information.
- If the question is complex, break it down into understandable parts.
- Always recommend consulting with a qualified attorney for specific legal matters.
- Be professional and accurate in your responses.
- If you're unsure about something, acknowledge it rather than guessing.

Conversation history:
{history}

User: {input}

Legal Assistant:"""
        
        self.prompt = PromptTemplate(
            input_variables=["history", "input"],
            template=prompt_template
        )
    
    def ask(self, query):
        """Process a legal question and return response"""
        try:
            response = self.conversation.predict(input=query)
            return response.strip()
        except Exception as e:
            print(f"Error in general legal bot: {str(e)}")
            return "I apologize, but I'm experiencing technical difficulties. Please try again later or consult with a qualified attorney for your legal question."
    
    def reset_conversation(self):
        """Reset the conversation memory"""
        self.memory.clear()


# Global instance for the Flask app
_bot_instance = None


def get_bot_instance():
    """Get or create the global bot instance"""
    global _bot_instance
    if _bot_instance is None:
        _bot_instance = GeneralLegalBot()
    return _bot_instance


def legal_bot(query: str) -> str:
    """
    Main function to interact with the legal bot
    This maintains compatibility with your existing code
    """
    bot = get_bot_instance()
    return bot.ask(query)


# For backward compatibility and testing
if __name__ == "__main__":
    # Test the bot
    print("Testing General Legal Bot...")
    
    # Test cases
    test_queries = [
        "What is the difference between bail and parole?",
        "How does contract law work?",
        "What are the key elements of a valid contract?",
        "What should I know about employment law?"
    ]
    
    for query in test_queries:
        print(f"\nQ: {query}")
        response = legal_bot(query)
        print(f"A: {response}")
        print("-" * 50)
