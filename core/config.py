import os
from pathlib import Path
import sys

# 判断程序是否被打包
def get_app_path():
    if getattr(sys, 'frozen', False):
        # 如果是打包状态，返回可执行文件所在的目录
        return os.path.dirname(sys.executable)
    else:
        # 如果是源码运行状态，返回项目根目录
        return os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 应用根目录
APP_ROOT = get_app_path()

# 项目根目录
PROJECT_ROOT = Path(APP_ROOT)

# 数据目录
DATA_DIR = PROJECT_ROOT / "data"
SESSION_DIR = DATA_DIR / "sessions"
DOWNLOAD_DIR = DATA_DIR / "downloads"
QRCODE_DIR = DATA_DIR / "qrcodes"

# 确保目录存在
for dir_path in [DATA_DIR, SESSION_DIR, DOWNLOAD_DIR, QRCODE_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# 默认配置
DEFAULT_SESSION_FILE = SESSION_DIR / "bilibili_session.json"
DEFAULT_QRCODE_FILE = QRCODE_DIR / "bilibili_qrcode.png"
FAVORITES_CACHE_FILE = DATA_DIR / "favorites_cache.json"

# API配置
BILIBILI_API = {
    'base_url': 'https://api.bilibili.com',
    'login_base': 'https://passport.bilibili.com',
    'get_fav': 'https://api.bilibili.com/x/v3/fav/folder/created/list-all',
    'get_fav_videos': 'https://api.bilibili.com/x/v3/fav/resource/list',
    'get_fav_videos_detail': 'https://api.bilibili.com/x/v3/fav/resource/list',
    'play_url': 'https://api.bilibili.com/x/player/playurl',
    'subtitle_url': 'https://api.bilibili.com/x/player/v2',
    'user_agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# 媒体服务器端口
MEDIA_SERVER_PORT = 8765