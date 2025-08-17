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
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        if monthly_goal is not None:
            data["monthly_goal"] = monthly_goal
        if weekly_goal is not None:
            data["weekly_goal"] = weekly_goal
        if routine is not None:
            data["routine"] = routine
        
        result = await supabase.table("user_profiles").upsert(data, on_conflict="user_id").execute()
        return result.data[0] if result.data else {}
    
    except Exception as e:
        raise Exception(f"유저 프로필 생성 또는 업데이트 중 오류 발생: {str(e)}")

async def get_user_profile(user_id: int) -> dict | None:
    """유저 프로필을 조회합니다."""
    try:
        result = await supabase.table("user_profiles").select("*").filter("user_id", "eq", str(user_id)).maybe_single().execute()
        return result.data if result else None
    except Exception as e:
        raise Exception(f"유저 프로필 조회 중 오류 발생: {str(e)}")