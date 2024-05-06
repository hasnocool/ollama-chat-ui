import sys
import os
import re
import sqlite3
import threading
import requests
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QTextEdit,
    QLineEdit, QPushButton, QHBoxLayout, QComboBox, QFileDialog
)
from PyQt6.QtCore import pyqtSignal
from langchain_community.chat_models import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import AIMessage, HumanMessage
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import ChatPromptTemplate

API_BASE_URL = "http://192.168.1.26:11434/api"
DB_FILE = 'chat_history.db'
DEFAULT_MODEL = "default_model"
WINDOW_TITLE = "Chat UI"
EDITOR_TITLE = "Text Editor"
TEXT_FILE_TYPES = "Text Files (*.py);;All Files (*)"

def db_operation(func):
    def wrapper(*args, **kwargs):
        def run():
            try:
                func(*args, **kwargs)
            except Exception as e:
                print(f"Error in database operation: {e}")
        threading.Thread(target=run).start()
    return wrapper

@db_operation
def add_message_to_db(message_type, content):
    """Add messages to the database."""
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute('INSERT INTO messages (message_type, content) VALUES (?, ?)', (message_type, content))
        conn.commit()

class EditorWindow(QMainWindow):
    """Text Editor Window for opening and applying file contents."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(EDITOR_TITLE)
        self.setGeometry(100, 100, 600, 400)
        self.file_contents = ""
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface components for the editor."""
        self.text_edit = QTextEdit()
        self.open_button = QPushButton("Open File")
        self.open_button.clicked.connect(self.open_file)

        layout = QVBoxLayout()
        layout.addWidget(self.text_edit)
        layout.addWidget(self.open_button)
        
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)



    def open_file(self):
        """Handle file opening with error handling."""
        filename, _ = QFileDialog.getOpenFileName(self, "Open Text File", "", TEXT_FILE_TYPES)
        if filename:
            self.file_contents = self.read_file(filename)
            self.text_edit.setPlainText(self.file_contents)

    def read_file(self, filename):
        """Read file contents with error handling."""
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            print(f"Failed to read file {filename}: {e}")
            return ""  # Return empty string on failure


    def get_file_contents(self):
        """Return the current contents of the file."""
        return self.file_contents

class ChatWindow(QMainWindow):
    """Main Chat Window for handling interactions and displaying the chat interface."""

    update_ui = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.setGeometry(100, 100, 800, 400)
        self.editor_window = None
        self.setup_ui()
        self.initialize_memory_and_client()

    def setup_ui(self):
        """Set up the chat UI layout."""
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.input_text = QLineEdit()
        self.input_text.returnPressed.connect(self.send_message)
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        self.delete_button = QPushButton("Delete Last Line")
        self.delete_button.clicked.connect(self.delete_last_message)
        self.editor_button = QPushButton("Open Editor")
        self.editor_button.clicked.connect(self.open_editor)
        self.model_combobox = QComboBox()
        self.populate_model_combobox()

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.send_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.editor_button)
        button_layout.addWidget(self.model_combobox)

        layout = QVBoxLayout()
        layout.addWidget(self.text_edit)
        layout.addWidget(self.input_text)
        layout.addLayout(button_layout)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def open_editor(self):
        """Open the editor window."""
        if not self.editor_window:
            self.editor_window = EditorWindow()
        self.editor_window.show()

    def populate_model_combobox(self):
        """Populate the combobox with available models."""
        models = self.list_local_models()
        self.model_combobox.addItems(models)

    def list_local_models(self):
        """Fetch model names from the API."""
        try:
            response = requests.get(f"{API_BASE_URL}/tags")
            return [model["name"] for model in response.json().get("models", [])] if response.status_code == 200 else []
        except requests.RequestException as e:
            print(f"Failed to fetch models: {e}")
            return []

    def initialize_memory_and_client(self):
        """Initialize chat components and memory."""
        selected_model = self.model_combobox.currentText() if self.model_combobox.count() > 0 else DEFAULT_MODEL
        try:
            self.ollama_client = ChatOllama(model=selected_model)
            self.memory = ConversationBufferMemory()
            self.output_parser = StrOutputParser()
            self.load_chat_history()
        except Exception as e:
            print(f"Failed to initialize chat components or memory with model {selected_model}: {e}")
            raise

    def load_chat_history(self):
        """Load chat history from the database."""
        def fetch_history():
            with sqlite3.connect(DB_FILE) as conn:
                c = conn.cursor()
                c.execute('SELECT id, message_type, content FROM messages ORDER BY id')
                history = c.fetchall()
                self.update_ui.emit(history)
        threading.Thread(target=fetch_history).start()

    def send_message(self):
        """Send a message and process it."""
        message = self.input_text.text()
        if message:
            add_message_to_db('Human', message)
            self.process_message(message)

    def process_message(self, message):
        """Process a sent message and update the UI."""
        self.memory.chat_memory.add_user_message(message)
        self.text_edit.append(f"You: {message}\n")
        self.input_text.clear()
        self.interact_with_model(message)

    @staticmethod
    def safe_format(template, **kwargs):
        """Safely format the string, filling missing keys with placeholders."""
        class SafeDict(dict):
            def __missing__(self, key):
                return f'{{{key}}}'  # Return the key itself as a placeholder.
        try:
            kwargs.setdefault('e', '')  # Set default value for 'e'
            return template.format_map(SafeDict(**kwargs))
        except KeyError as e:
            print(f"Template formatting error: missing key '{e.args[0]}' in template")
            return template  # Return the original template if formatting fails

    


    def interact_with_model(self, message):
        """Create and process interaction with the chat model using safe formatting."""
        try:
            formatted_history = self.format_history(message)
            chat_template = ChatPromptTemplate.from_messages(formatted_history)

            editor_content = self.editor_window.get_file_contents() if self.editor_window and self.editor_window.isVisible() else None
            wrapped_content = f"```{editor_content}```" if editor_content else f"```{message}```"

            # Define 'e', 'response', and 'what' before calling safe_format
            e = ""  # Replace with the actual value if available
            response = ""  # Replace with the actual value if available
            what = wrapped_content

            # Check if all required keys are in the template
            required_keys = ['e', 'what', 'response']
            if all(key in chat_template.format() for key in required_keys):
                formatted_messages = ChatWindow.safe_format(chat_template.format(), e=e, what=what, response=response)
            else:
                print("Missing required keys in the template")
                return

            response = self.ollama_client.invoke(formatted_messages)
            self.display_response(response)
        except KeyError as e:
            print(f"KeyError: Missing key in template: {e}")
        except Exception as e:
            print(f"An error occurred during message formatting or invocation: {e}")








    def escape_special_characters(self, content):
        """Escape special characters in the content."""
        # Add code here to escape special characters
        # Escape single quotes
        escaped_content = content.replace("'", "\\'")
        # Wrap code blocks properly
        escaped_content = re.sub(r'(```(?:[^`]+)?```)', r"''' \1 '''", escaped_content)
        return escaped_content








    def format_history(self, message):
        """Format chat history for prompting the AI model."""
        recent_messages = self.memory.chat_memory.messages[-5:]
        formatted_history = []
        for msg in recent_messages:
            if isinstance(msg, HumanMessage):
                formatted_history.append(('human', msg.content))
            elif isinstance(msg, AIMessage):
                formatted_history.append(('ai', msg.content))
            else:
                print(f"Unexpected message type: {type(msg)}")
        formatted_history.append(('human', message))
        if self.editor_window and self.editor_window.isVisible() and self.editor_window.get_file_contents():
            formatted_history.append(('human', self.editor_window.get_file_contents()))
        return formatted_history

    def display_response(self, response):
        """Display the response from the AI model."""
        parsed_response = response.content if isinstance(response, AIMessage) else self.output_parser.parse(response)
        add_message_to_db('AI', parsed_response)
        self.memory.chat_memory.add_ai_message(parsed_response)
        self.text_edit.append(f"AI: {parsed_response}\n")

    def delete_last_message(self):
        """Delete the last message from the chat history."""
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute('DELETE FROM messages WHERE id = (SELECT MAX(id) FROM messages)')
            conn.commit()
        self.load_chat_history()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    style_file = "style.css"
    if os.path.isfile(style_file):
        with open(style_file, "r") as file:
            app.setStyleSheet(file.read())
    window = ChatWindow()
    window.show()
    sys.exit(app.exec())
