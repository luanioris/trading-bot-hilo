import sys
import os
import json

# Adiciona o diretório raiz ao PYTHONPATH para garantir importações corretas
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from src.core.scanner import MarketScanner
from src.services.supabase_client import get_supabase_client
from src.config import Config

# Caminho do arquivo de configuração do usuário (gerado pelo Dashboard)
CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "user_config.json")

def load_user_config():
    """Carrega as configurações definidas pelo usuário no Dashboard."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Erro ao ler config do usuário: {e}")
    # Default fallback
    return {"cron_active": True, "hilo_period": 10}

# Função auxiliar para buscar ativos no banco
def get_monitored_assets():
    supabase = get_supabase_client()
    try:
        # Pega todos os tickers da tabela assets
        response = supabase.table("assets").select("ticker").execute()
        if response.data:
            return [item['ticker'] for item in response.data]
    except Exception as e:
        print(f"⚠️ Erro ao buscar ativos do banco: {e}")
    return ["PETR4", "VALE3", "BOVA11"] # Fallback

def is_cron_active():
    """Verifica se o robô está ativo via configuração do usuário (JSON)."""
    cfg = load_user_config()
    # Padrão é True se não existir chave
    return cfg.get("cron_active", True)

def run_market_scan(specific_tickers=None, is_manual_run=False):
    """
    Função principal que orquestra a varredura.
    :param specific_tickers: Lista de tickers específicos para analisar (opcional)
    :param is_manual_run: Se True, ignora a trava do Cron (roda mesmo se estiver pausado)
    """
    print("=== Trading Bot B3 - HiLo Scanner ===")
    
    try:
        Config.validate()
    except ValueError as e:
        print(f"❌ Config Error: {e}")
        return
    
    # 1. Carregar Configurações do Usuário
    user_conf = load_user_config()
    print(f"⚙️ Configurações Carregadas: {user_conf}")
    
    # 2. Checagem do Cron (Se for execução automática geral)
    if not is_manual_run and specific_tickers is None:
        if not user_conf.get("cron_active", True):
            print("⏸️ Scanner pausado pelo usuário. Encerrando.")
            return

    # 3. Definição do Escopo
    tickers = specific_tickers if specific_tickers else get_monitored_assets()
    print(f"📋 Analisando {len(tickers)} ativos: {tickers}")
    
    # 4. Instancia Scanner com Configuração de HiLo e Profit Target do Usuário
    hilo_p = int(user_conf.get("hilo_period", 10))
    prof_t = float(user_conf.get("profit_target", 50.0))
    
    scanner = MarketScanner(hilo_period=hilo_p, profit_target=prof_t)
    
    # 5. Execução
    for ticker in tickers:
        try:
            print(f"🔄 Processando {ticker} (HiLo {hilo_p})...")
            # is_manual_run força notificação? Normalmente não, só se for teste unitário.
            # Aqui vamos deixar False, a menos que queiramos forçar.
            # Se for manual run E specific_ticker, talvez o usuario queira ver o log.
            # O scanner já tem logica interna de 'is_new' para notificar.
            scanner.analyze_asset(ticker)
            
        except Exception as e:
            print(f"❌ Erro em {ticker}: {e}")
            
    print("=== Fim da Análise ===")

if __name__ == "__main__":
    # Se rodar direto: python src/main.py
    run_market_scan()
