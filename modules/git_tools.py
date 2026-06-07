import subprocess

def git_commit(message, project_dir):
    """Run git add, commit, and push from inside Max."""
    print(f"\nRunning git add...")
    try:
        result = subprocess.run(
            ["git", "add", "."],
            cwd=project_dir,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"git add failed: {result.stderr.strip()}")
            return

        print(f"Committing: {message}")
        result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=project_dir,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            if "nothing to commit" in result.stdout:
                print("Nothing to commit — no changes detected.")
            else:
                print(f"git commit failed: {result.stderr.strip()}")
            return

        print("Pushing to GitHub...")
        result = subprocess.run(
            ["git", "push"],
            cwd=project_dir,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"git push failed: {result.stderr.strip()}")
            print("Tip: Check your token has 'repo' scope and your internet connection.")
            return

        print(f"Done. Pushed to GitHub: '{message}'")

    except FileNotFoundError:
        print("Error: git not found. Make sure Git is installed and on your PATH.")
    except Exception as e:
        print(f"Git error: {e}")

def git_status(project_dir):
    """Show current git status."""
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=project_dir,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"git status failed: {result.stderr.strip()}")
            return
        if result.stdout.strip():
            print("\n--- Uncommitted changes ---")
            print(result.stdout)
        else:
            print("\nNothing to commit. Working tree is clean.")
    except Exception as e:
        print(f"Git error: {e}")
