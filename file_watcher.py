from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class FileChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory:
            print(f"File modified: {event.src_path}")

    def on_created(self, event):
        if not event.is_directory:
            print(f"File created: {event.src_path}")

    def on_deleted(self, event):
        if not event.is_directory:
            print(f"File deleted: {event.src_path}")

if __name__ == "__main__":
    # Specify the directory to watch
    path_to_watch = r'C:\path\to\watch'

    # Create an instance of the handler
    handler = FileChangeHandler()

    # Create an observer object and attach it to the handler
    observer = Observer()
    observer.schedule(handler, path=path_to_watch, recursive=True)

    try:
        # Start the observer
        print(f"Watching directory: {path_to_watch}")
        observer.start()
        # Keep the script running to observe changes
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        # Stop the observer when interrupted
        observer.stop()

    # Wait for the observer to finish
    observer.join()
