import asyncio
import warnings
import sqlite3
from ollama import AsyncClient
from langchain.prompts import PromptTemplate
from langchain_community.tools import DuckDuckGoSearchRun

warnings.simplefilter('ignore', category=RuntimeWarning)
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

def init_db():
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS chat_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT, content TEXT)''')
    conn.commit()
    conn.close()

def save_chat_history(messages):
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    for message in messages:
        c.execute("INSERT INTO chat_history (`role`, `content`) VALUES (?, ?)", (message['role'], message['content']))
    conn.commit()
    conn.close()

def load_chat_history():
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    c.execute("SELECT role, content FROM chat_history")
    messages = [{'role': row[0], 'content': row[1]} for row in c.fetchall()]
    conn.close()
    return messages

async def ask_question():
    try:
        # Load chat history from the database
        messages = load_chat_history()
        ddg_search = DuckDuckGoSearchRun()

        while True:
            user_input = input("\nYou: ")
            if user_input.lower() == 'exit':
                break

            user_message = {'role': 'user', 'content': user_input}
            messages.append(user_message)

            # Save chat history to the database
            save_chat_history(messages)

            # Create the prompt with context and user's question
            context = '\n'.join([f"{msg['content']}" for msg in messages])
            prompt = PromptTemplate(template="Context: {context}\n\nQuestion: Lets think this through. {question} Respond in markdown format. You are named Bradley. Be yourself and respond truthfully. {search_results}", input_variables=["context", "question", "search_results"])

            if "search" in user_input.lower():
                search_term = user_input.split("search", 1)[-1].strip()
                search_results = ddg_search.run(search_term)
                prompt_with_context = prompt.format(context=context, question=user_input, search_results=search_results)
            else:
                prompt_with_context = prompt.format(context=context, question=user_input, search_results="")

            message = {'role': 'user', 'content': prompt_with_context}
            async for part in await AsyncClient(host='http://192.168.1.25:11434').chat(model='llama3', messages=[message], stream=True):
                print(part['message']['content'], end='', flush=True)

            assistant_message = {'role': 'assistant', 'content': part['message']['content']}
            messages.append(assistant_message)

            # Save chat history to the database
            save_chat_history(messages)

            # Limit the number of messages to the last 4
            messages = messages[-4:]

    except KeyboardInterrupt:
        print("\nExiting...")
    except EOFError:
        print("\nExiting...")

async def main():
    init_db()
    await ask_question()

if __name__ == "__main__":
    asyncio.run(main())
