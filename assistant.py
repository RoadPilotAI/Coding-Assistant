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

def load_file(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error loading file: {e}"

def show_help():
    print("""
Commands:
  Just type to chat with the assistant
  fetch <url>           - Pull any webpage into context
  github fetch <url>    - Pull a GitHub file into context
  github search <query> - Search GitHub for relevant code
  load <filename>       - Load one of your project files into context
  save <filename>       - Save last code response to file
  clear                 - Reset conversation
  help                  - Show this message
  quit                  - Exit
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

    elif user_input.startswith("load "):
        filename = user_input[5:].strip()
        print(f"\nLoading: {filename}")
        content = load_file(filename)
        return chat(f"Here is my existing code from {filename}:\n\n{content}\n\nRemember this as part of my project.")

    elif user_input.lower() == "help":
        show_help()
        return last_response

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