import warnings
import logging
import asyncio
from configparser import ConfigParser
from concurrent.futures import ThreadPoolExecutor

warnings.filterwarnings("ignore", category=FutureWarning, message=".*resume_download.*")

import ollama
from langchain_community.document_loaders import PlaywrightURLLoader
from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain_community.vectorstores import SQLiteVSS
from langchain_text_splitters import CharacterTextSplitter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("script.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Load configurations
config = ConfigParser()
config.read('config.ini')

HOST = config.get('ollama', 'host', fallback='http://localhost:11434')
MODEL_NAME = config.get('ollama', 'model_name', fallback='llama3')
DB_FILE = config.get('database', 'file', fallback='/tmp/vss.db')
TABLE_NAME = config.get('database', 'table', fallback='state_union')
URLS = [url.strip() for url in config.get('documents', 'urls', fallback='').split('\n') if url.strip()]

# Initialize the client
client = ollama.Client(host=HOST)

def validate_config():
    if not URLS:
        logger.error("No URLs specified in the configuration.")
        raise ValueError("URL list is empty. Please provide URLs to load documents.")

def stream_chat_response_with_context(model, messages, context):
    system_prompt = """
    You are a helpful assistant. This client is using the LangChain framework to build applications powered by large language models (LLMs). 
    The client expects detailed, context-aware responses that utilize the context provided from their indexed documents. 
    Always base your responses on the given context and aim to assist in developing, debugging, or explaining aspects of LangChain applications.
    """
    context_message = {"role": "system", "content": system_prompt + f"Context: {context}"}
    messages_with_context = [context_message] + messages

    stream = client.chat(
        model=model,
        messages=messages_with_context,
        stream=True
    )
    
    response_chunks = []
    for chunk in stream:
        response_chunks.append(chunk['message']['content'])
        print(chunk['message']['content'], end='', flush=True)
    full_response = ''.join(response_chunks)
    logger.info(f"Assistant response: {full_response}")
    print()
    return full_response

async def load_documents_from_urls(urls):
    with ThreadPoolExecutor() as executor:
        loop = asyncio.get_event_loop()
        tasks = [loop.run_in_executor(executor, load_document, url) for url in urls]
        return await asyncio.gather(*tasks)

def load_document(url):
    try:
        logger.info(f"Loading document from URL: {url}")
        loader = PlaywrightURLLoader(
            urls=[url], 
            remove_selectors=["header", "footer"]
        )
        docs = loader.load()
        logger.info(f"Successfully loaded document from URL: {url}")
        return docs
    except Exception as e:
        logger.error(f"Error loading document from {url}: {e}")
        return []

def load_and_index_documents(docs, db_file=DB_FILE, table=TABLE_NAME):
    try:
        logger.info("Splitting documents into chunks...")
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        docs_split = text_splitter.split_documents(docs)
        texts = [doc.page_content for doc in docs_split]
        
        logger.info("Indexing documents...")
        embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
        db = SQLiteVSS.from_texts(
            texts=texts,
            embedding=embedding_function,
            table=table,
            db_file=db_file,
        )
        logger.info("Documents indexed successfully.")
        return db
    except Exception as e:
        logger.error(f"Error indexing documents: {e}")
        return None

def query_documents(db, query):
    try:
        logger.info(f"Querying documents for: {query}")
        results = db.similarity_search(query)
        result_content = results[0].page_content if results else "No relevant documents found."
        logger.info(f"Query result: {result_content}")
        return result_content
    except Exception as e:
        logger.error(f"Error querying documents: {e}")
        return "Error querying documents."

def loop_chat(db):
    model = MODEL_NAME
    messages = []

    while True:
        user_input = input("\nYou: ")  # Ensuring "You: " starts on a new line
        if user_input.lower() in ['exit', 'quit']:
            print("Exiting chat...")
            logger.info("Chat session ended by user.")
            break

        messages.append({'role': 'user', 'content': user_input})
        
        context = query_documents(db, user_input)

        full_response = stream_chat_response_with_context(model, messages, context)
        messages.append({'role': 'assistant', 'content': full_response})

if __name__ == "__main__":
    try:
        validate_config()

        logger.info("Starting document loading...")
        # Load documents from the specified URLs
        loop = asyncio.get_event_loop()
        docs = loop.run_until_complete(load_documents_from_urls(URLS))

        # Flatten list of lists
        docs = [doc for sublist in docs for doc in sublist]

        if docs:
            logger.info(f"Number of documents loaded: {len(docs)}")

            # Index the loaded documents
            db = load_and_index_documents(docs)

            if db:
                # Start the interactive loop chat
                loop_chat(db)
            else:
                logger.error("Failed to index documents.")
        else:
            logger.error("No documents loaded.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
