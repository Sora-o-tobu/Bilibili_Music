import requests
import time
import json
import os
from pathlib import Path
from core.config import DEFAULT_SESSION_FILE, DEFAULT_QRCODE_FILE, BILIBILI_API

class AuthService:
    """认证服务类"""
    
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
                
                # 检查session是否过期(7天)
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
            return True
        except Exception as e:
            print(f"Failed to save session: {e}")
            return False
    
    def check_login_status(self):
        """检查当前登录状态"""
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
                    return True
            
            print("Session已失效，需要重新登录")
            return False
        except Exception as e:
            print(f"检查登录状态失败: {e}")
            return False
        
    def apply_qrcode(self):
        """申请二维码"""
        apply_url = f"{BILIBILI_API['login_base']}/x/passport-login/web/qrcode/generate"
        headers = {
            "User-Agent": BILIBILI_API['user_agent'],
            "Referer": f"{BILIBILI_API['login_base']}/login"
        }
        
        res = self.session.get(apply_url, headers=headers, timeout=10)
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
            return True
        except ImportError:
            print("qrcode package not installed. Install it with: pip install qrcode[pil]")
            print(f"Please scan this URL manually: {url}")
            return False

    def scan_login(self, qrcode_key):
        """扫描登录检查"""
        scan_url = f"{BILIBILI_API['login_base']}/x/passport-login/web/qrcode/poll"
        headers = {
            "User-Agent": BILIBILI_API['user_agent'],
            "Referer": f"{BILIBILI_API['login_base']}/login"
        }
        
        res = self.session.get(scan_url, params={"qrcode_key": qrcode_key}, headers=headers, timeout=10)
        if res.status_code != 200:
            raise Exception("Failed to scan QR code")
        
        data = res.json()
        if data['code'] != 0:
            raise Exception("Error in QR code scanning")
        
        status_code = data["data"]["code"]
        
        if status_code == 0:  # 扫码登录成功
            # 获取cookies并保存到session
            for cookie in res.cookies:
                self.session.cookies.set(cookie.name, cookie.value, domain=cookie.domain)
            
            # 保存session到文件
            if self.save_session():
                return 4, "Login successful"
            else:
                return -1, "Failed to save session"
        elif status_code == 86038:  # 二维码失效
            return 1, "QR code expired"
        elif status_code == 86090:  # 已扫码未确认
            return 3, "Scanned, waiting for confirmation"
        elif status_code == 86101:  # 未扫描
            return 0, "Not scanned"
        else:
            return 0, "Not scanned"

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
        """确保登录状态"""
        # 首先检查当前session是否有效
        if self.check_login_status():
            return True
        
        print("需要重新登录...")
        return self.login_with_qrcode()

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