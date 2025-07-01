from backend.services import AuthService, BilibiliService, DownloadService

def main():
    print("=== Bilibili 音频下载工具 ===")
    
    # 初始化服务
    auth_service = AuthService()
    
    # 确保登录
    if not auth_service.ensure_login():
        print("登录失败，程序退出")
        return
    
    print("登录成功！")
    
    # 初始化其他服务
    bilibili_service = BilibiliService(auth_service)
    download_service = DownloadService(auth_service)
    
    # 测试下载
    bv_id = input("请输入BV号: ").strip()
    if not bv_id:
        # 测试用默认 BV 号
        bv_id = "BV1BW411j7mh"
    
    # 加载视频信息
    video = bilibili_service.load_video_info(bv_id)
    if video:
        print(f"找到视频: {video}")
        
        # 下载音频
        result = download_service.download_audio(video)
        if result:
            print(f"下载成功: {result}")
        else:
            print("下载失败")
    else:
        print("视频信息加载失败")

if __name__ == "__main__":
    main()
