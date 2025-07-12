# Local LLM Server

A high-performance local language model server with streaming responses, conversation memory, and intelligent token estimation. Built with FastAPI and llama.cpp for optimal performance.

## Features

- **Streaming & Sync APIs**: Real-time streaming responses via Server-Sent Events (SSE) and traditional synchronous endpoints
- **Conversation Memory**: Context-aware conversations with configurable memory length
- **Intelligent Token Estimation**: Dynamic token allocation based on prompt type and complexity
- **Thinking Block Support**: AI reasoning visualization with `<|thinking|>` blocks
- **Terminal Chat Client**: Feature-rich command-line interface with markdown rendering
- **Model Flexibility**: Support for various GGUF models via llama.cpp
- **Performance Optimized**: Memory mapping, multi-threading, and efficient batching

## Project Structure

```
local_llm_server/
├── src/
│   └── server.py           # FastAPI server with streaming/sync endpoints
├── models/                 # Model storage directory
│   └── README.md          # Model management guide
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Quick Start

### 1. Installation

```bash
git clone <repository-url>
cd local_llm_server
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Download a Model

Place GGUF model files in the `models/` directory. Default model: `phi-3-mini-4k-instruct.Q4_K_M.gguf`

### 3. Start the Server

```bash
python src/server.py
```

Server runs on `http://localhost:8004`

### 4. Use the Terminal Chat Client

```bash
./chat
```

## API Endpoints

### Streaming Chat (SSE)
```bash
curl -X POST http://localhost:8004/generate/ \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "prompt": "Explain quantum computing",
    "session_id": "my_session",
    "max_tokens": 1000
  }'
```

### Synchronous Chat
```bash
curl -X POST http://localhost:8004/generate-sync/ \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a Python function",
    "session_id": "my_session"
  }'
```

## Configuration

### Environment Variables

- `LLM_MODEL`: Model filename (default: `phi-3-mini-4k-instruct.Q4_K_M.gguf`)
- `LLM_BACKEND`: Backend type (default: `llama.cpp`)

### Request Parameters

- `prompt`: Your message/question
- `session_id`: Conversation identifier (optional, default: "default")
- `max_tokens`: Response length limit (optional, auto-estimated)

## Features in Detail

### Conversation Memory
Sessions maintain context up to 100 exchanges. Clear context with "clear context" in your prompt.

### Token Estimation
Intelligent estimation based on:
- Prompt length and complexity
- Content type (code, explanations, lists, etc.)
- Dynamic scaling (256-4096 tokens)

### Thinking Blocks
AI shows reasoning process in gray `<|thinking|>` blocks before final answers.

### Terminal Chat Client
- Real-time streaming responses
- Markdown rendering (code blocks, formatting)
- Conversation history
- Commands: `/help`, `/history`, `/clear`, `/quit`

## Performance Tuning

The server automatically optimizes:
- **Memory mapping**: Faster model loading
- **Multi-threading**: Uses all CPU cores
- **Batch processing**: 512-token batches
- **Context window**: 4096 tokens

## Troubleshooting

### Model Not Found
Ensure model file exists in `models/` directory and filename matches `LLM_MODEL` environment variable.

### Connection Issues
Check server is running on port 8004 and not blocked by firewall.

### Memory Issues
Use smaller quantized models (Q4_K_M) or reduce context window.

## License

MIT License