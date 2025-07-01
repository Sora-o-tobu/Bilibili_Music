"""
音乐库管理服务
"""
import os
import json
from pathlib import Path
from datetime import datetime
from core.config import DOWNLOAD_DIR
from backend.models.music import Music

class MusicService:
    """音乐库管理服务"""
    
    def __init__(self):
        self.download_dir = Path(DOWNLOAD_DIR)
        self.music_db_file = self.download_dir.parent / "music_library.json"
        self.music_library = self.load_music_library()
    
    def load_music_library(self):
        """从JSON文件加载音乐库"""
        if self.music_db_file.exists():
            try:
                with open(self.music_db_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return {path: Music.from_dict(info) for path, info in data.items()}
            except Exception as e:
                print(f"加载音乐库失败: {e}")
        return {}
    
    def save_music_library(self):
        """保存音乐库到JSON文件"""
        try:
            data = {path: music.to_dict() for path, music in self.music_library.items()}
            with open(self.music_db_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存音乐库失败: {e}")
    
    def scan_download_folder(self):
        """扫描下载文件夹，只加载json元数据文件"""
        if not self.download_dir.exists():
            return []
        new_files = []
        for file_path in self.download_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() == '.json':
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        music = Music.from_dict(data)
                        self.music_library[str(music.file_path)] = music
                        new_files.append(music)
                except Exception as e:
                    print(f"读取音乐json失败: {e}")
        self.save_music_library()
        return new_files
    
    def get_all_music(self):
        """获取所有音乐列表"""
        # 先扫描新文件
        self.scan_download_folder()
        
        # 检查文件是否仍然存在
        existing_music = []
        for music in self.music_library.values():
            if music.file_path.exists():
                existing_music.append(music)
        
        # 按下载时间排序（最新的在前）
        existing_music.sort(key=lambda x: x.download_time, reverse=True)
        return existing_music
    
    def get_music_by_path(self, file_path):
        """根据文件路径获取音乐信息"""
        return self.music_library.get(str(file_path))
    
    def add_music(self, file_path, bv_id=None, title=None):
        """添加音乐到库中"""
        music = Music(file_path, bv_id=bv_id, title=title)
        music.get_metadata()
        self.music_library[str(file_path)] = music
        self.save_music_library()
        return music
    
    def remove_music(self, file_path):
        """从库中移除音乐"""
        file_key = str(file_path)
        if file_key in self.music_library:
            del self.music_library[file_key]
            self.save_music_library()
            return True
        return False
    
    def delete_music_file(self, file_path):
        """删除音乐文件及其记录"""
        file_path = Path(file_path)
        try:
            if file_path.exists():
                file_path.unlink()  # 删除文件
            self.remove_music(str(file_path))  # 从库中移除
            return True
        except Exception as e:
            print(f"删除文件失败: {e}")
            return False
    
    def search_music(self, keyword):
        """搜索音乐"""
        keyword = keyword.lower()
        results = []
        
        for music in self.get_all_music():
            if (keyword in music.title.lower() or 
                keyword in music.artist.lower() or 
                keyword in music.album.lower() or
                keyword in music.file_path.name.lower()):
                results.append(music)
        
        return results
    
    def get_statistics(self):
        """获取音乐库统计信息"""
        all_music = self.get_all_music()
        total_count = len(all_music)
        total_size = sum(music.file_size for music in all_music)
        total_duration = sum(music.duration for music in all_music if music.duration)
        
        # 格式化总大小
        size = total_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                total_size_readable = f"{size:.1f} {unit}"
                break
            size /= 1024.0
        else:
            total_size_readable = f"{size:.1f} TB"
        
        # 格式化总时长
        hours = int(total_duration // 3600)
        minutes = int((total_duration % 3600) // 60)
        total_duration_readable = f"{hours}小时{minutes}分钟"
        
        return {
            'total_count': total_count,
            'total_size': total_size,
            'total_size_readable': total_size_readable,
            'total_duration': total_duration,
            'total_duration_readable': total_duration_readable
        }
