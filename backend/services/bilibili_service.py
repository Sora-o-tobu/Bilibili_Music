# File: backend/services/bilibili_service.py
import requests
import re
from urllib.parse import urlparse, parse_qs
from core.config import BILIBILI_API, FAVORITES_CACHE_FILE
from core import wbi
from backend.models.video import Video
import json
import time
import random

class BilibiliService:
    def __init__(self, auth_service):
        self.auth_service = auth_service
        self.session = auth_service.session

    def _send_request(self, url, params=None, needs_wbi=False):
        """统一发送请求，自动处理WBI签名"""
        headers = {
            "User-Agent": BILIBILI_API['user_agent'],
            "Referer": "https://www.bilibili.com/"
        }
        
        final_params = params.copy() if params else {}
        
        if needs_wbi:
            img_key, sub_key = wbi.getWbiKeys()
            final_params = wbi.encWbi(params=final_params, img_key=img_key, sub_key=sub_key)

        try:
            res = self.session.get(url, params=final_params, headers=headers, timeout=10)
            res.raise_for_status()
            data = res.json()
            if data.get('code', 0) != 0:
                print(f"API Error: {data.get('message', 'Unknown error')}, URL: {url}")
                return None
            return data.get('data')
        except requests.exceptions.RequestException as e:
            print(f"请求失败: {e}, URL: {url}")
            return None
        except json.JSONDecodeError:
            print(f"JSON解码失败, URL: {url}")
            return None

    def extract_bvid_from_url(self, url):
        """从Bilibili视频URL中提取BV号"""
        match = re.search(r'/(BV[a-zA-Z0-9]+)', url)
        if match:
            return match.group(1)
        return None

    def load_video_info(self, video_url):
        """加载视频信息"""
        bvid = self.extract_bvid_from_url(video_url) or video_url
        api_url = f"{BILIBILI_API['base_url']}/x/web-interface/view"
        params = {'bvid': bvid}
        
        video_data = self._send_request(api_url, params, needs_wbi=True)
        
        if video_data:
            video = Video(
                avid=video_data.get('aid'),
                bvid=video_data.get('bvid'),
                cid=video_data.get('cid'),
                title=video_data.get('title'),
                pic=video_data.get('pic'),
                duration=video_data.get('duration')
            )
            print(f"视频信息加载成功: {video.title}")
            return video
        return None

    def get_favorites(self, force_refresh=False):
        """获取收藏夹信息，优先从缓存读取"""
        if not force_refresh and FAVORITES_CACHE_FILE.exists():
            try:
                with open(FAVORITES_CACHE_FILE, 'r', encoding='utf-8') as f:
                    print("从缓存加载收藏夹...")
                    return json.load(f)
            except Exception as e:
                print(f"从缓存加载收藏夹失败: {e}")
        
        print("从API获取收藏夹...")
        return self._fetch_and_cache_favorites()

    def _fetch_favorite_videos_paginated(self, media_id, folder_title):
        """分页获取单个收藏夹的所有视频"""
        videos = []
        page_num = 1
        while True:
            fav_videos_url = BILIBILI_API['get_fav_videos_detail']
            params = {'media_id': media_id, 'pn': page_num, 'ps': 20, 'platform': 'web'}
            
            data = self._send_request(fav_videos_url, params, needs_wbi=True)
            
            if not data:
                print(f"获取收藏夹 {folder_title} 内容失败。")
                break

            videos_info = data.get('medias', [])
            if not videos_info:
                break  # No more videos

            for video_info in videos_info:
                # Skip invalid/deleted videos which may lack essential data
                if video_info.get('is_invalid') or not video_info.get('bvid'):
                    print(f"Skipping invalid or incomplete video entry: {video_info.get('title')}")
                    continue
                
                ugc_info = video_info.get('ugc')
                cid = ugc_info.get('first_cid') if ugc_info else None

                video = Video(
                    avid=video_info.get('id'),
                    bvid=video_info.get('bvid'),
                    cid=cid,
                    title=video_info.get('title'),
                    pic=video_info.get('cover'),
                    duration=video_info.get('duration')
                )
                videos.append(video.to_dict())
            
            if not data.get('has_more'):
                break  # Last page
            
            page_num += 1
            time.sleep(random.uniform(0.1, 0.2))  # Be nice to Bilibili API
        return videos

    def _fetch_and_cache_favorites(self):
        """从Bilibili API获取所有收藏夹内容并缓存"""
        user_info = self.auth_service.check_login_status()
        if not user_info or 'mid' not in user_info:
            print("用户未登录或无法获取用户信息")
            return []

        up_mid = user_info['mid']
        fav_list_url = BILIBILI_API['get_fav']
        
        data = self._send_request(fav_list_url, params={'up_mid': up_mid})
        if not data:
            return []

        favorites_data = []
        fav_folders = data.get('list', [])
        if not fav_folders:
            print("没有找到任何收藏夹")
            return []

        for folder in fav_folders:
            media_id = folder.get('id')
            folder_title = folder.get('title')
            media_count = folder.get('media_count', 0)

            if not media_id:
                continue

            folder_data = {
                "id": media_id,
                "title": folder_title,
                "media_count": media_count,
                "videos": []
            }

            if media_count > 0:
                folder_data["videos"] = self._fetch_favorite_videos_paginated(media_id, folder_title)
            
            favorites_data.append(folder_data)
        
        try:
            FAVORITES_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(FAVORITES_CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(favorites_data, f, ensure_ascii=False, indent=4)
            print("收藏夹数据已成功缓存。")
        except Exception as e:
            print(f"缓存收藏夹失败: {e}")

        return favorites_data