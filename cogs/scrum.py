import os
import logging
import discord
from discord import app_commands, ui, Interaction
from discord.ext import commands

logger = logging.getLogger(__name__)


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


class ScrumModal(ui.Modal, title="✍️ 인증 내용 작성"):
    def __init__(self, channel_id: int, yesterday: str, today: str):
        super().__init__()
        self.channel_id = channel_id

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
                f"😉 하고 싶은 말\n{self.comment_input.value}"
            )

            await check_channel.send(
                f"<@{interaction.user.id}>님의 인증입니다\n\n{content}"
            )
            await interaction.response.send_message(
                "✅ 인증이 등록되었습니다!", ephemeral=True
            )

        except Exception as e:
            logger.error(f"Error in scrum modal submit: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ 인증 등록 중 오류가 발생했습니다.", ephemeral=True
                )


class ScrumEditModal(ui.Modal, title="✏️ 인증 내용 수정"):
    def __init__(self, message_to_edit: discord.Message, yesterday: str, today: str, comment: str):
        super().__init__()
        self.message_to_edit = message_to_edit

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
            await interaction.response.send_message(
                "✅ 인증이 수정되었습니다!", ephemeral=True
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

            modal = ScrumModal(channel_id=channel_id, yesterday=today_section or "(없음)", today="")
            await interaction.response.send_modal(modal)
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


