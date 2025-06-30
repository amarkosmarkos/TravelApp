# text_chunker.py
import tiktoken

def chunk_text(text, chunk_size=1200, overlap=50, model="gpt-4-1106-preview"):
    enc = tiktoken.encoding_for_model(model)
    tokens = enc.encode(text)
    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk = enc.decode(tokens[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks 