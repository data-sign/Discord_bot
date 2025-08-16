## 0. 환경변수 설정
# Supabase 환경변수
import os

from app.log import logger


SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")

# Discord 환경변수
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", 0))
GUILD_ID = int(os.getenv("GUILD_ID", 0))
ADMIN_CHANNEL_ID = int(os.getenv("ADMIN_CHANNEL_ID", 1396068768798478386)) # 관리자 채널

if not DISCORD_TOKEN or not CHANNEL_ID:
    logger.error("DISCORD_TOKEN과 CHANNEL_ID 환경변수를 모두 설정하세요.")
    raise ValueError("DISCORD_TOKEN과 CHANNEL_ID 환경변수를 모두 설정하세요.")

