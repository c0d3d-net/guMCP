# Simple Tools guMCP Server

guMCP server implementation for simple data storage and retrieval operations. This server provides basic key-value storage functionality for testing and demonstration purposes.

## 📦 Prerequisites

- Python 3.11+
- A Simple Tools API key (for demonstration purposes)

## 🔑 API Token Generation

To use this server, you'll need an API key for the Simple Tools service. This is a template server, so you can use any string as your API key for testing purposes.

## 🔐 Local Authentication

To authenticate and save your API key for local testing, run:

```bash
python src/servers/simple-tools-server/main.py auth
```

This will:
1. Prompt you to enter your Simple Tools API key
2. Store your credentials securely for future use

## 🛠️ Available Tools

### store_data
Store a key-value pair in the server's memory

### retrieve_data  
Retrieve a value by its key from the server's storage

### list_data
List all stored key-value pairs in the server

## 💡 Usage Examples

This server maintains user-specific data stores and provides basic CRUD operations for key-value data management. 