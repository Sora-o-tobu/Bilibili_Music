"""
Backend services for Bilibili application.

This package contains various services for handling authentication,
video information retrieval, download functionality, and music library management.
"""

from .auth import AuthService
from .bilibili_service import BilibiliService
from .download import DownloadService
from .music import MusicService

__all__ = [
    'AuthService',
    'BilibiliService', 
    'DownloadService',
    'MusicService'
]