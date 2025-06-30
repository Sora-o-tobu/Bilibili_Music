# File: video.py
from core import wbi

class Video:
    """视频类，包含视频的基本信息和下载功能"""
    def __init__(self, avid=None, bvid=None, cid=None, title=None):
        self.avid = avid
        self.bvid = bvid
        self.cid = cid
        self.title = title

    def __str__(self):
        return f"Video(AV号: {self.avid}, BV号: {self.bvid}, CID: {self.cid}, 标题: {self.title})"
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'avid': self.avid,
            'bvid': self.bvid,
            'cid': self.cid,
            'title': self.title
        }
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建Video对象"""
        return cls(
            avid=data.get('avid'),
            bvid=data.get('bvid'),
            cid=data.get('cid'),
            title=data.get('title')
        )

    def download_audio(self, session, filename):
        """下载视频音频，目前仅用 dash 视频格式"""
        if not self.cid or (not self.avid and not self.bvid):
            print("视频信息不完整，无法下载音频")
            return False
        
        download_url = "https://api.bilibili.com/x/player/wbi/playurl"
        img_key, sub_key = wbi.getWbiKeys()
        params = wbi.encWbi(
            params={
                'aid': self.avid,
                'bvid': self.bvid,
                'cid': self.cid,
                'fnval': 16,  # 请求 dash 视频流
            },
            img_key=img_key,
            sub_key=sub_key
        )
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
            "Referer": "https://www.bilibili.com/"
        }
        
        try:
            res = session.get(download_url, params=params, headers=headers)
            if res.status_code == 200:
                data = res.json()
                if data.get('code') == 0:
                    video_data = data['data']
                    audio_url = video_data['dash']['audio'][0]['baseUrl']
                    
                    # 下载音频文件
                    audio_res = session.get(audio_url, headers=headers)
                    if audio_res.status_code == 200:
                        with open(filename, 'wb') as f:
                            f.write(audio_res.content)
                        print(f"音频已下载到 {filename}")
                        return True
                    else:
                        print("音频下载失败")
                else:
                    print(f"获取视频信息失败: {data.get('message', 'Unknown error')}")
            else:
                print("请求失败，状态码:", res.status_code)
        except Exception as e:
            print(f"下载音频时发生错误: {e}")
        return False