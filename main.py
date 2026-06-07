# main.py

import sys
from modules.github import get_repos, create_issue, update_repo_description
from modules.files import read_file, write_file, list_files_in_directory
from modules.web import fetch_web_page, send_email
from modules.git_tools import clone_repository, commit_changes, push_to_origin
from modules.history import log_command

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <command> [options]")
        return

    command = sys.argv[1]
    options = sys.argv[2:]

    if command == 'get_repos':
        log_command(command)
        get_repos(options)
    elif command == 'create_issue':
        log_command(command)
        create_issue(options)
    elif command == 'update_repo_description':
        log_command(command)
        update_repo_description(options)
    elif command == 'read_file':
        log_command(command)
        read_file(options)
    elif command == 'write_file':
        log_command(command)
        write_file(options)
    elif command == 'list_files_in_directory':
        log_command(command)
        list_files_in_directory(options)
    elif command == 'fetch_web_page':
        log_command(command)
        fetch_web_page(options)
    elif command == 'send_email':
        log_command(command)
        send_email(options)
    elif command == 'clone_repository':
        log_command(command)
        clone_repository(options)
    elif command == 'commit_changes':
        log_command(command)
        commit_changes(options)
    elif command == 'push_to_origin':
        log_command(command)
        push_to_origin(options)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
