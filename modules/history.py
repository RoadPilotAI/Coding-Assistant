import os
import datetime

def save_history(conversation, project_dir):
    """Save the current conversation to a timestamped text file."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"history_{timestamp}.txt"
    filepath = os.path.join(project_dir, filename)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            for message in conversation:
                role = message["role"].upper()
                content = message["content"]
                if role == "SYSTEM":
                    continue
                f.write(f"[{role}]\n{content}\n\n{'='*50}\n\n")
        print(f"Conversation saved to {filename}")
        return filename
    except Exception as e:
        print(f"Error saving history: {e}")
        return None

def list_history(project_dir):
    """List all saved conversation history files."""
    try:
        files = sorted([
            f for f in os.listdir(project_dir)
            if f.startswith("history_") and f.endswith(".txt")
        ], reverse=True)
        if not files:
            print("No history files found.")
            return
        print("\n--- Saved Conversations ---")
        for f in files:
            filepath = os.path.join(project_dir, f)
            size = os.path.getsize(filepath)
            print(f"  {f} ({size:,} bytes)")
        print()
    except Exception as e:
        print(f"Error listing history: {e}")
