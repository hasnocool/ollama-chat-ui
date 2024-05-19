import sys
import asyncio
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton
from PyQt6.QtCore import QThread, pyqtSignal, pyqtSlot, QObject
from PyQt6.QtGui import QTextCursor
from ollama import AsyncClient

class ChatWorker(QObject):
    new_message = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client

    async def chat(self, user_input):
        message = {'role': 'user', 'content': user_input}
        async for part in await self.client.chat(model='llama3', messages=[message], stream=True):
            self.new_message.emit(part['message']['content'])

    def stop(self):
        self.finished.emit()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.client = AsyncClient(host='http://192.168.1.25:11434')
        self.chat_worker = ChatWorker(self.client)
        self.chat_thread = QThread()
        self.chat_worker.moveToThread(self.chat_thread)
        self.chat_worker.new_message.connect(self.append_message)
        self.chat_thread.start()
        self.event_loop = asyncio.new_event_loop()
        self.chat_worker_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.chat_worker_loop)
        self.loop_thread = QThread()
        self.loop_thread.run = self.chat_worker_loop.run_forever
        self.loop_thread.start()

    def init_ui(self):
        self.setWindowTitle('Async Chat with PyQt6')
        self.setGeometry(100, 100, 800, 600)

        self.layout = QVBoxLayout()

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.layout.addWidget(self.chat_display)

        self.user_input = QLineEdit()
        self.user_input.returnPressed.connect(self.on_user_input)
        self.layout.addWidget(self.user_input)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.on_user_input)
        self.layout.addWidget(self.send_button)

        self.setLayout(self.layout)

    @pyqtSlot()
    def on_user_input(self):
        user_text = self.user_input.text()
        if user_text.lower() == "exit":
            self.chat_worker.stop()
            self.chat_thread.quit()
            self.chat_thread.wait()
            self.loop_thread.quit()
            self.loop_thread.wait()
            self.close()
        else:
            self.user_input.clear()
            self.chat_display.append(f"You: {user_text}\n")
            asyncio.run_coroutine_threadsafe(self.handle_chat(user_text), self.chat_worker_loop)

    async def handle_chat(self, user_text):
        await self.chat_worker.chat(user_text)

    @pyqtSlot(str)
    def append_message(self, message):
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(message)
        self.chat_display.setTextCursor(cursor)
        self.chat_display.ensureCursorVisible()

    def closeEvent(self, event):
        self.chat_worker.stop()
        self.chat_thread.quit()
        self.chat_thread.wait()
        self.loop_thread.quit()
        self.loop_thread.wait()
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    # Start the application's event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
