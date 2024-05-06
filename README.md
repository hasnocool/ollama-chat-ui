# Chat Application with PyQt6 and LangChain Integration

This project is a Python-based chat application that utilizes PyQt6 for the graphical user interface and LangChain for AI-driven chat functionalities. It features real-time chat capabilities, database storage for chat history, and a text editor for script interactions.

## Features

- **GUI based on PyQt6**: Provides a responsive and intuitive user interface for chat interactions and text editing.
- **LangChain Integration**: Utilizes LangChain models for AI-driven chat responses.
- **SQLite Database**: Stores chat history in a local SQLite database, ensuring persistence of data.
- **Threading**: Implements Python's threading to handle database operations and AI interactions without blocking the user interface.
- **File Operations**: Includes a text editor window for opening, reading, and interacting with text files.
- **Dynamic Model Selection**: Allows users to select different chat models dynamically from a drop-down menu.

## Installation

To run this application, you need Python installed on your machine along with the following packages:

```bash
pip install PyQt6 sqlite3 re requests
pip install langchain_community langchain_core
```

## Usage

Clone the repository or download the source code.
Navigate to the project directory.
Run the application using Python:

`python VisualContentSearch.py`

## Configuration

API_BASE_URL: Set the base URL for the API that provides the chat models.
DB_FILE: Name of the SQLite database file for storing chat history.
DEFAULT_MODEL: Default chat model to use.

## Contributing

Contributions to this project are welcome! Please fork the repository and submit a pull request with your features or fixes.
License

This project is released under the MIT License. See the LICENSE file in the repository for more details.
