import os
import discord
from discord import app_commands, ui, Interaction
from discord.ext import commands
import asyncio
from aiohttp import web

## 0. 환경변수 설정
# 환경변수에서 디스코드 토큰 가져오기
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

if not TOKEN or not CHANNEL_ID:
    raise ValueError("DISCORD_TOKEN과 CHANNEL_ID 환경변수를 모두 설정하세요.")

CHANNEL_ID = int(CHANNEL_ID)

## 1. Discord Bot 정의
intents = discord.Intents.default()
intents.message_content = True  # message.content 읽기 위해 필요
intents.guilds = True
intents.messages = True

# 봇 클라이언트 생성
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"🤖 Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"슬래시 커맨드 {len(synced)}개 동기화 완료")
    except Exception as e:
        print(e)

## 2. aiohttp 헬스체크 서버 정의
async def health_check(request):
    return web.Response(text="OK", status=200)

async def start_web_server():
    app = web.Application()
    app.router.add_get('/health', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8000)
    await site.start()
    print("🌐 Health check server running on port 8000")

## 3. 인증 모달 생성
# 섹션 추출 함수: 시작 이모지~다음 섹션 시작 전까지 텍스트 추출
def extract_section(text, start_heading, end_heading):
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
        # 인증 채널로 전송
        auth_channel = interaction.client.get_channel(CHANNEL_ID)

        content = (
            f"🧐 어제 무엇을 했나요?\n{self.yesterday_input.value}\n\n"
            f"🫣 오늘 무엇을 할 계획인가요?\n{self.today_input.value}\n\n"
            f"😉 하고 싶은 말\n{self.comment_input.value}"
        )

        await auth_channel.send(f"<@{interaction.user.id}>님의 인증입니다\n\n{content}")
        await interaction.response.send_message("✅ 인증이 등록되었습니다!", ephemeral=True)

# 슬래시 명령으로 Modal 실행
@bot.tree.command(name="인증복사", description="이전 인증에서 '오늘 계획'을 복사해 새 인증을 작성합니다.")
async def copy_scrum(interaction: Interaction):
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

## 4. Discord bot + aiohttp 병렬 실행
async def main():
    # aiohttp 웹서버와 디스코드 봇을 동시에 실행
    await asyncio.gather(
        start_web_server(),
        bot.start(TOKEN)  # 또는 client.run()은 안됨 (blocking)
    )

if __name__ == "__main__":
    asyncio.run(main())
