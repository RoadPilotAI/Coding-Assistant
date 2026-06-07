import requests
import json
import sys
import re
import os
import subprocess
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
    conversation.append({"role": "user", "content": user_message})
    response = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "messages": conversation,
        "stream": True
    }, stream=True)

    full_response = ""
    print("\nMax: ", end="", flush=True)
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
    if "github.com" in url and "/blob/" in url:
        url = url.replace("https://github.com", "https://raw.githubusercontent.com")
        url = url.replace("/blob/", "/")
    try:
        r = requests.get(url, headers=GITHUB_HEADERS, timeout=10)
        r.raise_for_status()
        return r.text[:6000]
    except Exception as e:
        return f"Error fetching GitHub file: {e}"

def github_search(query):
    print(f"\nSearching GitHub for: {query}")
    try:
        search_url = "https://api.github.com/search/repositories"
        params = {
            "q": f"{query} language:python",
            "sort": "stars",
            "order": "desc",
            "per_page": 10
        }
        r = requests.get(search_url, headers=GITHUB_HEADERS, params=params, timeout=10)
        r.raise_for_status()
        results = r.json()

        if not results.get("items"):
            print("No results found.")
            return "No GitHub results found for that query."

        LINUX_ONLY = ["pyinotify", "inotify", "inotifywait", "epoll"]
        candidates = []

        for repo in results["items"]:
            if repo.get("archived"):
                continue
            updated = repo.get("updated_at", "")
            if updated and updated[:4] < "2020":
                continue
            candidates.append({
                "name": repo["full_name"],
                "stars": repo.get("stargazers_count", 0),
                "description": repo.get("description") or "",
                "updated": updated[:4] if updated else "unknown",
                "url": repo["html_url"]
            })

        if not candidates:
            print("No suitable results found after filtering.")
            return "No suitable GitHub results found. Try a different search term."

        top = candidates[:3]
        print("\nTop results:")
        for i, repo in enumerate(top):
            print(f"  [{i+1}] {repo['name']} ({repo['stars']} stars, updated {repo['updated']})")
            if repo['description']:
                print(f"      {repo['description'][:80]}")

        print()
        choice = input("Pick a result to load [1/2/3] or 's' to skip: ").strip().lower()

        if choice == 's':
            return "Search skipped."

        try:
            index = int(choice) - 1
            if index < 0 or index >= len(top):
                raise ValueError
        except ValueError:
            print("Invalid choice, loading first result.")
            index = 0

        selected = top[index]
        print(f"\nFetching files from: {selected['name']}")

        code_search_url = "https://api.github.com/search/code"
        code_params = {
            "q": f"{query} repo:{selected['name']} language:python",
            "per_page": 3
        }
        code_r = requests.get(code_search_url, headers=GITHUB_HEADERS,
                              params=code_params, timeout=10)
        code_r.raise_for_status()
        code_results = code_r.json()

        if not code_results.get("items"):
            return f"Found repo {selected['name']} but couldn't fetch specific files. Visit: {selected['url']}"

        top_file = code_results["items"][0]
        path = top_file["path"]
        raw_url = f"https://raw.githubusercontent.com/{selected['name']}/HEAD/{path}"

        print(f"Loading: {path}")
        file_r = requests.get(raw_url, headers=GITHUB_HEADERS, timeout=10)
        file_r.raise_for_status()
        content = file_r.text[:6000]

        linux_hits = [lib for lib in LINUX_ONLY if lib in content]
        if linux_hits:
            print(f"  Warning: this file may use Linux-only libraries: {', '.join(linux_hits)}")

        return (f"From {selected['name']} ({selected['stars']} stars) — {path}:\n\n"
                f"{content}\n\nNote: review for platform compatibility before using directly.")

    except Exception as e:
        return f"Error searching GitHub: {e}"

def save_code(filename, last_response):
    pattern = r"```(?:\w+)?\n(.*?)```"
    matches = re.findall(pattern, last_response, re.DOTALL)
    if not matches:
        print("No code blocks found in last response.")
        return
    code = max(matches, key=len)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(code)
    print(f"Saved to {filename}")

def write_file(filename, last_response):
    pattern = r"```(?:\w+)?\n(.*?)```"
    matches = re.findall(pattern, last_response, re.DOTALL)
    if not matches:
        print("No code blocks found in last response.")
        return

    code = max(matches, key=len)
    print(f"\n--- Preview of {filename} ---")
    print(code[:500])
    if len(code) > 500:
        print(f"... ({len(code) - 500} more characters)")
    print(f"--- End Preview ---\n")

    confirm = input(f"Write this to {filename}? [y/n]: ").strip().lower()
    if confirm == 'y':
        with open(filename, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"Written to {filename}")
    else:
        print("Cancelled.")

def edit_file(filename, user_request):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            current_content = f.read()
    except FileNotFoundError:
        print(f"File not found: {filename}")
        return ""

    print(f"\nLoading {filename} and asking Max to edit it...")
    message = (
        f"Here is the current content of {filename}:\n\n"
        f"```\n{current_content}\n```\n\n"
        f"Please make this change: {user_request}\n\n"
        f"Return the complete updated file, not just the changed part."
    )
    response = chat(message)

    pattern = r"```(?:\w+)?\n(.*?)```"
    matches = re.findall(pattern, response, re.DOTALL)
    if not matches:
        print("Max didn't return a code block. Try asking again.")
        return response

    updated_code = max(matches, key=len)
    print(f"\n--- Preview of updated {filename} ---")
    print(updated_code[:500])
    if len(updated_code) > 500:
        print(f"... ({len(updated_code) - 500} more characters)")
    print(f"--- End Preview ---\n")

    confirm = input(f"Write updated version to {filename}? [y/n]: ").strip().lower()
    if confirm == 'y':
        with open(filename, "w", encoding="utf-8") as f:
            f.write(updated_code)
        print(f"Updated {filename}")
    else:
        print("Cancelled.")

    return response

def show_project():
    print(f"\n--- Project Files in {PROJECT_DIR} ---")
    skip = {"venv", "__pycache__", ".git"}
    for item in sorted(os.listdir(PROJECT_DIR)):
        if item in skip or item.startswith("."):
            continue
        full_path = os.path.join(PROJECT_DIR, item)
        if os.path.isfile(full_path):
            size = os.path.getsize(full_path)
            print(f"  {item} ({size:,} bytes)")
        elif os.path.isdir(full_path):
            print(f"  {item}/")
    print()

def git_commit(message):
    print(f"\nRunning git add...")
    try:
        result = subprocess.run(
            ["git", "add", "."],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"git add failed: {result.stderr}")
            return

        print(f"Committing: {message}")
        result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"git commit failed: {result.stderr}")
            return

        print("Pushing to GitHub...")
        result = subprocess.run(
            ["git", "push"],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"git push failed: {result.stderr}")
            return

        print(f"Done. Pushed to GitHub with message: '{message}'")

    except Exception as e:
        print(f"Git error: {e}")

def save_history():
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"history_{timestamp}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        for message in conversation:
            role = message["role"].upper()
            content = message["content"]
            if role == "SYSTEM":
                continue
            f.write(f"[{role}]\n{content}\n\n{'='*50}\n\n")
    print(f"Conversation saved to {filename}")
    return filename

def load_file(filename):
    if filename.lower() == "self":
        filename = "assistant.py"
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error loading file: {e}"

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
  history                   - Save conversation to a timestamped file
  clear                     - Reset conversation
  help                      - Show this message
  quit                      - Exit
""")

def handle_input(user_input, last_response):
    if user_input.startswith("fetch "):
        url = user_input[6:].strip()
        print(f"\nFetching: {url}")
        content = fetch_url(url)
        return chat(f"I fetched this content from {url}. Use it to help with my project:\n\n{content}")

    elif user_input.startswith("github fetch "):
        url = user_input[13:].strip()
        print(f"\nFetching from GitHub: {url}")
        content = github_fetch(url)
        return chat(f"Here is code from GitHub ({url}):\n\n{content}\n\nUse this as reference.")

    elif user_input.startswith("github search "):
        query = user_input[14:].strip()
        content = github_search(query)
        return chat(f"I found this code on GitHub searching for '{query}':\n\n{content}\n\nUse this as reference.")

    elif user_input.startswith("save "):
        filename = user_input[5:].strip()
        save_code(filename, last_response)
        return last_response

    elif user_input.startswith("write "):
        filename = user_input[6:].strip()
        write_file(filename, last_response)
        return last_response

    elif user_input.startswith("edit "):
        parts = user_input[5:].strip().split(" ", 1)
        if len(parts) < 2:
            print("Usage: edit <filename> <what to change>")
            return last_response
        filename = parts[0]
        request = parts[1]
        return edit_file(filename, request)

    elif user_input.startswith("load "):
        filename = user_input[5:].strip()
        print(f"\nLoading: {filename}")
        content = load_file(filename)
        return chat(f"Here is my existing code from {filename}:\n\n{content}\n\nRemember this as part of my project.")

    elif user_input.lower() == "project":
        show_project()
        return last_response

    elif user_input.startswith("commit "):
        message = user_input[7:].strip()
        if not message:
            print("Usage: commit <message>")
            return last_response
        git_commit(message)
        return last_response

    elif user_input.lower() == "history":
        save_history()
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