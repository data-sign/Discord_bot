import os
import sys
import aiohttp
import asyncio
import discord
from aiohttp import web
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

from app.config import ADMIN_CHANNEL_ID, CHANNEL_ID, DISCORD_TOKEN, GUILD_ID, logger




## 1. Discord Bot 정의
intents = discord.Intents.default()
intents.message_content = True  # message.content 읽기 위해 필요
intents.guilds = True
intents.messages = True

# 봇 클라이언트 생성
bot = commands.Bot(command_prefix="!", intents=intents)
setattr(bot, "channel_id", CHANNEL_ID)
setattr(bot, "guild_id", GUILD_ID)


async def ping_self_loop():
    await bot.wait_until_ready()
    url = os.environ.get("KOYEB_URL", "").strip()

    if not url:
        logger.warning("❌ KOYEB_URL 환경변수가 비어 있습니다.")
        return

    while not bot.is_closed():
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as res:
                    logger.info(f"✅ Self-ping 성공: {res.status} (URL: {url})")
        except Exception as e:
            logger.warning(f"❌ Self-ping 실패: {type(e).__name__}: {e} (URL: {url})")

        await asyncio.sleep(300)  # 5분 간격


@bot.event
async def on_ready():
    logger.info(f"🤖 Logged in as {bot.user}")
    logger.info(f"Connected to {len(bot.guilds)} guilds")
    try:
        if GUILD_ID:
            # 길드 동기화
            guild_ref = discord.Object(id=GUILD_ID)

            # 전역 슬래시 명령을 길드에 복사
            # commands.Cog를 사용하면서 명령어가 전역으로 사용됨
            # 명령어를 길드(디스코드 서버)에 복사해야 표시됨
            bot.tree.copy_global_to(guild=guild_ref)
            synced = await bot.tree.sync(guild=guild_ref)

            logger.info(f"길드 동기화 완료: {len(synced)}개")
            logger.info(f"등록된 커맨드: {[cmd.name for cmd in bot.tree.get_commands(guild=guild_ref)]}")

            # 준비 완료 메시지 전송
            channel = bot.get_channel(ADMIN_CHANNEL_ID)
            guild_obj = bot.get_guild(GUILD_ID)
            guild_name = guild_obj.name if guild_obj else str(GUILD_ID)
            await channel.send(f"🤖 봇이 준비되었습니다! 길드: {guild_name} {bot.user.name} 봇 준비 완료")
        else:
            # 전역 동기화
            synced = await bot.tree.sync()
            logger.info(f"전역 동기화 완료: {len(synced)}개")
            logger.info(f"등록된 커맨드: {[cmd.name for cmd in bot.tree.get_commands()]}")
    except Exception as e:
        logger.error(f"슬래시 커맨드 동기화 실패: {e}")

# 디스코드봇 에러 핸들러
@bot.event
async def on_error(event, *args, **kwargs):
    logger.error(f"Discord bot error in {event}: {args}")


## 2. aiohttp 헬스체크 서버 정의
async def health_check(request):
    logger.info("Health check requested")
    return web.Response(text="OK", status=200)

async def start_web_server():
    app = web.Application()
    app.router.add_get('/health', health_check)
    app.router.add_get('/', health_check)  # 루트 경로도 추가
    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, '0.0.0.0', 8000)
    await site.start()
    logger.info(f"🌐 Health check server running on port 8000")

## 3. Discord bot + aiohttp 병렬 실행
async def main():
    logger.info("Starting Discord bot and web server...")
    try:
        # 확장 로드 (도메인 별로 추가)
        await bot.load_extension("app.cogs.scrum")
        
        # aiohttp 웹서버와 디스코드 봇을 동시에 실행
        await asyncio.gather(
            start_web_server(),
            bot.start(DISCORD_TOKEN),
            ping_self_loop(),
            return_exceptions=True
        )
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    try: 
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)