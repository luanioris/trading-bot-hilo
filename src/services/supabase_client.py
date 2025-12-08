from supabase import create_client, Client
from src.config import Config

def get_supabase_client() -> Client:
    url = Config.SUPABASE_URL
    key = Config.SUPABASE_KEY
    
    if not url or not key:
        raise ValueError("Credenciais do Supabase não encontradas.")

    return create_client(url, key)
