import os
import json
import requests
from pathlib import Path
from core.config import DOWNLOAD_DIR, BILIBILI_API
from core import wbi
from backend.models.music import Music

class DownloadService:
    def __init__(self, auth_service):
        self.auth_service = auth_service
        self.session = auth_service.session
    
    def download_cover_image(self, pic_url, output_dir, filename_base):
        """下载封面图片"""
        if not pic_url:
            return None
            
        try:
            headers = {
                "User-Agent": BILIBILI_API['user_agent'],
                "Referer": "https://www.bilibili.com/"
            }
            
            response = self.session.get(pic_url, headers=headers, timeout=30)
            if response.status_code == 200:
                # 获取图片扩展名
                content_type = response.headers.get('content-type', '')
                if 'jpeg' in content_type or 'jpg' in content_type:
                    ext = '.jpg'
                elif 'png' in content_type:
                    ext = '.png'
                elif 'webp' in content_type:
                    ext = '.webp'
                else:
                    ext = '.jpg'  # 默认
                
                cover_filename = f"{filename_base}_cover{ext}"
                cover_path = Path(output_dir) / cover_filename
                
                with open(cover_path, 'wb') as f:
                    f.write(response.content)
                
                print(f"封面已下载到 {cover_path}")
                return str(cover_path)
            else:
                print(f"封面下载失败，状态码: {response.status_code}")
                return None
        except Exception as e:
            print(f"下载封面时发生错误: {e}")
            return None
    
    def create_music_info_file(self, music, output_dir):
        """创建音乐信息JSON文件"""
        try:
            info_filename = f"{music.file_path.stem}_info.json"
            info_path = Path(output_dir) / info_filename
            
            with open(info_path, 'w', encoding='utf-8') as f:
                json.dump(music.to_dict(), f, ensure_ascii=False, indent=2)
            
            print(f"音乐信息已保存到 {info_path}")
            return str(info_path)
        except Exception as e:
            print(f"保存音乐信息失败: {e}")
            return None
    def download_audio(self, video, filename=None, output_dir=None):
        """下载视频音频，并生成json和本地封面"""
        if not video.cid or (not video.avid and not video.bvid):
            print("视频信息不完整，无法下载音频")
            return None
        
        if output_dir is None:
            output_dir = DOWNLOAD_DIR
        
        if filename is None:
            # 清理文件名中的非法字符
            safe_title = video.title.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
            filename = f"{safe_title}.mp3"
        
        output_path = Path(output_dir) / filename
        filename_base = output_path.stem  # 用于生成封面和信息文件名
        
        download_url = f"{BILIBILI_API['base_url']}/x/player/wbi/playurl"
        
        try:
            img_key, sub_key = wbi.getWbiKeys()
            params = wbi.encWbi(
                params={
                    'aid': video.avid,
                    'bvid': video.bvid,
                    'cid': video.cid,
                    'fnval': 16,  # 请求 dash 视频流
                },
                img_key=img_key,
                sub_key=sub_key
            )
            
            headers = {
                "User-Agent": BILIBILI_API['user_agent'],
                "Referer": "https://www.bilibili.com/"
            }
            
            res = self.session.get(download_url, params=params, headers=headers, timeout=30)
            if res.status_code == 200:
                data = res.json()
                if data.get('code') == 0:
                    video_data = data['data']
                    audio_url = video_data['dash']['audio'][0]['baseUrl']
                    
                    # 下载音频文件
                    audio_res = self.session.get(audio_url, headers=headers, timeout=60)
                    if audio_res.status_code == 200:
                        # 确保输出目录存在
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        with open(output_path, 'wb') as f:
                            f.write(audio_res.content)
                        print(f"音频已下载到 {output_path}")
                        
                        # 下载封面图片
                        cover_path = None
                        if video.pic:
                            cover_path = self.download_cover_image(video.pic, output_dir, filename_base)
                        
                        # 创建音乐对象
                        music = Music(
                            file_path=str(output_path),
                            title=video.title,
                            album=video.title, # Use title as a fallback for album
                            bv_id=video.bvid,
                            pic=video.pic,
                            cover_path=cover_path
                        )
                        
                        # 生成json
                        info_filename = f"{output_path.stem}.json"
                        info_path = Path(output_dir) / info_filename
                        with open(info_path, 'w', encoding='utf-8') as f:
                            json.dump(music.to_dict(), f, ensure_ascii=False, indent=2)
                        
                        print(f"音乐信息已保存到 {info_path}")
                        return music
                    else:
                        print(f"音频下载失败，状态码: {audio_res.status_code}")
                        return None
                else:
                    error_msg = data.get('message', '未知错误')
                    print(f"获取下载链接失败: {error_msg}")
                    return None
            else:
                print(f"请求失败，状态码: {res.status_code}")
                return None
        except Exception as e:
            print(f"下载音频时发生错误: {e}")
            return None