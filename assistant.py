import requests
import json
import sys
import os

from modules.web import fetch_url
from modules.github import github_fetch, github_search
from modules.files import load_file, save_code, write_file, edit_file, show_project
from modules.git_tools import git_commit, git_status
from modules.history import save_history, list_history

# Load config
with open("config.json", "r") as f:
    config = json.load(f)

OLLAMA_URL = config["ollama_url"]
MODEL = config["model"]
GITHUB_TOKEN = config["github_token"]
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

conversation = []

MAX_SYSTEM_PROMPT = (
    "Your name is Max. You are a confident, friendly coding assistant built to help "
    "people build real applications — even if they've never written code before. "
    "You always write complete, working, executable code. You never say you cannot "
    "write code. You never hedge or say 'I think' or 'possibly' when you know the answer. "
    "You speak in plain everyday language, avoiding jargon. When you must use a technical "
    "term, you explain it in one simple sentence. "
    "You think of yourself as a knowledgeable friend sitting beside the user, helping "
    "them build something real. You are encouraging and patient. "
    "When asked to build something, you build it — you don't just describe how it could "
    "be built. You provide the complete code, explain what each part does in plain "
    "language, and tell the user exactly what to do next. "
    "When you find code on GitHub or the web, you adapt it to the user's specific needs "
    "rather than just describing it. "
    "You remember everything in this conversation and use that context to give better, "
    "more relevant answers as the session continues. "
    "Your goal is to make the user feel capable and confident, like they can build "
    "anything with your help. "
    "You are also capable of improving yourself — when shown your own source code, "
    "you can suggest and implement improvements to your own functionality."
)

def chat(user_message):
    """Send a message to Max and stream the response."""
    conversation.append({"role": "user", "content": user_message})
    try:
        response = requests.post(OLLAMA_URL, json={
            "model": MODEL,
            "messages": conversation,
            "stream": True
        }, stream=True)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to Ollama. Is it running?")
        print("Start it with: ollama serve\n")
        conversation.pop()
        return ""
    except Exception as e:
        print(f"\nError connecting to Ollama: {e}\n")
        conversation.pop()
        return ""

    full_response = ""
    print("\nMax: ", end="", flush=True)
    for line in response.iter_lines():
        if line:
            try:
                data = json.loads(line)
                chunk = data.get("message", {}).get("content", "")
                print(chunk, end="", flush=True)
                full_response += chunk
                if data.get("done"):
                    break
            except json.JSONDecodeError:
                continue

    print("\n")
    conversation.append({"role": "assistant", "content": full_response})
    return full_response

def show_help():
    print("""
Commands:
  Just type to chat with Max
  fetch <url>               - Pull any webpage into context
  github fetch <url>        - Pull a GitHub file into context
  github search <query>     - Search GitHub for relevant code
  load <filename>           - Load a project file into context
  load self                 - Load assistant.py into context
  save <filename>           - Save last code response to file
  write <filename>          - Write last code response to file with preview
  edit <filename> <change>  - Load a file, make a change, write it back
  project                   - Show all files in the project folder
  commit <message>          - git add, commit and push to GitHub
  status                    - Show uncommitted git changes
  history                   - Save conversation to a timestamped file
  history list              - List all saved history files
  clear                     - Reset conversation
  help                      - Show this message
  quit                      - Exit
""")

def handle_input(user_input, last_response):
    """Route user input to the correct command or chat."""

    if user_input.startswith("fetch "):
        url = user_input[6:].strip()
        print(f"\nFetching: {url}")
        content = fetch_url(url)
        return chat(f"I fetched this content from {url}. Use it to help with my project:\n\n{content}")

    elif user_input.startswith("github fetch "):
        url = user_input[13:].strip()
        print(f"\nFetching from GitHub: {url}")
        content = github_fetch(url, GITHUB_TOKEN)
        return chat(f"Here is code from GitHub ({url}):\n\n{content}\n\nUse this as reference.")

    elif user_input.startswith("github search "):
        query = user_input[14:].strip()
        content = github_search(query, GITHUB_TOKEN)
        return chat(f"I found this code on GitHub searching for '{query}':\n\n{content}\n\nUse this as reference.")

    elif user_input.startswith("save "):
        filename = user_input[5:].strip()
        save_code(filename, last_response, PROJECT_DIR)
        return last_response

    elif user_input.startswith("write "):
        filename = user_input[6:].strip()
        write_file(filename, last_response, PROJECT_DIR)
        return last_response

    elif user_input.startswith("edit "):
        parts = user_input[5:].strip().split(" ", 1)
        if len(parts) < 2:
            print("Usage: edit <filename> <what to change>")
            return last_response
        return edit_file(parts[0], parts[1], PROJECT_DIR, chat)

    elif user_input.startswith("load "):
        filename = user_input[5:].strip()
        print(f"\nLoading: {filename}")
        content = load_file(filename, PROJECT_DIR)
        return chat(f"Here is my existing code from {filename}:\n\n{content}\n\nRemember this as part of my project.")

    elif user_input.lower() == "project":
        show_project(PROJECT_DIR)
        return last_response

    elif user_input.startswith("commit "):
        message = user_input[7:].strip()
        if not message:
            print("Usage: commit <message>")
            return last_response
        git_commit(message, PROJECT_DIR)
        return last_response

    elif user_input.lower() == "status":
        git_status(PROJECT_DIR)
        return last_response

    elif user_input.lower() == "history list":
        list_history(PROJECT_DIR)
        return last_response

    elif user_input.lower() == "history":
        save_history(conversation, PROJECT_DIR)
        return last_response

    elif user_input.lower() == "help":
        show_help()
        return last_response

    elif user_input.lower() == "clear":
        conversation.clear()
        conversation.append({"role": "system", "content": MAX_SYSTEM_PROMPT})
        print("Conversation cleared.\n")
        return last_response

    else:
        return chat(user_input)

def main():
    print("=== Max - Your Coding Assistant ===")
    print("Type 'help' for commands, 'quit' to exit")
    print("=" * 35 + "\n")

    conversation.append({"role": "system", "content": MAX_SYSTEM_PROMPT})

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
