import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

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

# API配置
BILIBILI_API = {
    'base_url': 'https://api.bilibili.com',
    'login_base': 'https://passport.bilibili.com',
    'user_agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# 媒体服务器端口
MEDIA_SERVER_PORT = 8765