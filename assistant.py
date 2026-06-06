import requests
import json
import sys
from bs4 import BeautifulSoup

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5-coder:3b"
WEB_HEADERS = {"User-Agent": "Mozilla/5.0"}

conversation = []

def chat(user_message):
    conversation.append({"role": "user", "content": user_message})
    response = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "messages": conversation,
        "stream": True
    }, stream=True)

    full_response = ""
    print("\nAssistant: ", end="", flush=True)
    for line in response.iter_lines():
        if line:
            data = json.loads(line)
            chunk = data.get("message", {}).get("content", "")
            print(chunk, end="", flush=True)
            full_response += chunk
            if data.get("done"):
                break

    print("\n")
    conversation.append({"role": "assistant", "content": full_response})

def fetch_url(url):
    try:
        r = requests.get(url, headers=WEB_HEADERS, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        return text[:4000]
    except Exception as e:
        return f"Error fetching URL: {e}"

def handle_input(user_input):
    if user_input.startswith("fetch "):
        url = user_input[6:].strip()
        print(f"\nFetching: {url}")
        content = fetch_url(url)
        message = f"I fetched this content from {url}. Use it to help with my project:\n\n{content}"
        chat(message)
    else:
        chat(user_input)

def main():
    print("=== Local Coding Assistant ===")
    print("Commands:")
    print("  Just type to chat")
    print("  'fetch https://...' to pull a webpage into context")
    print("  'clear' to reset conversation")
    print("  'quit' to exit")
    print("=" * 30 + "\n")

    conversation.append({
        "role": "system",
        "content": (
            "You are an expert coding assistant. You write clean, well-commented code. "
            "When given fetched web content, extract what's useful and apply it directly. "
            "Always explain what you built and why. Prefer practical working code over theory."
        )
    })

    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            if user_input.lower() == "quit":
                print("Bye.")
                sys.exit(0)
            if user_input.lower() == "clear":
                conversation.clear()
                print("Conversation cleared.\n")
                continue
            handle_input(user_input)
        except KeyboardInterrupt:
            print("\nBye.")
            sys.exit(0)

if __name__ == "__main__":
    main()