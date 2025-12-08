import sys
import os

# Adiciona o diretório raiz ao PYTHONPATH
sys.path.append(os.getcwd())

from src.services.brapi import BrapiClient
from src.core.options_selector import OptionsSelector
import pandas as pd

def test_manual_options():
    print("=== Teste Manual do Seletor de Opções ===")
    
    ticker = "PETR4"
    current_price = 31.37  # Preço de referência (fechamento recente)
    simulated_signal = "VIRADA PARA BAIXA (Venda)" # Simulando que virou para venda hoje
    
    print(f"🔹 Ativo: {ticker}")
    print(f"🔹 Preço Atual: R$ {current_price}")
    print(f"🔹 Sinal Simulado: {simulated_signal} -> Deve buscar PUT ATM")
    
    # 1. Buscar Cadeia na Brapi
    print("\n1. Buscando dados na Brapi...")
    brapi = BrapiClient()
    options_chain = brapi.get_options_chain(ticker)
    
    if not options_chain:
        print("❌ Falha ao buscar opções (API retornou vazio ou erro). Verifique o Token.")
        return

    print(f"✅ Recebidas {len(options_chain)} opções brutas.")
    
    # 2. Filtrar
    print("\n2. Filtrando Melhor Opção (30-45 dias, ATM)...")
    selector = OptionsSelector()
    best_option = selector.filter_options(options_chain, current_price, simulated_signal)
    
    if best_option:
        print("\n🏆 OPÇÃO ELEGIDA:")
        print(f"   Ticker: {best_option['ticker']}")
        print(f"   Tipo: {best_option['type']}")
        print(f"   Strike: R$ {best_option['strike']}")
        print(f"   Vencimento: {best_option['expiration']} (Daqui a {best_option['dte']} dias)")
        print(f"   Distância do Preço: R$ {best_option['distance']:.2f}")
    else:
        print("⚠️ Nenhuma opção atendeu aos critérios.")

if __name__ == "__main__":
    test_manual_options()
