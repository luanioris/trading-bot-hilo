import os
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
load_dotenv()

class Config:
    BRAPI_TOKEN = os.getenv("BRAPI_TOKEN")
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

    @classmethod
    def validate(cls):
        missing = []
        if not cls.BRAPI_TOKEN:
            missing.append("BRAPI_TOKEN")
        if not cls.SUPABASE_URL:
            missing.append("SUPABASE_URL")
        if not cls.SUPABASE_KEY:
            missing.append("SUPABASE_KEY")
        
        if missing:
            raise ValueError(f"Faltam variáveis de ambiente configuradas: {', '.join(missing)}")

# Exemplo de uso:
# Config.validate()
# print(Config.BRAPI_TOKEN)
