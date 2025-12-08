import sys
import os
sys.path.append(os.getcwd())

from src.services.supabase_client import get_supabase_client

def seed_assets():
    """
    Cadastra os ativos monitorados na tabela 'assets' para evitar erro de chave estrangeira.
    """
    supabase = get_supabase_client()
    
    # Lista de ativos que o user está operando
    new_tickers = [
        "RDOR3", "COGN3", "YDUQ3", "BPAC11", 
        "PETR4", "VALE3", "BOVA11", "MGLU3",
        "CYRE3", "MRVE3", "SANB11"
    ]
    
    print("💾 Cadastrando ativos no Supabase...")
    
    for ticker in new_tickers:
        try:
            # Tentar inserir (upsert não é padrão simples no cliente py, vamos de insert + ignore erro)
            # Verifica se já existe
            existing = supabase.table("assets").select("ticker").eq("ticker", ticker).execute()
            
            if not existing.data:
                data = {"ticker": ticker}
                supabase.table("assets").insert(data).execute()
                print(f"✅ {ticker} cadastrado com sucesso.")
            else:
                print(f"ℹ️ {ticker} já existe.")
                
        except Exception as e:
            print(f"⚠️ Erro ao cadastrar {ticker}: {e}")

if __name__ == "__main__":
    seed_assets()
