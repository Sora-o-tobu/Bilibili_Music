import http.server
import socketserver
import os
from urllib.parse import unquote
import functools
from pathlib import Path

# 音频文件服务器
class MediaFileHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, media_dir=None, **kwargs):
        self.media_dir = media_dir
        # The new directory parameter for SimpleHTTPRequestHandler is available in Python 3.7+
        # For broader compatibility, we handle the path manually.
        super().__init__(*args, **kwargs)

    def do_GET(self):
        # 统一处理 /audio/ 和 /covers/ 路径
        if self.path.startswith(('/audio/', '/covers/')):
            # 移除前缀，获取相对路径
            # e.g., /audio/some/song.mp3 -> some/song.mp3
            relative_path = unquote(self.path.split('/', 2)[-1])
            full_path = os.path.join(self.media_dir, relative_path)

            if os.path.exists(full_path) and os.path.isfile(full_path):
                self.send_response(200)
                
                # 根据文件扩展名确定MIME类型
                mime_type = 'application/octet-stream'
                if full_path.endswith('.mp3'): mime_type = 'audio/mpeg'
                elif full_path.endswith('.m4a'): mime_type = 'audio/mp4'
                elif full_path.endswith('.wav'): mime_type = 'audio/wav'
                elif full_path.endswith('.flac'): mime_type = 'audio/flac'
                elif full_path.endswith('.ogg'): mime_type = 'audio/ogg'
                elif full_path.endswith(('.jpg', '.jpeg')): mime_type = 'image/jpeg'
                elif full_path.endswith('.png'): mime_type = 'image/png'
                elif full_path.endswith('.webp'): mime_type = 'image/webp'
                
                self.send_header('Content-Type', mime_type)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Accept-Ranges', 'bytes')
                
                file_size = os.path.getsize(full_path)
                self.send_header('Content-Length', str(file_size))
                self.end_headers()
                
                with open(full_path, 'rb') as f:
                    self.copyfile(f, self.wfile)
            else:
                self.send_error(404, 'File not found')
        else:
            # 对于其他请求，可以调用父类方法处理，或者直接返回404
            self.send_error(404, 'Not found')


def start_media_server(media_dir, port=8765):
    """启动媒体文件服务器"""
    # 使用 functools.partial 来传递额外的参数给处理器
    handler = functools.partial(MediaFileHandler, media_dir=media_dir)
    
    try:
        # 设置工作目录，以便 SimpleHTTPRequestHandler 可以找到文件
        os.chdir(media_dir)
        with socketserver.TCPServer(("", port), handler) as httpd:
            print(f"媒体服务器启动在端口 {port}，服务目录 {media_dir}")
            httpd.serve_forever()
    except Exception as e:
        print(f"启动媒体服务器失败: {e}")
