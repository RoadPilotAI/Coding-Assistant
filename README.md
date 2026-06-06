# Coding Assistant 🤖

A local AI coding assistant that runs entirely on your own computer — no subscriptions, no data centers, no internet required to think. Powered by [Ollama](https://ollama.com) and open source language models.

Built for two kinds of people:
- **Technically curious non-coders** who want to explore AI and start building things without needing a computer science degree
- **Experienced developers** who want powerful AI assistance without sending their code to someone else's server

---

## Why Local AI?

Every time you use a cloud AI service, your prompts and code travel to a massive data center, consume enormous energy, and are processed on hardware you don't control. This project takes a different approach:

- Your code never leaves your machine
- No API keys or subscriptions required
- Works offline once set up
- Runs on modest consumer hardware (8GB RAM laptop is fine)
- Gets smarter over time as better small models are released

---

## What It Does

- **Chat with an AI coding assistant** that understands your project and writes clean, explained code
- **Fetch live documentation** from any webpage and use it to inform the code it writes
- **Search GitHub** for open source solutions and learn from real working code
- **Pull specific files** from any public GitHub repository directly into context
- **Load your own files** so the assistant understands your existing code before suggesting changes
- **Save generated code** directly to files in your project without copy/pasting

---

## Requirements

- Windows 10 or 11
- [Python 3.10+](https://www.python.org/downloads/)
- [Ollama](https://ollama.com/download) installed and running
- 8GB RAM minimum
- Internet connection for GitHub search and web fetch features (the AI itself runs offline)

---

## Installation

**1. Clone the repository**
```bash
git clone https://github.com/RoadPilotAI/Coding-Assistant.git
cd Coding-Assistant
```

**2. Create a virtual environment and install dependencies**
```bash
python -m venv venv
venv\Scripts\activate
pip install requests beautifulsoup4
```

**3. Pull the AI model**
```bash
ollama pull qwen2.5-coder:3b
```

**4. Create your config file**

Create a file called `config.json` in the project folder:
```json
{
    "github_token": "your_github_token_here",
    "github_username": "your_github_username",
    "model": "qwen2.5-coder:3b",
    "ollama_url": "http://localhost:11434/api/chat"
}
```

To get a GitHub token: github.com → Settings → Developer Settings → Personal Access Tokens → Generate New Token. Check the **repo** scope.

**5. Launch**
```bash
python assistant.py
```

Or double-click the `launch-assistant.bat` file for a one-click start.

---

## Commands

| Command | What It Does |
|---|---|
| Just type | Chat with the assistant |
| `fetch https://...` | Pull any webpage into context |
| `github fetch https://...` | Pull a specific GitHub file into context |
| `github search <query>` | Search GitHub for relevant code |
| `load <filename>` | Load one of your project files into context |
| `save <filename>` | Save the last code response to a file |
| `clear` | Reset the conversation |
| `help` | Show command list |
| `quit` | Exit |

---

## Example Session

```
You: write a function that monitors a folder for new files
Assistant: Here's a clean file watcher using the watchdog library...

You: github search python csv parser
Searching GitHub for: python csv parser
Found: jdunck/python-unicodecsv
Assistant: Here's what that code does, and here's a cleaner version for your project...

You: save csv_parser.py
Saved to csv_parser.py

You: fetch https://docs.python.org/3/library/csv.html
Fetching: https://docs.python.org/3/library/csv.html
Assistant: I've read the Python CSV docs. Here's how to improve the parser...
```

---

## Hardware Guide

| RAM | Recommended Model | Notes |
|---|---|---|
| 8GB | `qwen2.5-coder:3b` | Fast, capable, fits comfortably |
| 16GB | `qwen2.5-coder:7b` | Better reasoning, still local |
| 32GB+ | `qwen2.5-coder:14b` | Near cloud-quality, fully private |

The assistant works on CPU-only machines. A dedicated GPU will significantly speed up responses but is not required.

---

## Privacy

`config.json` is listed in `.gitignore` and will never be committed to GitHub. Your GitHub token and any code you write stays on your machine. The AI model runs locally — your prompts are never sent to Anthropic, OpenAI, or any other service.

---

## Contributing

This project is intentionally kept simple — one Python file, minimal dependencies, no frameworks. Contributions that stay true to that philosophy are welcome.

- Fork the repo
- Create a feature branch
- Submit a pull request with a clear description of what you added and why

---

## Roadmap

- [ ] Auto-installer batch file for one-click setup
- [ ] Smarter GitHub search with quality filtering
- [ ] Conversation history logging
- [ ] Multi-file project context
- [ ] Support for more operating systems (Mac, Linux)

---

## License

MIT License — free to use, modify, and distribute.

---

*Built with [Ollama](https://ollama.com) and [qwen2.5-coder](https://ollama.com/library/qwen2.5-coder). Inspired by the idea that powerful AI tools should run on the computer in front of you, not in a building you'll never visit.*
