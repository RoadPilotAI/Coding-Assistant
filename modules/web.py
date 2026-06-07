import requests
from bs4 import BeautifulSoup

WEB_HEADERS = {"User-Agent": "Mozilla/5.0"}

def fetch_url(url):
    """Fetch a webpage and return clean text content, capped at 4000 characters."""
    try:
        r = requests.get(url, headers=WEB_HEADERS, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        return text[:4000]
    except requests.exceptions.ConnectionError:
        return "Error: Could not connect. Check your internet connection."
    except requests.exceptions.Timeout:
        return "Error: Request timed out. The site may be slow or unavailable."
    except requests.exceptions.HTTPError as e:
        return f"Error: HTTP {e.response.status_code} — page not found or access denied."
    except Exception as e:
        return f"Error fetching URL: {e}"
