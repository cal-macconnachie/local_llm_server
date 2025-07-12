# README for Local LLM Server

## Project Overview
The Local LLM Server is a simple application that hosts a large language model locally, allowing users to interact with it via a web interface. The server accepts user input, processes it through the model, and returns generated responses.

## Project Structure
```
local_llm_server
├── src
│   ├── main.py         # Entry point for the application
│   ├── server.py       # Web server setup and API endpoints
│   └── utils.py        # Utility functions for input processing and response formatting
├── requirements.txt     # List of dependencies
└── README.md            # Documentation for the project
```

## Setup Instructions
1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd local_llm_server
   ```

2. **Create a virtual environment (optional but recommended):**
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the required dependencies:**
   ```
   pip install -r requirements.txt
   ```

## Usage
1. **Start the server:**
   ```
   python src/server.py
   ```

2. **Send a request to the server:**
   You can use tools like `curl` or Postman to send a POST request to the server. For example:
   ```
   curl -X POST http://localhost:8004/generate/ -H "Content-Type: application/json" -d '{"prompt": "Tell me the most important thing to know about LLMs"}'
   ```

3. **Receive the response:**
   The server will return a JSON response containing the generated text.

## Example
To get a response from the model, send a prompt like:
```json
{
  "prompt": "Tell me about large language models."
}
```

## License
This project is licensed under the MIT License. See the LICENSE file for more details.

venv/bin/activate && python src/server.py