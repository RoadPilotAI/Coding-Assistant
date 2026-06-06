import requests
import json
import sys
import re
import os
from bs4 import BeautifulSoup

# Load config
with open("config.json", "r") as f:
    config = json.load(f)

OLLAMA_URL = config["ollama_url"]
MODEL = config["model"]
GITHUB_TOKEN = config["github_token"]
GITHUB_USERNAME = config["github_username"]
WEB_HEADERS = {"User-Agent": "Mozilla/5.0"}
GITHUB_HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

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
    return full_response

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

def github_fetch(url):
    # Convert browser URL to raw content URL if needed
    # https://github.com/user/repo/blob/main/file.py
    # -> https://raw.githubusercontent.com/user/repo/main/file.py
    if "github.com" in url and "/blob/" in url:
        url = url.replace("https://github.com", "https://raw.githubusercontent.com")
        url = url.replace("/blob/", "/")

    try:
        r = requests.get(url, headers=GITHUB_HEADERS, timeout=10)
        r.raise_for_status()
        content = r.text
        return content[:6000]
    except Exception as e:
        return f"Error fetching GitHub file: {e}"

def github_search(query):
    print(f"\nSearching GitHub for: {query}")
    try:
        search_url = "https://api.github.com/search/code"
        params = {
            "q": f"{query} language:python",
            "sort": "indexed",
            "per_page": 3
        }
        r = requests.get(search_url, headers=GITHUB_HEADERS, params=params, timeout=10)
        r.raise_for_status()
        results = r.json()

        if not results.get("items"):
            return "No results found."

        # Take the top result
        top = results["items"][0]
        repo = top["repository"]["full_name"]
        path = top["path"]
        print(f"Found: {repo}/{path}")

        # Fetch the actual file content
        raw_url = f"https://raw.githubusercontent.com/{repo}/HEAD/{path}"
        file_r = requests.get(raw_url, headers=GITHUB_HEADERS, timeout=10)
        file_r.raise_for_status()
        content = file_r.text[:6000]

        return f"Found in {repo}/{path}:\n\n{content}"

    except Exception as e:
        return f"Error searching GitHub: {e}"

def save_code(filename, last_response):
    # Extract code blocks from last response
    pattern = r"```(?:\w+)?\n(.*?)```"
    matches = re.findall(pattern, last_response, re.DOTALL)

    if not matches:
        print("No code blocks found in last response.")
        return

    # If multiple blocks, take the largest one
    code = max(matches, key=len)

    with open(filename, "w", encoding="utf-8") as f:
        f.write(code)

    print(f"Saved to {filename}")

def show_help():
    print("""
Commands:
  Just type to chat with the assistant
  fetch <url>          - Pull any webpage into context
  github fetch <url>   - Pull a GitHub file into context
  github search <query>- Search GitHub for relevant code
  save <filename>      - Save last code response to file
  load <filename>      - Load one of your project files into context
  clear                - Reset conversation
  help                 - Show this message
  quit                 - Exit
""")

def load_file(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()
        return content
    except Exception as e:
        return f"Error loading file: {e}"

def handle_input(user_input, last_response):
    # fetch webpage
    if user_input.startswith("fetch "):
        url = user_input[6:].strip()
        print(f"\nFetching: {url}")
        content = fetch_url(url)
        message = f"I fetched this content from {url}. Use it to help with my project:\n\n{content}"
        return chat(message)

    # github fetch
    elif user_input.startswith("github fetch "):
        url = user_input[13:].strip()
        print(f"\nFetching from GitHub: {url}")
        content = github_fetch(url)
        message = f"Here is code from GitHub ({url}):\n\n{content}\n\nUse this as reference for my project."
        return chat(message)

    # github search
    elif user_input.startswith("github search "):
        query = user_input[14:].strip()
        content = github_search(query)
        message = f"I found this code on GitHub searching for '{query}':\n\n{content}\n\nUse this as reference."
        return chat(message)

    # save code
    elif user_input.startswith("save "):
        filename = user_input[5:].strip()
        save_code(filename, last_response)
        return last_response

    # load local file
    elif user_input.startswith("load "):
        filename = user_input[5:].strip()
        print(f"\nLoading: {filename}")
        content = load_file(filename)
        message = f"Here is my existing code from {filename}:\n\n{content}\n\nRemember this as part of my project."
        return chat(message)

    # help
    elif user_input.lower() == "help":
        show_help()
        return last_response

    # clear
    elif user_input.lower() == "clear":
        conversation.clear()
        conversation.append({
            "role": "system",
            "content": (
                "You are an expert coding assistant. You write clean, well-commented code. "
                "When given fetched web content or GitHub code, extract what is useful and "
                "apply it directly. Always explain what you built and why. "
                "Prefer practical working code over theory."
            )
        })
        print("Conversation cleared.\n")
        return last_response

    else:
        return chat(user_input)

def main():
    print("=== Local Coding Assistant ===")
    print("Type 'help' for commands, 'quit' to exit")
    print("=" * 30 + "\n")

    conversation.append({
        "role": "system",
        "content": (
            "You are an expert coding assistant. You write clean, well-commented code. "
            "When given fetched web content or GitHub code, extract what is useful and "
            "apply it directly. Always explain what you built and why. "
            "Prefer practical working code over theory."
        )
    })

    last_response = ""

    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            if user_input.lower() == "quit":
                print("Bye.")
                sys.exit(0)
            last_response = handle_input(user_input, last_response)
        except KeyboardInterrupt:
            print("\nBye.")
            sys.exit(0)

if __name__ == "__main__":
    main()