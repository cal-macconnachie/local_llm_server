from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import os
import json
import re
from typing import Dict, AsyncGenerator, Optional
from collections import deque

app = FastAPI()

conversation_contexts: Dict[str, deque] = {}
MAX_CONTEXT_LENGTH = 100

async def load_llama_cpp_model():
    """Load llama.cpp model asynchronously"""
    try:
        from llama_cpp import Llama
        model_name = os.environ.get("LLM_MODEL", "phi-3-mini-4k-instruct.Q4_K_M.gguf")
        model_path = os.path.join(os.path.dirname(__file__), "..", "models", model_name)
        
        if not os.path.exists(model_path):
            print(f"Model file not found: {model_path}")
            return None
            
        model = Llama(
            model_path=model_path,
            n_ctx=4096,  # Increased context window
            n_threads=os.cpu_count() or 4,  # Use all available CPU cores
            verbose=False,
            n_batch=512,  # Batch size for prompt processing
            use_mmap=True,  # Memory-mapped file for faster loading
            use_mlock=True,  # Lock model in memory
        )
        print(f"llama.cpp model loaded successfully: {model_name}")
        return model
    except Exception as e:
        print(f"llama.cpp model loading failed: {e}")
        return None

# Load model based on backend selection
backend = os.environ.get("LLM_BACKEND", "llama.cpp")
print(f"Using backend: {backend}")

generator = None

@app.on_event("startup")
async def startup_event():
    global generator
    generator = await load_llama_cpp_model()

class InputText(BaseModel):
    prompt: str
    session_id: str = "default"
    max_tokens: int = None

def estimate_response_tokens(prompt: str) -> int:
    """Estimate required tokens based on prompt characteristics and length"""
    # More generous base token count
    base_tokens = 512
    
    # More sophisticated prompt length analysis
    prompt_length = len(prompt.split())
    char_length = len(prompt)
    
    # Scale with prompt length (longer prompts usually need longer responses)
    if prompt_length > 200:
        base_tokens += 1024
    elif prompt_length > 100:
        base_tokens += 768
    elif prompt_length > 50:
        base_tokens += 512
    elif prompt_length > 20:
        base_tokens += 256
    
    # Character-based scaling for very long prompts
    if char_length > 2000:
        base_tokens += 1024
    elif char_length > 1000:
        base_tokens += 512
    
    # Adjust based on prompt type with more generous allocations
    prompt_lower = prompt.lower()
    
    # Code-related prompts need significantly more tokens
    code_keywords = ['code', 'function', 'script', 'program', 'implement', 'debug', 'refactor', 'class', 'method']
    if any(keyword in prompt_lower for keyword in code_keywords):
        base_tokens += 1536
    
    # Explanation/tutorial prompts need substantial tokens
    explain_keywords = ['explain', 'how to', 'tutorial', 'guide', 'steps', 'walkthrough', 'detail']
    if any(keyword in prompt_lower for keyword in explain_keywords):
        base_tokens += 1024
    
    # List/enumeration prompts need good token allocation
    list_keywords = ['list', 'examples', 'ways', 'methods', 'types', 'table', 'compare', 'options']
    if any(keyword in prompt_lower for keyword in list_keywords):
        base_tokens += 768
    
    # Creative writing needs generous allocation
    creative_keywords = ['story', 'write', 'creative', 'poem', 'essay', 'narrative', 'fiction']
    if any(keyword in prompt_lower for keyword in creative_keywords):
        base_tokens += 1024
    
    # Technical analysis needs more tokens
    analysis_keywords = ['analyze', 'review', 'assessment', 'evaluation', 'research', 'study']
    if any(keyword in prompt_lower for keyword in analysis_keywords):
        base_tokens += 1024
    
    # Question answering with context
    qa_keywords = ['what', 'why', 'how', 'when', 'where', 'which', 'who']
    if any(prompt_lower.startswith(keyword) for keyword in qa_keywords):
        base_tokens += 512
    
    # Set reasonable limits with much higher caps
    final_tokens = min(max(base_tokens, 256), 4096)
    return final_tokens

async def generate_sse_stream(session_id: str, user_prompt: str, max_tokens: int = None) -> AsyncGenerator[str, None]:
    try:
        if generator is None:
            yield json.dumps({"error": "Model not loaded. Please check server logs."}) + "\n"
            return
        
        if "clear context" in user_prompt.lower():
            conversation_contexts[session_id] = deque(maxlen=MAX_CONTEXT_LENGTH)
            yield f"data: {json.dumps({'chunk': 'Context cleared. Starting fresh conversation.'})}\n\n"
            yield "event: done\ndata: {}\n\n"
            return
        
        if session_id not in conversation_contexts:
            conversation_contexts[session_id] = deque(maxlen=MAX_CONTEXT_LENGTH)
        
        conversation_contexts[session_id].append(f"User: {user_prompt}")
        
        # Build proper chat format
        context = "\n".join(list(conversation_contexts[session_id]))
        full_prompt = f"<|system|>You are a helpful AI assistant. Give direct, concise answers. Please ensure your responses are well formatted using markdown and newlines. IMPORTANT: You must wrap ONLY your reasoning and planning in <|thinking|> tags, then provide your final answer OUTSIDE the thinking tags. Example format:\n\n<|thinking|>\nLet me think about this step by step...\n</|thinking|>\n\nHere is my final answer without thinking tags.<|end|>\n{context}\nAssistant:"
        
        # Use provided max_tokens or estimate based on prompt
        if max_tokens is None:
            max_tokens = estimate_response_tokens(user_prompt)
        full_response = ""
        for output in generator(
            full_prompt,
            max_tokens=max_tokens,
            temperature=0.3,
            top_p=0.95,
            repeat_penalty=1.1,
            stop=["</s>", "User:", "Assistant:", "<|end|>", "Support:", "support:", "<system", "AI:", 'Answer:', '<|end_of_instruction|>', '</|end|>'],
            echo=False,
            stream=True
        ):
            token = output['choices'][0]['text']
            # Send all tokens, including empty ones (newlines)
            full_response += token
            
            # Encode newlines as <<NEWLINE>> for frontend processing
            encoded_token = token.replace('\n', '<<NEWLINE>>')
            yield f"data: {json.dumps({'chunk': encoded_token})}\n\n"
            
            # Force flush to ensure immediate streaming
            import asyncio
            await asyncio.sleep(0)  # Yield control immediately
        
        conversation_contexts[session_id].append(f"Assistant: {full_response.strip()}")
        
        # Send end marker
        yield "event: done\ndata: {}\n\n"
            
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
        yield "event: error\ndata: {}\n\n"

@app.post("/generate/")
async def generate_response(input_text: InputText):
    return StreamingResponse(
        generate_sse_stream(input_text.session_id, input_text.prompt, input_text.max_tokens),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )

@app.post("/generate-sync/")
async def generate_response_sync(input_text: InputText):
    try:
        if generator is None:
            return "Model not loaded. Please check server logs."
        
        session_id = input_text.session_id
        user_prompt = input_text.prompt
        
        if "clear context" in user_prompt.lower():
            conversation_contexts[session_id] = deque(maxlen=MAX_CONTEXT_LENGTH)
            return "Context cleared. Starting fresh conversation."
        
        if session_id not in conversation_contexts:
            conversation_contexts[session_id] = deque(maxlen=MAX_CONTEXT_LENGTH)
        
        conversation_contexts[session_id].append(f"User: {user_prompt}")
        
        # Build proper chat format  
        context = "\n".join(list(conversation_contexts[session_id]))
        full_prompt = f"<|system|>You are a helpful AI assistant. Give direct, concise answers. Please ensure your responses are well formatted using markdown and newlines. IMPORTANT: You must wrap ONLY your reasoning and planning in <|thinking|> tags, then provide your final answer OUTSIDE the thinking tags, there MUST ALWAYS be an answer outside the thinking tags. Example format:\n\n<|thinking|>\nLet me think about this step by step...\n</|thinking|>\n\nHere is my final answer without thinking tags.<|end|>\n{context}\nAssistant:"
        max_tokens = input_text.max_tokens or estimate_response_tokens(user_prompt)
        result = generator(
            full_prompt,
            max_tokens=max_tokens,
            temperature=0.8,
            top_p=0.95,
            repeat_penalty=1.1,
            stop=["</s>", "User:"],
            echo=False
        )
        response = result['choices'][0]['text'].strip()
        
        if not response:
            response = "I'm here to help! What would you like to know?"

        conversation_contexts[session_id].append(f"Assistant: {response}")
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)