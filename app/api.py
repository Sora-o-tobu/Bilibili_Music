import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.services import AuthService, BilibiliService, DownloadService, MusicService
from backend.models.video import Video
from core.config import DOWNLOAD_DIR
import os

class Api:
    def __init__(self):
        self.auth_service = AuthService()
        self.bilibili_service = BilibiliService(self.auth_service)
        self.download_service = DownloadService(self.auth_service)
        self.music_service = MusicService()

    def ensure_login(self, _=None):
        """检查并确保用户已登录"""
        user_info = self.auth_service.check_login_status()
        if user_info:
            return {'status': 'ok', 'message': f'已登录用户: {user_info["uname"]}'}
        
        qrcode_data = self.auth_service.get_login_qrcode()
        if not qrcode_data:
            return {'status': 'error', 'message': '获取登录二维码失败'}

        # 启动一个线程来轮询登录状态
        # 注意：在实际应用中，这里应该有更好的方式来处理异步和线程间通信
        # 但对于pywebview的简单场景，我们可以直接返回二维码
        return {
            'status': 'qrcode',
            'message': '请扫描二维码登录',
            'qrcode': qrcode_data['qrcode_base64'],
            'qrcode_key': qrcode_data['qrcode_key']
        }

    def poll_login_status(self, qrcode_key):
        """轮询检查登录状态"""
        if not qrcode_key:
            return {'status': 'error', 'message': '无效的qrcode_key'}
        
        # 后端直接返回字典，前端直接透传
        return self.auth_service.poll_login_status(qrcode_key)

    def get_favorites(self, force_refresh=False):
        """获取收藏夹，带缓存和强制刷新"""
        favorites = self.bilibili_service.get_favorites(force_refresh)
        if favorites is not None:
            return {'status': 'ok', 'favorites': favorites}
        else:
            return {'status': 'error', 'message': '获取收藏夹失败'}

    def load_video_info(self, url):
        """加载视频信息"""
        if not url:
            return {'status': 'error', 'message': 'URL不能为空'}
        
        video = self.bilibili_service.load_video_info(url)
        if video:
            return {'status': 'ok', 'video': video.to_dict()}
        else:
            return {'status': 'error', 'message': '获取视频信息失败'}

    def download_audio(self, video_dict=None):
        """根据视频信息字典下载音频"""
        if not video_dict:
            return {'status': 'error', 'message': '无效的视频信息'}
            
        video = Video.from_dict(video_dict)
        music = self.download_service.download_audio(video)
        if music:
            return {'status': 'ok', 'message': f'音频已保存到 {music.file_path}', 'music': music.to_dict()}
        else:
            return {'status': 'error', 'message': '下载失败，请查看控制台日志'}

    def get_music_library(self, _=None):
        """获取音乐库中的所有音乐信息"""
        music_list = self.music_service.get_all_music()
        
        # 为每个音乐对象添加 cover_url
        for music in music_list:
            music.cover_url = self.get_media_url(music.cover_path)
            
        return [music.to_dict_with_cover_url() for music in music_list]

    def get_media_url(self, file_path):
        """将本地媒体文件路径转换为可访问的Flask URL"""
        if not file_path:
            return None
        
        from pathlib import Path
        file_path = Path(file_path)
        # 只获取文件名，因为服务器知道根目录
        file_name = file_path.name
        
        # 返回指向 Flask 路由的 URL
        return f"http://localhost:8765/media/{file_name}"

    def refresh_music_library(self, _=None):
        """刷新音乐库"""
        self.music_service.scan_download_folder()
        return self.get_music_library()
    
    def download_audio_wrap(self, bv_id):
        video = self.bilibili_service.load_video_info(bv_id)
        if not video:
            return None
        return self.download_service.download_audio(video)
    
    # 音乐库相关方法
    def get_music_list(self):
        """获取音乐列表"""
        music_list = self.music_service.get_all_music()
        return [music.to_dict() for music in music_list]
    
    def search_music(self, keyword):
        """搜索音乐"""
        if not keyword:
            return self.get_music_list()
        music_list = self.music_service.search_music(keyword)
        return [music.to_dict() for music in music_list]
    
    def delete_music(self, file_path):
        """删除音乐文件"""
        return self.music_service.delete_music_file(file_path)
    
    def get_music_statistics(self):
        """获取音乐库统计信息"""
        return self.music_service.get_statistics()
    
    def refresh_music_library(self):
        """刷新音乐库（扫描新文件）"""
        new_files = self.music_service.scan_download_folder()
        return len(new_files)  # 返回新发现的文件数量
    
    def get_audio_file_url(self, file_path):
        """获取音频文件的可访问URL"""
        import os
        import urllib.parse
        from core.config import DOWNLOAD_DIR
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return None
            
        try:
            # 获取相对于下载目录的路径
            download_dir = Path(DOWNLOAD_DIR)
            file_path_obj = Path(file_path)
            
            # 如果文件在下载目录中，使用本地服务器
            if download_dir in file_path_obj.parents or download_dir == file_path_obj.parent:
                relative_path = file_path_obj.name
                # 使用本地HTTP服务器的URL
                encoded_path = urllib.parse.quote(relative_path)
                return f"http://localhost:8765/media/{encoded_path}"
            else:
                # 如果文件不在下载目录中，尝试file协议
                abs_path = os.path.abspath(file_path)
                url_path = urllib.parse.quote(abs_path.replace('\\', '/'))
                return f"file:///{url_path}"
                
        except Exception as e:
            print(f"获取音频URL失败: {e}")
            return None
    
    def copy_audio_to_temp(self, file_path):
        """将音频文件复制到临时目录并返回新路径"""
        import tempfile
        import shutil
        import os
        from pathlib import Path
        
        try:
            if not os.path.exists(file_path):
                return None
                
            # 创建临时目录
            temp_dir = tempfile.gettempdir()
            temp_music_dir = os.path.join(temp_dir, 'bilibili_music')
            os.makedirs(temp_music_dir, exist_ok=True)
            
            # 获取文件名
            file_name = Path(file_path).name
            temp_file_path = os.path.join(temp_music_dir, file_name)
            
            # 复制文件
            shutil.copy2(file_path, temp_file_path)
            
            return temp_file_path
        except Exception as e:
            print(f"复制文件到临时目录失败: {e}")
            return None
