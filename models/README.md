# Model Management Guide

This directory contains GGUF model files for the Local LLM Server. Models are loaded via llama.cpp for optimal performance and compatibility.

## Supported Model Formats

- **GGUF**: Recommended format (GPT-Generated Unified Format)
- **Quantized models**: Q4_K_M, Q5_K_M, Q8_0 for different performance/quality tradeoffs
- **Context lengths**: Models with 4K, 8K, 16K, or 32K context windows

## Default Model

The server looks for `phi-3-mini-4k-instruct.Q4_K_M.gguf` by default. Override with the `LLM_MODEL` environment variable.

## Recommended Models

### Small & Fast (1-4B parameters)
- **Phi-3 Mini**: `phi-3-mini-4k-instruct.Q4_K_M.gguf` (2.3GB)
  - Excellent for general chat and coding
  - Low memory usage, fast responses
  - 4K context window

- **Gemma 2B**: `gemma-2b-it.Q4_K_M.gguf` (1.6GB)
  - Google's efficient model
  - Good for simple tasks

### Medium Performance (7-8B parameters)
- **Llama 3.1 8B**: `llama-3.1-8b-instruct.Q4_K_M.gguf` (4.7GB)
  - Excellent general performance
  - Good reasoning capabilities
  - 8K context window

- **Mistral 7B**: `mistral-7b-instruct-v0.3.Q4_K_M.gguf` (4.1GB)
  - Fast inference
  - Strong coding abilities

### Large & Powerful (13B+ parameters)
- **Llama 3.1 70B**: `llama-3.1-70b-instruct.Q4_K_M.gguf` (40GB)
  - Near GPT-4 performance
  - Requires significant RAM (48GB+)
  - 8K context window

## Download Sources

### Hugging Face
```bash
# Using huggingface-hub
pip install huggingface-hub
huggingface-cli download microsoft/Phi-3-mini-4k-instruct-gguf \
  Phi-3-mini-4k-instruct-q4.gguf --local-dir models/
```

### Popular Model Collections
- [TheBloke's GGUF Models](https://huggingface.co/TheBloke)
- [Microsoft Phi-3 GGUF](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf)
- [Meta Llama GGUF](https://huggingface.co/meta-llama)

## Installation

1. **Place model file** in this `models/` directory
2. **Set environment variable** (optional):
   ```bash
   export LLM_MODEL="your-model-name.gguf"
   ```
3. **Restart the server** to load the new model

## Model Performance Guide

### Memory Requirements
- **Q4_K_M**: ~50% of model parameter count in GB
- **Q5_K_M**: ~60% of model parameter count in GB
- **Q8_0**: ~100% of model parameter count in GB

### Quality vs Speed
- **Q4_K_M**: Best balance of speed and quality
- **Q5_K_M**: Higher quality, slightly slower
- **Q8_0**: Highest quality, slowest inference

### Context Window
- **4K**: Good for short conversations
- **8K**: Better for longer context
- **32K**: Excellent for document analysis

## Configuration

### Server Settings
Edit `src/server.py` to adjust:
- `n_ctx`: Context window size
- `n_threads`: CPU threads (default: all cores)
- `n_batch`: Batch size (default: 512)

### Performance Tuning
```python
model = Llama(
    model_path=model_path,
    n_ctx=8192,          # Increase for longer context
    n_threads=8,         # Adjust for your CPU
    n_batch=1024,        # Larger batch = more memory, faster
    use_mmap=True,       # Memory mapping (recommended)
    use_mlock=True,      # Lock in memory (recommended)
)
```

## Troubleshooting

### Model Not Loading
- Check file exists in `models/` directory
- Verify file isn't corrupted (re-download)
- Ensure sufficient RAM

### Out of Memory
- Use smaller quantized model (Q4_K_M instead of Q8_0)
- Reduce context window (`n_ctx`)
- Close other applications

### Slow Performance
- Use Q4_K_M quantization
- Increase `n_threads` to match CPU cores
- Enable `use_mmap=True`

## Model File Naming

Follow this convention for easy identification:
```
{model-name}-{size}-{variant}.{quantization}.gguf

Examples:
- phi-3-mini-4k-instruct.Q4_K_M.gguf
- llama-3.1-8b-instruct.Q4_K_M.gguf
- mistral-7b-instruct-v0.3.Q5_K_M.gguf
```

## License Notes

Models have different licenses:
- **Phi-3**: MIT License (commercial use allowed)
- **Llama**: Custom license (check usage restrictions)
- **Mistral**: Apache 2.0 (commercial use allowed)
- **Gemma**: Custom license (check terms)

Always verify model licenses for your use case.