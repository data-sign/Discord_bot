import discord
from discord import app_commands, ui, Interaction
from discord.ext import commands
import asyncio

from app.repositories.scrum_entries import create_scrum_entry, update_scrum_entry
from app.repositories.user_profiles import get_user_profile
from app.log import logger


def extract_section(text: str, start_heading: str, end_heading: str) -> str:
    if not text:
        return ""

    lines = text.splitlines()
    is_in_section = False
    collected: list[str] = []
    for line in lines:
        if line.strip().startswith(start_heading):
            is_in_section = True
            continue
        if is_in_section and end_heading and line.strip().startswith(end_heading):
            break
        if is_in_section:
            collected.append(line)
    return "\n".join(collected).strip()

class StartScrumButton(ui.View):
    def __init__(self, channel_id: int, user_id: int, yesterday: str, today: str, has_goals: bool = False):
        super().__init__(timeout=300)  # 5분 타임아웃
        self.channel_id = channel_id
        self.user_id = user_id
        self.yesterday = yesterday
        self.today = today
        self.has_goals = has_goals

    @ui.button(label="인증 작성 시작", style=discord.ButtonStyle.primary, emoji="✍️")
    async def start_scrum(self, interaction: Interaction, button: ui.Button):
        try:
            modal = ScrumModal(
                channel_id=self.channel_id,
                user_id=self.user_id,
                yesterday=self.yesterday,
                today=self.today
            )
            await interaction.response.send_modal(modal)
        except Exception as e:
            logger.error(f"Error in start scrum button: {e}")
            await interaction.response.send_message(
                "❌ 모달을 열 수 없습니다.", ephemeral=True
            )

class ScrumModal(ui.Modal, title="✍️ 인증 내용 작성"):
    def __init__(self, channel_id: int, user_id: int, yesterday: str, today: str):
        super().__init__()
        self.channel_id = channel_id
        self.user_id = user_id


        self.yesterday_input: ui.TextInput = ui.TextInput(
            label="🧐 어제 무엇을 했나요?",
            style=discord.TextStyle.paragraph,
            default=yesterday,
        )
        self.today_input: ui.TextInput = ui.TextInput(
            label="🫣 오늘 무엇을 할 계획인가요?",
            style=discord.TextStyle.paragraph,
            default=today,
        )
        self.comment_input: ui.TextInput = ui.TextInput(
            label="😉 하고 싶은 말 (힘든 점, 좋은 일, 기대하는 모습 등)",
            style=discord.TextStyle.paragraph,
            default="",
        )

        self.add_item(self.yesterday_input)
        self.add_item(self.today_input)
        self.add_item(self.comment_input)

    async def on_submit(self, interaction: Interaction):
        try:

            check_channel = interaction.client.get_channel(self.channel_id)
            if not check_channel:
                await interaction.response.send_message(
                    "❌ 인증 채널을 찾을 수 없습니다.", ephemeral=True
                )
                return
            if not isinstance(check_channel, (discord.TextChannel, discord.Thread)):
                await interaction.response.send_message(
                    "❌ 텍스트 채널에서만 사용할 수 있습니다.", ephemeral=True
                )
                return

            content = (
                f"🧐 어제 무엇을 했나요?\n{self.yesterday_input.value}\n\n"
                f"🫣 오늘 무엇을 할 계획인가요?\n{self.today_input.value}\n\n"
                f"😉 하고 싶은 말\n{self.comment_input.value}\n\n"
            )

            # 디스코드에 메시지 전송
            sent_message = await check_channel.send(
                f"<@{interaction.user.id}>님의 인증입니다\n\n{content}"
            )
            
            # DB에 저장
            try:
                await create_scrum_entry(
                    user_id=str(interaction.user.id),
                    yesterday_work=self.yesterday_input.value,
                    today_plan=self.today_input.value,
                    comment=self.comment_input.value,
                    message_id=str(sent_message.id),
                    channel_id=str(self.channel_id)
                )
                # 모달 응답 보내기
                await interaction.response.send_message(
                    "✅ 인증이 등록되었습니다!", ephemeral=True
                )
            except Exception as e:
                logger.error(f"DB 저장 중 오류 발생: {e}")
                await interaction.followup.send(
                    "⚠️ 데이터베이스 저장 중 오류가 발생했습니다.", ephemeral=True
                )

        except Exception as e:
            logger.error(f"Error in scrum modal submit: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ 인증 등록 중 오류가 발생했습니다.", ephemeral=True
                )


class ScrumEditModal(ui.Modal, title="✏️ 인증 내용 수정"):
    def __init__(self, message_to_edit: discord.Message, yesterday: str, today: str, comment: str, user_id: int):
        super().__init__()
        self.message_to_edit = message_to_edit
        self.user_id = user_id

        self.yesterday_input: ui.TextInput = ui.TextInput(
            label="🧐 어제 무엇을 했나요?",
            style=discord.TextStyle.paragraph,
            default=yesterday,
        )
        self.today_input: ui.TextInput = ui.TextInput(
            label="🫣 오늘 무엇을 할 계획인가요?",
            style=discord.TextStyle.paragraph,
            default=today,
        )
        self.comment_input: ui.TextInput = ui.TextInput(
            label="😉 하고 싶은 말 (힘든 점, 좋은 일, 기대하는 모습 등)",
            style=discord.TextStyle.paragraph,
            default=comment,
        )

        self.add_item(self.yesterday_input)
        self.add_item(self.today_input)
        self.add_item(self.comment_input)

    async def on_submit(self, interaction: Interaction):
        try:
            content = (
                f"🧐 어제 무엇을 했나요?\n{self.yesterday_input.value}\n\n"
                f"🫣 오늘 무엇을 할 계획인가요?\n{self.today_input.value}\n\n"
                f"😉 하고 싶은 말\n{self.comment_input.value}"
            )

            # 기존 메시지 수정
            new_content = f"<@{interaction.user.id}>님의 인증입니다 (수정됨)\n\n{content}"
            await self.message_to_edit.edit(content=new_content)

            # DB 업데이트
            try:
                await update_scrum_entry(
                    message_id=str(self.message_to_edit.id),
                    yesterday_work=self.yesterday_input.value,
                    today_plan=self.today_input.value,
                    comment=self.comment_input.value
                )
                # 모달 응답 보내기
                await interaction.response.send_message(
                    "✅ 인증이 수정되었습니다!", ephemeral=True
                )
            except Exception as e:
                logger.error(f"DB 업데이트 중 오류 발생: {e}")
                await interaction.followup.send(
                    "⚠️ 데이터베이스 업데이트 중 오류가 발생했습니다.", ephemeral=True
                )
            
        except Exception as e:
            logger.error(f"Error in scrum edit modal submit: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ 인증 수정 중 오류가 발생했습니다.", ephemeral=True
                )


class ScrumCog(commands.Cog, name="Scrum"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="인증복사", description="이전 인증에서 '오늘 계획'을 복사해 새 인증을 작성합니다.")
    async def copy_scrum(self, interaction: Interaction):
        try:
            channel_id = getattr(self.bot, "channel_id", None)
            if channel_id is None:
                await interaction.response.send_message(
                    "❌ CHANNEL_ID가 설정되지 않았습니다.", ephemeral=True
                )
                return

            channel = self.bot.get_channel(channel_id)
            user_id = interaction.user.id
            latest_msg: discord.Message | None = None

            if interaction.channel_id != channel_id:
                await interaction.response.send_message(
                    "이 채널에서는 사용할 수 없는 명령어입니다.", ephemeral=True
                )
                return

            if not isinstance(channel, (discord.TextChannel, discord.Thread)):
                await interaction.response.send_message(
                    "❌ 텍스트 채널에서만 사용할 수 있습니다.", ephemeral=True
                )
                return

            async for msg in channel.history(limit=200):
                if msg.author.bot and f"<@{user_id}>" in msg.content:
                    latest_msg = msg
                    break
                elif (
                    msg.author.id == user_id
                    and "🧐 어제 무엇을 했나요?" in msg.content
                ):
                    latest_msg = msg
                    break

            today_section = (
                extract_section(
                    latest_msg.content,
                    "🫣 오늘 무엇을 할 계획인가요?",
                    "😉 하고 싶은 말",
                )
                if latest_msg
                else ""
            )

            # 사용자 프로필 조회 
            user_profile = await get_user_profile(user_id)
            
            # 루틴이 있으면 오늘 계획에 자동으로 설정
            routine = user_profile.get('routine', '') if user_profile else ''
            today_plan = routine if routine else today_section or ""

            # 목표 정보가 있으면 먼저 보여주기
            has_goals = user_profile.get('monthly_goal') ㅋ

            if has_goals:
                # 목표가 있는 경우: 버튼 사용
                view = StartScrumButton(channel_id, user_id, today_section or "(없음)", today_plan, has_goals=True)
                await interaction.response.send_message(
                    f"🎯  {interaction.user.display_name}님의 목표\n\n"
                    f"📅  월간 목표\n{user_profile.get('monthly_goal', '(없음)')}\n\n"
                    f"📅  주간 목표\n{user_profile.get('weekly_goal', '(없음)')}\n\n"
                    "위 목표를 참고하여 인증을 작성해주세요\n", 
                    view=view,
                    ephemeral=True
                )
            else:
                # 목표가 없는 경우: 버튼 비활성화
                # view = StartScrumButton(channel_id, user_id, today_section or "(없음)", today_plan, has_goals=False)
                await interaction.response.send_message(
                    "❌ 월간 목표를 먼저 설정해주세요.\n\n"
                    "목표를 설정하려면 `/월간목표설정` 명령어를 사용해주세요.",
                    # view=view,
                    ephemeral=True
                )
        except Exception as e:
            logger.error(f"Error in copy_scrum command: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ 명령어 실행 중 오류가 발생했습니다.", ephemeral=True
                )

    @app_commands.command(name="인증수정", description="최근 인증 내용을 수정합니다.")
    async def edit_scrum(self, interaction: Interaction):
        try:
            channel_id = getattr(self.bot, "channel_id", None)
            if channel_id is None:
                await interaction.response.send_message(
                    "❌ CHANNEL_ID가 설정되지 않았습니다.", ephemeral=True
                )
                return

            channel = self.bot.get_channel(channel_id)
            user_id = interaction.user.id
            latest_msg: discord.Message | None = None

            if interaction.channel_id != channel_id:
                await interaction.response.send_message(
                    "이 채널에서는 사용할 수 없는 명령어입니다.", ephemeral=True
                )
                return

            if not isinstance(channel, (discord.TextChannel, discord.Thread)):
                await interaction.response.send_message(
                    "❌ 텍스트 채널에서만 사용할 수 있습니다.", ephemeral=True
                )
                return

            # 최근 봇이 보낸 메시지 중 해당 유저 태그가 있는 메시지 찾기
            async for msg in channel.history(limit=200):
                if (
                    msg.author.bot
                    and f"<@{user_id}>" in msg.content
                    and "님의 인증입니다" in msg.content
                ):
                    latest_msg = msg
                    break

            if not latest_msg:
                await interaction.response.send_message(
                    "❌ 수정할 인증 메시지를 찾을 수 없습니다.", ephemeral=True
                )
                return

            yesterday_section = extract_section(
                latest_msg.content,
                "🧐 어제 무엇을 했나요?",
                "🫣 오늘 무엇을 할 계획인가요?",
            )
            today_section = extract_section(
                latest_msg.content,
                "🫣 오늘 무엇을 할 계획인가요?",
                "😉 하고 싶은 말",
            )
            comment_section = extract_section(
                latest_msg.content, "😉 하고 싶은 말", ""
            )

            modal = ScrumEditModal(
                message_to_edit=latest_msg,
                yesterday=yesterday_section or "",
                today=today_section or "",
                comment=comment_section or "",
                user_id=user_id,
            )
            await interaction.response.send_modal(modal)

        except Exception as e:
            logger.error(f"Error in edit_scrum command: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ 명령어 실행 중 오류가 발생했습니다.", ephemeral=True
                )


async def setup(bot: commands.Bot):
    await bot.add_cog(ScrumCog(bot))


