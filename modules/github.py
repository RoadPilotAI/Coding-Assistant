import requests

LINUX_ONLY = ["pyinotify", "inotify", "inotifywait", "epoll"]

def get_headers(token):
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

def github_fetch(url, token):
    """Fetch a specific file from GitHub. Accepts browser or raw URLs."""
    if "github.com" in url and "/blob/" in url:
        url = url.replace("https://github.com", "https://raw.githubusercontent.com")
        url = url.replace("/blob/", "/")
    try:
        r = requests.get(url, headers=get_headers(token), timeout=10)
        r.raise_for_status()
        return r.text[:6000]
    except requests.exceptions.HTTPError as e:
        return f"Error: HTTP {e.response.status_code} — file not found or access denied."
    except requests.exceptions.ConnectionError:
        return "Error: Could not connect to GitHub. Check your internet connection."
    except Exception as e:
        return f"Error fetching GitHub file: {e}"

def github_search(query, token):
    """Search GitHub for relevant Python repos, filter by quality, let user pick."""
    print(f"\nSearching GitHub for: {query}")
    headers = get_headers(token)

    try:
        search_url = "https://api.github.com/search/repositories"
        params = {
            "q": f"{query} language:python",
            "sort": "stars",
            "order": "desc",
            "per_page": 10
        }
        r = requests.get(search_url, headers=headers, params=params, timeout=10)
        r.raise_for_status()
        results = r.json()

        if not results.get("items"):
            return "No GitHub results found for that query."

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
            return "No suitable results found after filtering. Try a different search term."

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

        code_url = "https://api.github.com/search/code"
        code_params = {
            "q": f"{query} repo:{selected['name']} language:python",
            "per_page": 3
        }
        code_r = requests.get(code_url, headers=headers, params=code_params, timeout=10)
        code_r.raise_for_status()
        code_results = code_r.json()

        if not code_results.get("items"):
            return f"Found repo {selected['name']} but couldn't fetch files. Visit: {selected['url']}"

        top_file = code_results["items"][0]
        path = top_file["path"]
        raw_url = f"https://raw.githubusercontent.com/{selected['name']}/HEAD/{path}"

        print(f"Loading: {path}")
        file_r = requests.get(raw_url, headers=headers, timeout=10)
        file_r.raise_for_status()
        content = file_r.text[:6000]

        linux_hits = [lib for lib in LINUX_ONLY if lib in content]
        if linux_hits:
            print(f"  Warning: may use Linux-only libraries: {', '.join(linux_hits)}")

        return (f"From {selected['name']} ({selected['stars']} stars) — {path}:\n\n"
                f"{content}\n\nNote: review for platform compatibility before using.")

    except requests.exceptions.HTTPError as e:
        return f"GitHub API error: HTTP {e.response.status_code}. Token may need 'repo' scope."
    except requests.exceptions.ConnectionError:
        return "Error: Could not connect to GitHub. Check your internet connection."
    except Exception as e:
        return f"Error searching GitHub: {e}"
