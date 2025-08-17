import discord
from discord import app_commands, Interaction, ui
from discord.ext import commands
from app.log import logger

from app.repositories.user_profiles import get_user_profile, upsert_user_profile


class MonthlyGoalSetModal(ui.Modal, title="🎯 월간 목표 설정"):
    # 월간 목표 입력용 Modal
    def __init__(self, monthly_goal: str = ""):
        super().__init__()
        self.monthly_goal_input: ui.TextInput = ui.TextInput(
            label="🔥  이번 달 이루고 싶은 목표는 무엇인가요?",
            style=discord.TextStyle.paragraph,
            default=monthly_goal,
            required=True,
            placeholder="이번 달에 달성하고 싶은 목표를 입력해주세요."
        )
        self.add_item(self.monthly_goal_input)

    async def on_submit(self, interaction: Interaction):
        try:
            await upsert_user_profile(interaction.user.id, monthly_goal=self.monthly_goal_input.value)
            await interaction.response.send_message(
                f"🎯 월간 목표가 설정되었습니다.", ephemeral=True
            )
        except Exception as e:
            logger.error(f"Error in monthly goal set modal submit: {e}")
            await interaction.response.send_message(
                f"❌ 월간 목표 설정에 실패했습니다. 관리자에게 문의해주세요.", ephemeral=True
            )


class WeeklyGoalSetModal(ui.Modal, title="🎯 주간 목표 설정"):
    # 주간 목표 입력용 Modal
    def __init__(self, weekly_goal: str = ""):
        super().__init__()
        self.weekly_goal_input: ui.TextInput = ui.TextInput(
            label="🔥  이번 주 이루고 싶은 목표는 무엇인가요?",
            style=discord.TextStyle.paragraph,
            default=weekly_goal,
            required=True,
            placeholder="이번 주에 달성하고 싶은 목표를 입력해주세요."
        )
        self.add_item(self.weekly_goal_input)
        
    async def on_submit(self, interaction: Interaction):
        try:
            await upsert_user_profile(interaction.user.id, weekly_goal=self.weekly_goal_input.value)
            await interaction.response.send_message(
                f"🎯 주간 목표가 설정되었습니다.", ephemeral=True
            )
        except Exception as e:
            logger.error(f"Error in weekly goal set modal submit: {e}")
            await interaction.response.send_message(
                f"❌ 주간 목표 설정에 실패했습니다. 관리자에게 문의해주세요.", ephemeral=True
            )


class RoutineSetModal(ui.Modal, title="🎯 루틴 설정"):
    # 루틴 입력용 Modal
    def __init__(self, routine: str = ""):
        super().__init__()
        self.routine_input: ui.TextInput = ui.TextInput(
            label="📌  매일 실천하고 싶은 나만의 특별한 루틴은 무엇인가요?",
            style=discord.TextStyle.paragraph,
            default=routine,
            required=True,
            placeholder="매일 실천하고 싶은 루틴을 입력해주세요."
        )
        self.add_item(self.routine_input)
        
    async def on_submit(self, interaction: Interaction):
        try:
            await upsert_user_profile(interaction.user.id, routine=self.routine_input.value)
            await interaction.response.send_message(
                f"🎯 루틴이 설정되었습니다.", ephemeral=True
            )
        except Exception as e:
            logger.error(f"Error in routine set modal submit: {e}")
            await interaction.response.send_message(
                f"❌ 루틴 설정에 실패했습니다. 관리자에게 문의해주세요.", ephemeral=True
            )


# 줄바꿈을 처리하는 함수
def format_goal_text(text: str) -> str:
    if not text or text == '없음':
        return text
    # 줄바꿈을 들여쓰기로 변환
    return text.replace('\n-', '-')


class UserCog(commands.Cog, name="User"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="내프로필조회", description="유저 프로필을 조회합니다.")
    async def view_profile(self, interaction: Interaction):

        user_id = interaction.user.id
        profile = await get_user_profile(user_id)

        if not profile:
            await interaction.response.send_message(
                f"🥲 유저 프로필을 찾을 수 없습니다. 관리자에게 문의해주세요.", ephemeral=True
            )
            return
        
        await interaction.response.send_message(
            f"👤 {interaction.user.display_name}님의 프로필\n\n"
            f"🎯 월간 목표\n\t{profile.get('monthly_goal', '없음')}\n\n"
            f"🎯 주간 목표\n\t{profile.get('weekly_goal', '없음')}\n\n"
            f"🎯 루틴\n\t{profile.get('routine', '없음')}", 
            ephemeral=True
        )       

    @app_commands.command(name="월간목표설정", description="월간 목표를 설정합니다.")
    async def set_monthly_goal(self, interaction: Interaction):
        try:
            await interaction.response.send_modal(MonthlyGoalSetModal())
        except Exception as e:
            logger.error(f"Error in set_monthly_goal command: {e}")
            await interaction.response.send_message(
                f"❌ 월간 목표 설정 모달을 열 수 없습니다. 관리자에게 문의해주세요.", 
                ephemeral=True
            )

    @app_commands.command(name="주간목표설정", description="주간 목표를 설정합니다.")
    async def set_weekly_goal(self, interaction: Interaction):
        try:
            await interaction.response.send_modal(WeeklyGoalSetModal())
        except Exception as e:
            logger.error(f"Error in set_weekly_goal command: {e}")
            await interaction.response.send_message(
                f"❌ 주간 목표 설정 모달을 열 수 없습니다. 관리자에게 문의해주세요.", 
                ephemeral=True
            )

    @app_commands.command(name="루틴설정", description="루틴을 설정합니다.")
    async def set_routine(self, interaction: Interaction):
        try:
            await interaction.response.send_modal(RoutineSetModal())
        except Exception as e:
            logger.error(f"Error in set_routine command: {e}")
            await interaction.response.send_message(
                f"❌ 루틴 설정 모달을 열 수 없습니다. 관리자에게 문의해주세요.", 
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(UserCog(bot))


