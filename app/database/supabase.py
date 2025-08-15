from supabase.client import AsyncClient

from app.config import SUPABASE_ANON_KEY, SUPABASE_URL



class SupabaseClient:
    _instance = None

    @classmethod
    def get_instance(cls) -> AsyncClient:
        """싱글톤 패턴으로 Supabase 클라이언트 인스턴스를 반환합니다."""
        if cls._instance is None:
            cls._instance = AsyncClient(
                supabase_url=SUPABASE_URL,
                supabase_key=SUPABASE_ANON_KEY,
            )
        return cls._instance


supabase = SupabaseClient.get_instance()
