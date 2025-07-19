import os
import discord
from discord import app_commands, ui, Interaction
from discord.ext import commands


# 환경변수에서 디스코드 토큰 가져오기
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True  # message.content 읽기 위해 필요
intents.guilds = True
intents.messages = True

# 봇 클라이언트 생성
bot = commands.Bot(command_prefix="!", intents=intents)


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

class 인증Modal(ui.Modal, title="✍️ 인증 내용 작성"):

    def __init__(self, yesterday: str, today: str):
        super().__init__()
        self.yesterday = yesterday
        self.today = today

        self.어제 = ui.TextInput(label="🧐 어제 무엇을 했나요?", style=discord.TextStyle.paragraph, default=yesterday)
        self.오늘 = ui.TextInput(label="🫣 오늘 무엇을 할 계획인가요?", style=discord.TextStyle.paragraph, default="")
        self.하고싶은말 = ui.TextInput(label="😉 하고 싶은 말", style=discord.TextStyle.paragraph, default="", required=False)

        self.add_item(self.어제)
        self.add_item(self.오늘)
        self.add_item(self.하고싶은말)

    async def on_submit(self, interaction: Interaction):
        # 인증 채널로 전송
        인증채널 = interaction.client.get_channel(CHANNEL_ID)

        content = (
            f"🧐 어제 무엇을 했나요?\n{self.어제.value}\n\n"
            f"🫣 오늘 무엇을 할 계획인가요?\n{self.오늘.value}\n\n"
            f"😉 하고 싶은 말\n{self.하고싶은말.value}"
        )

        await 인증채널.send(f"<@{interaction.user.id}>님의 인증입니다\n\n{content}")
        await interaction.response.send_message("✅ 인증이 등록되었습니다!", ephemeral=True)

# 슬래시 명령으로 Modal 실행
@bot.tree.command(name="인증복사", description="이전 인증에서 '오늘 계획'을 복사해 새 인증을 작성합니다.")
async def 인증복사(interaction: Interaction):
    # 최근 메시지에서 오늘계획 추출
    channel = bot.get_channel(CHANNEL_ID)
    user_id = interaction.user.id
    latest_msg = None

    async for msg in channel.history(limit=200):
        if msg.author.bot and f"<@{user_id}>" in msg.content:
            latest_msg = msg
            break

    today_section = extract_section(latest_msg.content, "🫣 오늘 무엇을 할 계획인가요?", "😉 하고 싶은 말") if latest_msg else ""

    modal = 인증Modal(yesterday=today_section or "(없음)", today="")
    await interaction.response.send_modal(modal)


bot.run(TOKEN)
