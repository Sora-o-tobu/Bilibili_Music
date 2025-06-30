import os
from pathlib import Path
from core.config import DOWNLOAD_DIR, BILIBILI_API
from core import wbi

class DownloadService:
    """下载服务类"""
    
    def __init__(self, auth_service):
        self.auth_service = auth_service
        self.session = auth_service.session
    
    def download_audio(self, video, filename=None, output_dir=None):
        """下载视频音频"""
        if not video.cid or (not video.avid and not video.bvid):
            print("视频信息不完整，无法下载音频")
            return False
        
        # 设置输出路径
        if output_dir is None:
            output_dir = DOWNLOAD_DIR
        
        if filename is None:
            # 清理文件名中的非法字符
            safe_title = "".join(c for c in video.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"{safe_title}.mp3"
        
        output_path = Path(output_dir) / filename
        
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
                    
                    # 检查是否有音频流
                    if 'dash' not in video_data or 'audio' not in video_data['dash']:
                        print("该视频没有可用的音频流")
                        return False
                    
                    audio_list = video_data['dash']['audio']
                    if not audio_list:
                        print("没有找到音频流")
                        return False
                    
                    # 选择第一个音频流
                    audio_url = audio_list[0]['baseUrl']
                    
                    # 下载音频文件
                    print(f"开始下载音频: {filename}")
                    audio_res = self.session.get(audio_url, headers=headers, timeout=60)
                    
                    if audio_res.status_code == 200:
                        # 确保输出目录存在
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        with open(output_path, 'wb') as f:
                            f.write(audio_res.content)
                        
                        print(f"音频已下载到: {output_path}")
                        return str(output_path)
                    else:
                        print(f"音频下载失败，状态码: {audio_res.status_code}")
                        return False
                else:
                    print(f"获取视频播放信息失败: {data.get('message', 'Unknown error')}")
                    return False
            else:
                print(f"请求播放URL失败，状态码: {res.status_code}")
                return False
                
        except Exception as e:
            print(f"下载音频时发生错误: {e}")
            return False