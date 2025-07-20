import os
import discord
from discord import app_commands, ui, Interaction
from discord.ext import commands
import asyncio
from aiohttp import web
import sys
import logging

# 로깅 설정 (서버 로그에 출력되도록)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

## 0. 환경변수 설정
# 환경변수에서 디스코드 토큰 가져오기
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
GUILD_ID = os.getenv("GUILD_ID")

if not TOKEN or not CHANNEL_ID:
    logger.error("DISCORD_TOKEN과 CHANNEL_ID 환경변수를 모두 설정하세요.")
    raise ValueError("DISCORD_TOKEN과 CHANNEL_ID 환경변수를 모두 설정하세요.")

CHANNEL_ID = int(CHANNEL_ID)
if GUILD_ID:
    GUILD_ID = int(GUILD_ID)

## 1. Discord Bot 정의
intents = discord.Intents.default()
intents.message_content = True  # message.content 읽기 위해 필요
intents.guilds = True
intents.messages = True

# 봇 클라이언트 생성
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    logger.info(f"🤖 Logged in as {bot.user}")
    logger.info(f"Connected to {len(bot.guilds)} guilds")
    try:
        if GUILD_ID:
            guild = discord.Object(id=GUILD_ID)
            synced = await bot.tree.sync(guild=guild)
            logger.info(f"길드 동기화 완료: {len(synced)}개")
            logger.info(f"등록된 커맨드: {[cmd.name for cmd in bot.tree.get_commands()]}")
        else:
            synced = await bot.tree.sync()
            logger.info(f"전역 동기화 완료: {len(synced)}개")
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
    logger.info(f"🌐 Health check server running on port {port}")

## 3. 인증 모달 생성
# 섹션 추출 함수: 시작 이모지~다음 섹션 시작 전까지 텍스트 추출
def extract_section(text, start_heading, end_heading):
    if not text:
        return ""

    lines = text.splitlines()
    is_in_section = False
    collected = []
    for line in lines:
        if line.strip().startswith(start_heading):
            is_in_section = True
            continue
        if is_in_section and line.strip().startswith(end_heading):
            break
        if is_in_section:
            collected.append(line)
    return "\n".join(collected).strip()

class ScrumModal(ui.Modal, title="✍️ 인증 내용 작성"):

    def __init__(self, yesterday: str, today: str):
        super().__init__()
        self.yesterday = yesterday
        self.today = today

        self.yesterday_input = ui.TextInput(label="🧐 어제 무엇을 했나요?", style=discord.TextStyle.paragraph, default=yesterday)
        self.today_input = ui.TextInput(label="🫣 오늘 무엇을 할 계획인가요?", style=discord.TextStyle.paragraph, default="")
        self.comment_input = ui.TextInput(label="😉 하고 싶은 말", style=discord.TextStyle.paragraph, default="", required=False)

        self.add_item(self.yesterday_input)
        self.add_item(self.today_input)
        self.add_item(self.comment_input)

    async def on_submit(self, interaction: Interaction):
        try: 
            # 인증 채널로 전송
            check_channel = interaction.client.get_channel(CHANNEL_ID)
            if not check_channel:
                await interaction.response.send_message("❌ 인증 채널을 찾을 수 없습니다.", ephemeral=True)
                return

            content = (
                f"🧐 어제 무엇을 했나요?\n{self.yesterday_input.value}\n\n"
                f"🫣 오늘 무엇을 할 계획인가요?\n{self.today_input.value}\n\n"
                f"😉 하고 싶은 말\n{self.comment_input.value}"
            )

            await check_channel.send(f"<@{interaction.user.id}>님의 인증입니다\n\n{content}")
            await interaction.response.send_message("✅ 인증이 등록되었습니다!", ephemeral=True)
        
        except Exception as e:
            logger.error(f"Error in scrum modal submit: {e}")
            await interaction.response.send_message("❌ 인증 등록 중 오류가 발생했습니다.", ephemeral=True)

# 슬래시 명령으로 Modal 실행
@bot.tree.command(name="인증복사", description="이전 인증에서 '오늘 계획'을 복사해 새 인증을 작성합니다.")
async def copy_scrum(interaction: Interaction):
    try: 
        # 최근 메시지에서 오늘계획 추출
        channel = bot.get_channel(CHANNEL_ID)
        user_id = interaction.user.id
        latest_msg = None

        async for msg in channel.history(limit=200):
            if msg.author.bot and f"<@{user_id}>" in msg.content:
                latest_msg = msg
                break

        today_section = extract_section(latest_msg.content, "🫣 오늘 무엇을 할 계획인가요?", "😉 하고 싶은 말") if latest_msg else ""

        modal = ScrumModal(yesterday=today_section or "(없음)", today="")
        await interaction.response.send_modal(modal)
    except Exception as e:
        logger.error(f"Error in copy_scrum command: {e}")
        await interaction.response.send_message("❌ 명령어 실행 중 오류가 발생했습니다.", ephemeral=True)

## 4. Discord bot + aiohttp 병렬 실행
async def main():
    logger.info("Starting Discord bot and web server...")
    try:
        # aiohttp 웹서버와 디스코드 봇을 동시에 실행
        await asyncio.gather(
            start_web_server(),
            bot.start(TOKEN),
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