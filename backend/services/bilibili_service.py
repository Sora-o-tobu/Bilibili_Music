import requests
from core.config import BILIBILI_API
from core import wbi
from backend.models.video import Video

class BilibiliService:
    """B站服务类"""
    
    def __init__(self, auth_service):
        self.auth_service = auth_service
        self.session = auth_service.session
    
    def load_video_info(self, bvid):
        """加载视频信息"""
        video_info_url = f"{BILIBILI_API['base_url']}/x/web-interface/view"
        params = {'bvid': bvid}
        headers = {
            "User-Agent": BILIBILI_API['user_agent'],
            "Referer": "https://www.bilibili.com/"
        }
        
        try:
            res = self.session.get(video_info_url, params=params, headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                code = data.get('code')
                
                if code == 0:
                    video_data = data['data']
                    video = Video(
                        avid=video_data.get('aid'),
                        bvid=video_data.get('bvid'),
                        cid=video_data.get('cid'),
                        title=video_data.get('title')
                    )
                    print(f"视频信息加载成功: {video.title} (AV号: {video.avid}, BV号: {video.bvid}, CID: {video.cid})")
                    return video
                else:
                    error_messages = {
                        -400: "视频请求错误",
                        -403: "视频权限不足",
                        -404: "视频不存在或已被删除",
                        62002: "稿件不可见",
                        63004: "稿件审核中",
                        62012: "稿件仅up主自己可见"
                    }
                    error_msg = error_messages.get(code, f"未知错误: {code}")
                    print(error_msg)
                    return None
            else:
                print(f"请求失败，状态码: {res.status_code}")
                return None
        except Exception as e:
            print(f"加载视频信息时发生错误: {e}")
            return None