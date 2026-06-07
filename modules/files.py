import os
import re

def load_file(filename, project_dir):
    """Load a file into context. Use 'self' to load assistant.py."""
    if filename.lower() == "self":
        filename = "assistant.py"
    filepath = os.path.join(project_dir, filename)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: File '{filename}' not found in project folder."
    except PermissionError:
        return f"Error: Permission denied reading '{filename}'."
    except Exception as e:
        return f"Error loading file: {e}"

def save_code(filename, last_response, project_dir):
    """Extract largest code block from last response and save to file."""
    pattern = r"```(?:\w+)?\n(.*?)```"
    matches = re.findall(pattern, last_response, re.DOTALL)
    if not matches:
        print("No code blocks found in last response.")
        return
    code = max(matches, key=len)
    filepath = os.path.join(project_dir, filename)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"Saved to {filename}")
    except Exception as e:
        print(f"Error saving file: {e}")

def write_file(filename, last_response, project_dir):
    """Extract code from last response, preview it, and write to file with confirmation."""
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
        filepath = os.path.join(project_dir, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(code)
            print(f"Written to {filename}")
        except Exception as e:
            print(f"Error writing file: {e}")
    else:
        print("Cancelled.")

def edit_file(filename, user_request, project_dir, chat_fn):
    """Load a file, ask Max to modify it, preview the result, write back with confirmation."""
    filepath = os.path.join(project_dir, filename)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            current_content = f.read()
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        return ""
    except Exception as e:
        print(f"Error reading file: {e}")
        return ""

    print(f"\nLoading {filename} and asking Max to edit it...")
    message = (
        f"Here is the current content of {filename}:\n\n"
        f"```\n{current_content}\n```\n\n"
        f"Please make this change: {user_request}\n\n"
        f"Return the complete updated file, not just the changed part."
    )
    response = chat_fn(message)

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
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(updated_code)
            print(f"Updated {filename}")
        except Exception as e:
            print(f"Error writing file: {e}")
    else:
        print("Cancelled.")

    return response

def show_project(project_dir):
    """List all project files with sizes, skipping venv and cache folders."""
    print(f"\n--- Project Files ---")
    skip = {"venv", "__pycache__", ".git"}
    try:
        for item in sorted(os.listdir(project_dir)):
            if item in skip or item.startswith("."):
                continue
            full_path = os.path.join(project_dir, item)
            if os.path.isfile(full_path):
                size = os.path.getsize(full_path)
                print(f"  {item} ({size:,} bytes)")
            elif os.path.isdir(full_path):
                print(f"  {item}/")
                for sub in sorted(os.listdir(full_path)):
                    if sub.startswith("__"):
                        continue
                    sub_path = os.path.join(full_path, sub)
                    if os.path.isfile(sub_path):
                        size = os.path.getsize(sub_path)
                        print(f"    {sub} ({size:,} bytes)")
    except Exception as e:
        print(f"Error listing project: {e}")
    print()
