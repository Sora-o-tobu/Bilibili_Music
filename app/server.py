# File: app/media_server.py
from flask import Flask, send_from_directory
import os

app = Flask(__name__)

@app.route('/media/<path:filename>')
def serve_media(filename):
    # 从环境变量或配置中获取下载目录
    download_dir = os.environ.get('DOWNLOAD_DIR')
    if not download_dir:
        # 如果环境变量未设置，提供一个默认的回退路径
        # 注意：这需要与主应用中的路径保持一致
        current_dir = os.path.dirname(os.path.abspath(__file__))
        download_dir = os.path.join(current_dir, '..', 'data', 'downloads')
        
    return send_from_directory(download_dir, filename)

def start_media_server(directory, port):
    """启动 Flask 媒体服务器"""
    # 将下载目录存储在环境变量中，以便 Flask 路由可以访问它
    # 修复：将 Path 对象转换为字符串
    os.environ['DOWNLOAD_DIR'] = str(directory)
    print(f"Flask 媒体服务器启动在 http://localhost:{port}")
    print(f"服务目录: {directory}")
    app.run(host='0.0.0.0', port=port, debug=False)
