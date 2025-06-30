import requests
import time
import json
import os
from pathlib import Path
from core import wbi

class video:
    """视频类，包含视频的基本信息和下载功能"""
    def __init__(self, avid=None, bvid=None, cid=None, title=None):
        self.avid = avid
        self.bvid = bvid
        self.cid = cid
        self.title = title

    def __str__(self):
        return f"Video(AV号: {self.avid}, BV号: {self.bvid}, CID: {self.cid}, 标题: {self.title})"
    
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

class Bilibili:
    """ TODO
    web 端cookies刷新: https://socialsisteryi.github.io/bilibili-API-collect/docs/login/cookie_refresh.html
    """
    def __init__(self, session_file="bilibili_session.json"):
        self.session = requests.Session()
        self.session_file = session_file
        self.qrcode_file = "bilibili_qrcode.png"
        self.load_session()

    def load_session(self):
        """从文件加载session信息"""
        if os.path.exists(self.session_file):
            try:
                with open(self.session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                # 恢复cookies
                for cookie in session_data.get('cookies', []):
                    self.session.cookies.set(**cookie)
                
                print("Session loaded from file")
                return True
            except Exception as e:
                print(f"Failed to load session: {e}")
        return False
    
    def save_session(self):
        """保存session信息到文件"""
        try:
            cookies_data = []
            for cookie in self.session.cookies:
                cookies_data.append({
                    'name': cookie.name,
                    'value': cookie.value,
                    'domain': cookie.domain,
                    'path': cookie.path,
                    'secure': cookie.secure,
                    'expires': cookie.expires
                })
            
            session_data = {
                'cookies': cookies_data,
                'timestamp': time.time()
            }
            
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            
            print("Session saved to file")
        except Exception as e:
            print(f"Failed to save session: {e}")
    
    def check_login_status(self):
        """检查当前登录状态"""
        try:
            check_url = "https://api.bilibili.com/x/web-interface/nav"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
                "Referer": "https://www.bilibili.com/"
            }
            
            res = self.session.get(check_url, headers=headers)
            if res.status_code == 200:
                data = res.json()
                if data.get('code') == 0 and data.get('data', {}).get('isLogin'):
                    user_info = data['data']
                    print(f"已登录用户: {user_info.get('uname', 'Unknown')}")
                    return True
            
            print("Session已失效，需要重新登录")
            return False
        except Exception as e:
            print(f"检查登录状态失败: {e}")
            return False
        
    def apply_qrcode(self):
        """申请二维码"""
        apply_url = "https://passport.bilibili.com/x/passport-login/web/qrcode/generate"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
            "Referer": "https://passport.bilibili.com/login"
        }
        res = self.session.get(apply_url, headers=headers)
        if res.status_code != 200:
            raise Exception("Failed to apply QR code")
        data = res.json()
        if data['code'] != 0:
            raise Exception("Error in QR code application")
        return data["data"]["qrcode_key"], data["data"]["url"]

    def generate_qrcode(self, url):
        """生成二维码"""
        try:
            import qrcode
            img = qrcode.make(url)
            img.save(self.qrcode_file)
            print(f"QR Code generated and saved as {self.qrcode_file}")
            print("Scan the QR code with the Bilibili app to log in.")
        except ImportError:
            print("qrcode package not installed. Install it with: pip install qrcode[pil]")
            print(f"Please scan this URL manually: {url}")

    def scan_login(self, qrcode_key):
        """扫描登录检查"""
        scan_url = "https://passport.bilibili.com/x/passport-login/web/qrcode/poll"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
            "Referer": "https://passport.bilibili.com/login"
        }
        res = self.session.get(scan_url, params={"qrcode_key": qrcode_key}, headers=headers)
        if res.status_code != 200:
            raise Exception("Failed to scan QR code")
        
        data = res.json()
        if data['code'] != 0:
            raise Exception("Error in QR code scanning")
        
        match data["data"]["code"]:
            case 0:      # 扫码登录成功
                # 获取cookies并保存到session
                cookies = res.cookies
                for cookie in cookies:
                    self.session.cookies.set(cookie.name, cookie.value, domain=cookie.domain)
                
                # 保存session到文件
                self.save_session()
                return 4, "Login successful"
            case 86038:  # 二维码失效
                return 1, "QR code expired"
            case 86090:  # 已扫码未确认
                return 3, "Scanned, waiting for confirmation"
            case 86101:  # 未扫描
                return 0, "Not scanned"
            case _:      # 默认未扫描
                return 0, "Not scanned"

    def login_with_qrcode(self):
        """使用二维码登录"""
        try:
            qrcode_key, url = self.apply_qrcode()
            self.generate_qrcode(url)
            
            print("Please scan the QR code to login...")
            while True:
                status, message = self.scan_login(qrcode_key)
                
                match status:
                    case 0:  # 未扫描
                        print(".", end="", flush=True)
                    case 1:  # 二维码失效
                        print(f"\n{message}. Please try again.")
                        return False
                    case 3:  # 扫描成功，等待确认
                        print(f"\n{message}")
                    case 4:  # 登录成功
                        print(f"\n{message}")
                        return True
                
                time.sleep(1)
        except Exception as e:
            print(f"Login failed: {e}")
            return False

    def ensure_login(self):
        """确保登录状态"""
        # 首先检查当前session是否有效
        if self.check_login_status():
            return True
        
        print("需要重新登录...")
        return self.login_with_qrcode()

    def load_video_info(self, bvid):
        video_info_url = "https://api.bilibili.com/x/web-interface/view"
        params = {
            # 'aid' : avid,  # 如果有avid可以使用
            'bvid': bvid
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
            "Referer": "https://www.bilibili.com/"
        }
        try:
            res = self.session.get(video_info_url, params=params, headers=headers)
            if res.status_code == 200:
                data = res.json()
                match data.get('code'):
                    case 0:
                        video_data = data['data']
                        avid = video_data.get('aid')
                        bvid = video_data.get('bvid')
                        cid = video_data.get('cid')
                        title = video_data.get('title')
                        print(f"视频信息加载成功: {title} (AV号: {avid}, BV号: {bvid}, CID: {cid})")
                        return video(avid=avid, bvid=bvid, cid=cid, title=title)
                    case -400:
                        print("视频请求错误")
                    case -403:
                        print("视频权限不足")
                    case -404:
                        print("视频不存在或已被删除")
                    case 62002:
                        print("稿件不可见")
                    case 63004:
                        print("稿件审核中")
                    case 62012:
                        print("稿件仅up主自己可见")
                    case _:
                        print("未知错误")
            else:
                print("请求失败，状态码:", res.status_code)
        except Exception as e:
            print(f"加载视频信息时发生错误: {e}")

    def download_audio(self, avid, bvid, cid, filename):
        download_url = "https://api.bilibili.com/x/player/wbi/playurl"
        # params = {
        #     #'avid': avid,
        #     'bvid': bvid,
        #     'cid': cid,
        #     'fnval': 16, # 请求 dash 视频流
        # }
        img_key, sub_key = wbi.getWbiKeys()
        params = wbi.encWbi(
            params={
                'aid': avid,
                'bvid': bvid,
                'cid': cid,
                'fnval': 16, # 请求 dash 视频流
            },
            img_key=img_key,
            sub_key=sub_key
        )
        # print(params)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
            "Referer": "https://www.bilibili.com/"
        }
        try:
            res = self.session.get(download_url, params=params, headers=headers)
            if res.status_code == 200:
                data = res.json()
                if data.get('code') == 0:
                    video_data = data['data']
                    audio_url = video_data['dash']['audio'][0]['baseUrl']
                    
                    # 下载音频文件
                    audio_res = self.session.get(audio_url, headers=headers)
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


def main():
    login_manager = Bilibili()
    
    if login_manager.ensure_login():
        print("登录成功！")
        new_video = login_manager.load_video_info('BV1BW411j7mh')
        if new_video:
            new_video.download_audio(login_manager.session, new_video.title + '.mp3')
        # login_manager.download_audio(avid, bvid, cid, 'audio.mp3')
    else:
        print("登录失败，请稍后重试。")

if __name__ == "__main__":
    main()