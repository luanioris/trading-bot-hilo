import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.brapi import BrapiClient
from datetime import datetime

print("=== TESTE DE DIAGNÓSTICO DA BRAPI ===\n")

client = BrapiClient()

# Teste 1: Buscar dados de 1 dia (intraday)
print("1. Buscando range=1d (candle de hoje)...")
data_1d = client.get_historical_data("PETR4", range="1d", interval="1d", include_today=False)

if data_1d:
    last = data_1d[-1]
    dt = datetime.fromtimestamp(last['date'])
    print(f"   Último candle: {dt.strftime('%d/%m/%Y %H:%M')}")
    print(f"   Close: R$ {last['close']}")
else:
    print("   ❌ Nenhum dado retornado!")

print("\n2. Buscando range=3mo (histórico)...")
data_3mo = client.get_historical_data("PETR4", range="3mo", interval="1d", include_today=False)

if data_3mo:
    last = data_3mo[-1]
    dt = datetime.fromtimestamp(last['date'])
    print(f"   Último candle: {dt.strftime('%d/%m/%Y %H:%M')}")
    print(f"   Close: R$ {last['close']}")
    print(f"   Total de candles: {len(data_3mo)}")
else:
    print("   ❌ Nenhum dado retornado!")

print("\n3. Testando include_today=True...")
data_combined = client.get_historical_data("PETR4", range="3mo", interval="1d", include_today=True)

if data_combined:
    last = data_combined[-1]
    dt = datetime.fromtimestamp(last['date'])
    print(f"   Último candle após merge: {dt.strftime('%d/%m/%Y %H:%M')}")
    print(f"   Close: R$ {last['close']}")
    print(f"   Total de candles: {len(data_combined)}")
