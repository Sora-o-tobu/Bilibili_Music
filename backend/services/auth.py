import requests
import time
import json
import os
import qrcode
import base64
from io import BytesIO
from pathlib import Path
from core.config import DEFAULT_SESSION_FILE, DEFAULT_QRCODE_FILE, BILIBILI_API

class AuthService:
    def __init__(self, session_file=None):
        self.session = requests.Session()
        self.session_file = session_file or DEFAULT_SESSION_FILE
        self.qrcode_file = DEFAULT_QRCODE_FILE
        self.load_session()

    def load_session(self):
        """从文件加载session信息"""
        if os.path.exists(self.session_file):
            try:
                with open(self.session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                # sessions 过七天需要重新登录
                if time.time() - session_data.get('timestamp', 0) > 7 * 24 * 3600:
                    print("Session已过期，需要重新登录")
                    return False
                
                # 恢复cookies
                for cookie in session_data.get('cookies', []):
                    self.session.cookies.set(**cookie)
                
                print("Session loaded from file")
                return True
            except Exception as e:
                print(f"Failed to load session: {e}")
        return False
    
    def save_session(self):
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
            return True
        except Exception as e:
            print(f"Failed to save session: {e}")
            return False
    
    def check_login_status(self):
        """通过nav接口检查登录状态，成功则返回用户信息，否则返回None"""
        try:
            check_url = f"{BILIBILI_API['base_url']}/x/web-interface/nav"
            headers = {
                "User-Agent": BILIBILI_API['user_agent'],
                "Referer": "https://www.bilibili.com/"
            }
            
            res = self.session.get(check_url, headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                if data.get('code') == 0 and data.get('data', {}).get('isLogin'):
                    user_info = data['data']
                    print(f"已登录用户: {user_info.get('uname', 'Unknown')}")
                    return user_info
            
            print("Session已失效，需要重新登录")
            return None
        except Exception as e:
            print(f"检查登录状态失败: {e}")
            return None
        
    def get_login_qrcode(self):
        """获取登录二维码及key"""
        try:
            # 1. 申请二维码
            apply_url = f"{BILIBILI_API['login_base']}/x/passport-login/web/qrcode/generate"
            headers = {"User-Agent": BILIBILI_API['user_agent']}
            res = self.session.get(apply_url, headers=headers, timeout=10)
            res.raise_for_status()
            data = res.json()
            if data['code'] != 0:
                raise Exception(data.get('message', '申请二维码失败'))
            
            qrcode_key = data["data"]["qrcode_key"]
            url = data["data"]["url"]

            # 2. 生成二维码图片 (Base64)
            qr_img = qrcode.make(url)
            buffered = BytesIO()
            qr_img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')

            return {
                "qrcode_key": qrcode_key,
                "qrcode_base64": img_str
            }
        except Exception as e:
            print(f"获取登录二维码时发生错误: {e}")
            return None

    def poll_login_status(self, qrcode_key):
        """轮询二维码登录状态"""
        try:
            poll_url = f"{BILIBILI_API['login_base']}/x/passport-login/web/qrcode/poll"
            headers = {"User-Agent": BILIBILI_API['user_agent']}
            params = {"qrcode_key": qrcode_key}
            
            res = self.session.get(poll_url, params=params, headers=headers, timeout=10)
            res.raise_for_status()
            data = res.json()['data']

            code = data['code']
            message = data['message']
            
            # 登录成功, 保存cookies
            if code == 0:
                self.save_session()
                return {"status": "ok", "message": "登录成功"}
            # 二维码失效
            elif code == 86038:
                return {"status": "expired", "message": message}
            # 已扫码未确认
            elif code == 86090:
                return {"status": "scanned", "message": message}
            # 未扫描
            else: # 86101
                return {"status": "waiting", "message": message}
        except Exception as e:
            print(f"轮询登录状态失败: {e}")
            return {"status": "error", "message": "轮询异常"}

    def login_with_qrcode(self, max_attempts=3):
        """使用二维码登录"""
        attempts = 0
        
        while attempts < max_attempts:
            try:
                qrcode_key, url = self.apply_qrcode()
                if not self.generate_qrcode(url):
                    return False
                
                print("Please scan the QR code to login...")
                timeout_count = 0
                max_timeout = 120  # 2分钟超时
                
                while timeout_count < max_timeout:
                    status, message = self.scan_login(qrcode_key)
                    
                    if status == 0:  # 未扫描
                        print(".", end="", flush=True)
                    elif status == 1:  # 二维码失效
                        print(f"\n{message}. Attempting to generate new QR code...")
                        break
                    elif status == 3:  # 扫描成功，等待确认
                        print(f"\n{message}")
                    elif status == 4:  # 登录成功
                        print(f"\n{message}")
                        return True
                    elif status == -1:  # 保存失败
                        print(f"\n{message}")
                        return False
                    
                    time.sleep(1)
                    timeout_count += 1
                
                if timeout_count >= max_timeout:
                    print("\n登录超时，重新尝试...")
                
            except Exception as e:
                print(f"\nLogin attempt {attempts + 1} failed: {e}")
            
            attempts += 1
            if attempts < max_attempts:
                print(f"Retrying... ({attempts + 1}/{max_attempts})")
                time.sleep(2)
        
        print("登录失败，已达到最大尝试次数")
        return False

    def ensure_login(self):
        """确保登录状态(主要用于命令行环境)"""
        # 首先检查当前session是否有效
        if self.check_login_status():
            return True
        
        print("需要重新登录...")
        # 此处省略命令行下的二维码登录逻辑，因为UI版本有自己的实现
        return False

    def logout(self):
        """登出"""
        try:
            # 清除cookies
            self.session.cookies.clear()
            
            # 删除session文件
            if os.path.exists(self.session_file):
                os.remove(self.session_file)
                print("Session file deleted")
            
            # 删除二维码文件
            if os.path.exists(self.qrcode_file):
                os.remove(self.qrcode_file)
                print("QR code file deleted")
            
            print("已登出")
            return True
        except Exception as e:
            print(f"登出失败: {e}")
            return False