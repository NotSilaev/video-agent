from pathlib import Path

from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    dev_mode: bool = True

    # Video
    video_cost: int = 1
    max_order_video_count: int = 20
    video_platforms: list = [
        {'title': 'YouTube Shorts', 'short_title': 'shorts'},
        {'title': 'Instagram Reels', 'short_title': 'reels'},
        {'title': 'TikTok', 'short_title': 'tiktok'}
    ]

    # Telegram bot
    telegram_bot_token: str
    admin_list: list

    # Database (PostgreSQL)
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str

    # Cache (Redis)
    cache_host: str
    cache_port: int
    cache_db: int
    cache_max_connections: int

    class Config:
        env_file = Path(__file__).parent / '.env'

settings = Settings()
