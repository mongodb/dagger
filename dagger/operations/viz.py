import threading
import webbrowser
import os
import argh
import dagger.visualization.server

@argh.named("viz")
def main():
    t = threading.Thread(target=dagger.visualizations.server.main)
    t.daemon = True
    t.start()
    url = "127.0.0.1:5000/interactive"
    webbrowser.open(url)
    raw_input("Enter anything to kill server")
