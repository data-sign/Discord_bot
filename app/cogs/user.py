from discord import app_commands, Interaction
from discord.ext import commands

from app.repositories.user_profiles import get_user_profile



class UserCog(commands.Cog, name="User"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="내프로필", description="유저 프로필을 조회합니다.")
    async def view_profile(self, interaction: Interaction):

        user_id = interaction.user.id
        profile = await get_user_profile(user_id)

        if not profile:
            await interaction.response.send_message(
                f"🥲 유저 프로필을 찾을 수 없습니다. 관리자에게 문의해주세요.", ephemeral=True
            )
            return
        
        await interaction.response.send_message(
            f"👤 프로필\n"
            f"🎯 월간 목표: {profile.get('monthly_goal', '없음')}\n"
            f"🎯 주간 목표: {profile.get('weekly_goal', '없음')}\n"
            f"🎯 루틴: {profile.get('routine', '없음')}", ephemeral=True)       


async def setup(bot: commands.Bot):
    await bot.add_cog(UserCog(bot))


