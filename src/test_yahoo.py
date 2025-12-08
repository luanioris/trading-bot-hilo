import yfinance as yf
import pandas as pd
from datetime import datetime

def test_yahoo_options():
    ticker_symbol = "PETR4.SA"
    print(f"📡 Conectando ao Yahoo Finance para {ticker_symbol}...")
    
    # 1. Instanciar Ticker
    asset = yf.Ticker(ticker_symbol)
    
    # 2. Obter datas de vencimento disponíveis
    expirations = asset.options
    
    if not expirations:
        print("❌ Nenhuma data de vencimento encontrada. O Yahoo pode não ter opções para este ativo.")
        return

    print(f"✅ Vencimentos encontrados: {len(expirations)}")
    print(f"   Próximos 3: {expirations[:3]}")
    
    # 3. Pegar options chain do primeiro vencimento viável (ex: daqui a 1 mês)
    # Vamos tentar pegar o segundo ou terceiro vencimento para simular swing trade
    target_date = expirations[1] if len(expirations) > 1 else expirations[0]
    print(f"\n🔍 Baixando Cadeia para Vencimento: {target_date}")
    
    opt_chain = asset.option_chain(target_date)
    
    calls = opt_chain.calls
    puts = opt_chain.puts
    
    print(f"   📊 Calls encontradas: {len(calls)}")
    print(f"   📊 Puts encontradas: {len(puts)}")
    
    if not puts.empty:
        print("\n🔎 Exemplo de PUTs (Top 3):")
        # Colunas comuns: contractSymbol, strike, lastPrice, volume, openInterest
        print(puts[['contractSymbol', 'strike', 'lastPrice', 'volume', 'openInterest']].head(3).to_string())
    
    print("\n✅ Teste Yahoo Finance Concluído! Parece promissor.")

if __name__ == "__main__":
    test_yahoo_options()
