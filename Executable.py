from flask import Flask
import webbrowser
import threading

app = Flask(__name__)

@app.route("/")
def index():
    return "Offline app running on your local network!"

def open_browser():
    webbrowser.open("http://10.10.21.96:5000/")

if __name__ == "__main__":
    threading.Timer(1, open_browser).start()
    app.run(host="0.0.0.0", port=5000)
 