import webview
import threading
from app.api import Api
from app.server import start_media_server
from core.config import DOWNLOAD_DIR
import os

def main():
    api = Api()
    html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'frontend', 'dist', 'index.html'))
    window = webview.create_window('Bilibili', html_path, js_api=api, width=1200, height=800)

    def on_loaded():
        print("DOM is loaded, refreshing music library...")
        window.evaluate_js('window.refreshMusicLibrary()')

    window.events.loaded += on_loaded
    
    media_thread = threading.Thread(
        target=start_media_server, 
        args=(DOWNLOAD_DIR, 8765), 
        daemon=True
    )
    media_thread.start()
    
    webview.start()

if __name__ == '__main__':
    main()