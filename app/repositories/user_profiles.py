from datetime import datetime, timezone
from app.database.supabase import supabase


async def upsert_user_profile(
    user_id: str,
    monthly_goal: str | None = None,
    weekly_goal: str | None = None,
    routine: str | None = None,
) -> dict:
    """새로운 유저 프로필을 생성 또는 업데이트 합니다."""
    try:
        data = {
            "user_id": str(user_id),
            "monthly_goal": monthly_goal,
            "weekly_goal": weekly_goal,
            "routine": routine,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        
        result = await supabase.table("user_profiles").upsert(data, on_conflict="user_id").maybe_single().execute()
        return result.data if result else {}
    
    except Exception as e:
        raise Exception(f"유저 프로필 생성 또는 업데이트 중 오류 발생: {str(e)}")

async def get_user_profile(user_id: int) -> dict | None:
    """유저 프로필을 조회합니다."""
    try:
        result = await supabase.table("user_profiles").select("*").filter("user_id", "eq", str(user_id)).maybe_single().execute()
        return result.data if result else None
    except Exception as e:
        raise Exception(f"유저 프로필 조회 중 오류 발생: {str(e)}")