from datetime import datetime, timezone
from app.database.supabase import supabase


async def create_scrum_entry(
    user_id: str,
    yesterday_work: str,
    today_plan: str,
    comment: str,
    message_id: str,
    channel_id: str,
) -> dict:
    """새로운 스크럼 인증을 생성합니다."""
    try:
        data = {
            "user_id": str(user_id),
            "yesterday_work": yesterday_work,
            "today_plan": today_plan,
            "comment": comment,
            "message_id": str(message_id),
            "channel_id": str(channel_id),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        
        result = await supabase.table("scrum_entries").insert(data).execute()
        return result.data[0] if result.data else {}
    
    except Exception as e:
        raise Exception(f"스크럼 인증 생성 중 오류 발생: {str(e)}")


async def update_scrum_entry(
    message_id: str,
    yesterday_work: str,
    today_plan: str,
    comment: str,
) -> dict:
    """기존 스크럼 인증을 수정합니다."""
    try:
        data = {
            "yesterday_work": yesterday_work,
            "today_plan": today_plan,
            "comment": comment,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "is_edited": True,
        }
        
        result = await (
            supabase.table("scrum_entries")
            .update(data)
            .eq("message_id", str(message_id))
            .execute()
        )
        return result.data[0] if result.data else {}
    
    except Exception as e:
        raise Exception(f"스크럼 인증 수정 중 오류 발생: {str(e)}")

# TODO: 추후 적용하기
# async def get_latest_scrum_entry(user_id: str, channel_id: str) -> dict | None:
#     """사용자의 최근 스크럼 인증을 조회합니다."""
#     try:
#         result = await (
#             supabase.table("scrum_entries")
#             .select("*")
#             .eq("user_id", str(user_id))
#             .eq("channel_id", str(channel_id))
#             .order("created_at", desc=True)
#             .limit(1)
#             .execute()
#         )
#         return result.data[0] if result.data else None
    
#     except Exception as e:
#         raise Exception(f"스크럼 인증 조회 중 오류 발생: {str(e)}")