import time
import queue
from flask import Flask, render_template, request
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

app = Flask(__name__)

notifications_queue = queue.Queue()


class MyHandler(FileSystemEventHandler):
    def on_modified(self, event):
        file_path = event.src_path
        print(f"File {file_path} has been modified")
        send_notification("modified", file_path)

    def on_created(self, event):
        file_path = event.src_path
        print(f"File {file_path} has been created")
        send_notification("created", file_path)

    def on_deleted(self, event):
        file_path = event.src_path
        print(f"File {file_path} has been deleted")
        send_notification("deleted", file_path)


def send_notification(action, file_path):
    notification = {"action": action, "file_path": file_path}
    notifications_queue.put(notification)


@app.route("/")
def index():
    notifications = []
    while not notifications_queue.empty():
        notifications.append(notifications_queue.get())
    print("Notifications:", notifications)
    return render_template("index.html", notifications=notifications)


@app.route("/notify", methods=["POST"])
def notify():
    try:
        data = request.json
        if data:
            file_path = data.get("file_path")
            if file_path:
                print("Notification received:", file_path)
                notifications_queue.put(file_path)
                return "Notification received"
        return "Invalid notification data", 400
    except Exception as e:
        print("Error:", e)
        return "An error occurred while processing the notification", 500


def start_watchdog():
    path = "./monitor"
    event_handler = MyHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        observer.join()
    except OSError as e:
        if e.errno == 10038:
            print("Ignoring OSError 10038")
        else:
            raise


if __name__ == "__main__":
    import threading

    watchdog_thread = threading.Thread(target=start_watchdog)
    watchdog_thread.start()

    app.run(debug=True, threaded=False)
