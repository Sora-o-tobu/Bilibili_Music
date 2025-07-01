"""
音乐文件模型
"""
import os
import json
from pathlib import Path
from datetime import datetime

try:
    import mutagen
    from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC
    HAS_MUTAGEN = True
except ImportError:
    HAS_MUTAGEN = False
    print("Warning: mutagen not installed. Audio metadata reading will be disabled.")

class Music:
    """本地音乐文件类"""
    
    def __init__(self, file_path, title=None, artist=None, album=None, duration=None, 
                 bv_id=None, download_time=None, pic=None, cover_path=None):
        self.file_path = Path(file_path)
        self.title = title or self.file_path.stem
        self.artist = artist or "Unknown Artist"
        self.album = album or "Unknown Album"
        self.duration = duration or 0
        self.bv_id = bv_id
        self.download_time = download_time or datetime.now().isoformat()
        self.pic = pic
        self.cover_path = cover_path
        self.file_size = self.get_file_size()
        
    def get_file_size(self):
        """获取文件大小（字节）"""
        try:
            return self.file_path.stat().st_size if self.file_path.exists() else 0
        except:
            return 0
    
    def get_file_size_readable(self):
        """获取可读的文件大小"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def get_metadata(self):
        """从文件中读取元数据"""
        if not HAS_MUTAGEN:
            return
            
        try:
            if self.file_path.exists() and self.file_path.suffix.lower() == '.mp3':
                audio_file = mutagen.File(self.file_path)
                if audio_file:
                    self.duration = audio_file.info.length if hasattr(audio_file, 'info') else 0
                    
                    # 尝试读取ID3标签
                    if hasattr(audio_file, 'tags') and audio_file.tags:
                        tags = audio_file.tags
                        self.title = str(tags.get('TIT2', [self.title])[0]) if 'TIT2' in tags else self.title
                        self.artist = str(tags.get('TPE1', [self.artist])[0]) if 'TPE1' in tags else self.artist
                        self.album = str(tags.get('TALB', [self.album])[0]) if 'TALB' in tags else self.album
        except Exception as e:
            print(f"读取音频元数据失败: {e}")
    
    def format_duration(self):
        """格式化播放时长"""
        if self.duration:
            minutes = int(self.duration // 60)
            seconds = int(self.duration % 60)
            return f"{minutes:02d}:{seconds:02d}"
        return "00:00"
    
    def to_dict(self):
        """只导出指定字段"""
        return {
            'file_path': str(self.file_path),
            'title': self.title,
            'artist': self.artist,
            'album': self.album,
            'duration': self.duration,
            'bv_id': self.bv_id,
            'download_time': self.download_time,
            'pic': self.pic,
            'cover_path': self.cover_path
        }
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建Music对象"""
        return cls(
            file_path=data.get('file_path'),
            title=data.get('title'),
            artist=data.get('artist'),
            album=data.get('album'),
            duration=data.get('duration'),
            bv_id=data.get('bv_id'),
            download_time=data.get('download_time'),
            pic=data.get('pic'),
            cover_path=data.get('cover_path')
        )
    
    @classmethod
    def from_video(cls, video, file_path, cover_path=None):
        """从Video对象和下载结果创建Music对象"""
        return cls(
            file_path=file_path,
            title=video.title,
            artist="Bilibili",
            album="Bilibili",
            duration=video.duration,
            bv_id=video.bvid,
            download_time=datetime.now().isoformat(),
            pic=video.pic,
            cover_path=cover_path
        )
    
    def __str__(self):
        return f"Music(title: {self.title}, artist: {self.artist}, duration: {self.format_duration()})"
