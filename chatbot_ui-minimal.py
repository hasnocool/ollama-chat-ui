import sys
import requests
import json
from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit, QLineEdit, QVBoxLayout, QWidget, QPushButton
from PyQt6.QtCore import QThread, pyqtSignal

class ModelPullThread(QThread):
    response_received = pyqtSignal(dict)

    def __init__(self, prompt, stream=False):
        super().__init__()
        self.prompt = prompt
        self.stream = stream

    def run(self):
        url = "http://192.168.1.26:11434/api/generate"
        payload = {
            "model": "llama3",
            "prompt": self.prompt,
            "stream": self.stream
        }

        response = requests.post(url, data=json.dumps(payload))

        if response.status_code == 200:
            response_data = response.json()
            self.response_received.emit(response_data)
        else:
            self.response_received.emit({"error": f"Request failed with status code {response.status_code}"})

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chat UI")

        # Create widgets
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.input_line = QLineEdit()
        self.input_line.returnPressed.connect(self.send_message)
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)

        # Create layout
        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.text_edit)
        layout.addWidget(self.input_line)
        layout.addWidget(self.send_button)
        central_widget.setLayout(layout)

        self.setCentralWidget(central_widget)

        # Initialize chat history
        self.chat_history = []

    def send_message(self):
        user_message = self.input_line.text().strip()
        if user_message:
            self.chat_history.append({"role": "user", "content": user_message})
            self.input_line.clear()
            self.text_edit.append(f"User: {user_message}")

            prompt = self.construct_prompt()
            self.thread = ModelPullThread(prompt, stream=False)
            self.thread.response_received.connect(self.handle_response)
            self.thread.start()

    def construct_prompt(self):
        prompt = ""
        for message in self.chat_history[-5:]:
            prompt += f"{message['role'].capitalize()}: {message['content']}\n"
        return prompt

    def handle_response(self, response_data):
        if "error" in response_data:
            self.text_edit.append(f"Error: {response_data['error']}")
        else:
            response_text = response_data["response"]
            self.text_edit.append(f"Assistant: {response_text}")
            self.chat_history.append({"role": "assistant", "content": response_text})

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
