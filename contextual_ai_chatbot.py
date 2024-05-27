import warnings

# Suppress specific warnings
warnings.filterwarnings("ignore", category=FutureWarning, message=".*resume_download.*")

import ollama
from bs4 import BeautifulSoup as Soup
from langchain_community.document_loaders import PlaywrightURLLoader
from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain_community.vectorstores import SQLiteVSS
from langchain_text_splitters import CharacterTextSplitter
from playwright.sync_api import sync_playwright

# Initialize the client
client = ollama.Client(host='http://localhost:11434')

# Create a function to handle streaming responses with context
def stream_chat_response_with_context(model, messages, context):
    # Add context to the beginning of the messages
    context_message = {'role': 'system', 'content': context}
    messages_with_context = [context_message] + messages

    # Call the chat function with streaming enabled
    stream = client.chat(
        model=model,
        messages=messages_with_context,
        stream=True
    )
    
    # Process and display the streaming response in real-time
    response_chunks = []
    for chunk in stream:
        response_chunks.append(chunk['message']['content'])
        print(chunk['message']['content'], end='', flush=True)
    print()  # Ensure a new line after the response
    return ''.join(response_chunks)

# Function to load documents from URLs using PlaywrightURLLoader
def load_documents_from_urls(urls):
    loader = PlaywrightURLLoader(
        urls=urls, 
        remove_selectors=["header", "footer"]
    )
    docs = loader.load()
    return docs

# Function to load and index documents
def load_and_index_documents(docs, db_file='/tmp/vss.db', table='state_union'):
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    docs_split = text_splitter.split_documents(docs)
    texts = [doc.page_content for doc in docs_split]
    
    embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    db = SQLiteVSS.from_texts(
        texts=texts,
        embedding=embedding_function,
        table=table,
        db_file=db_file,
    )
    return db

# Function to query the indexed documents for context
def query_documents(db, query):
    results = db.similarity_search(query)
    return results[0].page_content if results else "No relevant documents found."

# Main loop chat function
def loop_chat(db):
    model = 'llama3'
    messages = []

    while True:
        user_input = input("\nYou: ")  # Ensuring "You: " starts on a new line
        if user_input.lower() in ['exit', 'quit']:
            print("Exiting chat...")
            break

        messages.append({'role': 'user', 'content': user_input})
        
        # Query the context from the documents
        context = query_documents(db, user_input)
        print(f"Context: {context}")

        # Stream the response with context
        full_response = stream_chat_response_with_context(model, messages, context)
        
        # Add the AI response to messages for context in future interactions
        messages.append({'role': 'assistant', 'content': full_response})

# URLs to load
urls = ["https://python.langchain.com/v0.2/docs/introduction/"]

# Load documents from the specified URLs
docs = load_documents_from_urls(urls)

# Print the number of documents loaded
print(f"Number of documents loaded: {len(docs)}")

# Index the loaded documents
db = load_and_index_documents(docs)

# Start the interactive loop chat
loop_chat(db)
