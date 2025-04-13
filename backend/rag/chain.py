from .ollama_client import call_ollama

def get_answer(query: str) -> str:
    # Eventually you’ll inject retrieved docs here too
    system_prompt = "You are a helpful assistant answering user questions.\n"
    full_prompt = f"{system_prompt}\nUser: {query}\nAssistant:"
    return call_ollama(full_prompt)
