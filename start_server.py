#!/usr/bin/env python3
import subprocess
import socket
import sys
import os
import argparse
import torch
import glob

# Auto-activate virtual environment if not already activated
if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
    venv_path = os.path.join(os.path.dirname(__file__), 'venv')
    if os.path.exists(venv_path):
        # Restart script with venv python
        venv_python = os.path.join(venv_path, 'bin', 'python')
        if os.path.exists(venv_python):
            os.execv(venv_python, [venv_python] + sys.argv)

def get_local_ip():
    """Get the local IP address of this machine"""
    try:
        # Connect to a remote address to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"

def detect_gpu():
    """Detect if GPU is available"""
    try:
        return torch.cuda.is_available() and torch.cuda.device_count() > 0
    except:
        return False

def get_backend_choice(backend_arg):
    """Determine which backend to use based on argument and GPU availability"""
    if backend_arg:
        return backend_arg
    return "llama.cpp"

def scan_models():
    """Scan models directory and return available models"""
    models_dir = os.path.join(os.path.dirname(__file__), "models")
    if not os.path.exists(models_dir):
        return []
    
    # Look for .gguf files
    gguf_files = glob.glob(os.path.join(models_dir, "*.gguf"))
    return [os.path.basename(f) for f in gguf_files]

def select_model(models, no_choice=False):
    """Allow user to select a model from available models"""
    if not models:
        print("No models found in models directory!")
        return None
    
    if no_choice:
        return models[0]
    
    print("\nAvailable models:")
    for i, model in enumerate(models, 1):
        print(f"{i}. {model}")
    
    while True:
        try:
            choice = input(f"\nSelect a model (1-{len(models)}): ")
            idx = int(choice) - 1
            if 0 <= idx < len(models):
                return models[idx]
            else:
                print(f"Please enter a number between 1 and {len(models)}")
        except (ValueError, KeyboardInterrupt):
            print("\nExiting...")
            return None

def main():
    parser = argparse.ArgumentParser(description="Start Local LLM Server")
    parser.add_argument(
        "--backend", 
        choices=["llama.cpp"],
        help="Backend to use (default: auto-detect based on GPU availability)"
    )
    parser.add_argument("--port", type=int, default=8004, help="Port to run server on")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--no-choice", action="store_true", help="Auto-select first available model")
    
    args = parser.parse_args()
    
    # Scan and select model
    models = scan_models()
    selected_model = select_model(models, args.no_choice)
    
    if not selected_model:
        print("No model selected. Exiting...")
        return
    
    port = args.port
    host = args.host
    backend = get_backend_choice(args.backend)
    
    # Get local IP for display
    local_ip = get_local_ip()
    
    print("="*60)
    print("🚀 Starting Local LLM Server")
    print("="*60)
    print(f"Model:           {selected_model}")
    print(f"Backend:         {backend}")
    print(f"GPU Available:   {detect_gpu()}")
    print(f"Local access:    http://localhost:{port}")
    print(f"Network access:  http://{local_ip}:{port}")
    print("="*60)
    print(f"API endpoint:    http://{local_ip}:{port}/generate/")
    print(f"Example curl:")
    print(f'curl -X POST http://{local_ip}:{port}/generate/ \\')
    print(f'  -H "Content-Type: application/json" \\')
    print(f'  -d \'{{"prompt": "Tell me about LLMs"}}\'')
    print("="*60)
    print("Press Ctrl+C to stop the server")
    print("="*60)
    
    try:
        # Set environment variables for backend and model selection
        os.environ["LLM_BACKEND"] = backend
        os.environ["LLM_MODEL"] = selected_model
        
        # Start the uvicorn server
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "src.server:app", 
            "--host", host, 
            "--port", str(port),
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped")

if __name__ == "__main__":
    main()