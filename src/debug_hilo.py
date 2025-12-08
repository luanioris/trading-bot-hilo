import sys
import os
sys.path.append(os.getcwd())

from src.services.brapi import BrapiClient
import pandas as pd
import numpy as np

def calculate_hilo_ultra_debug(df: pd.DataFrame, period: int = 10):
    """Versão com debug ultra detalhado"""
    if len(df) < period:
        return df
    
    df['sma_high'] = df['high'].rolling(window=period).mean()
    df['sma_low'] = df['low'].rolling(window=period).mean()
    
    df['hilo'] = np.nan
    df['trend'] = 0
    
    trend = -1
    hilo_val = df['sma_high'].iloc[period-1]
    
    print(f"\n🔧 Iniciando HiLo (período {period})")
    print(f"   Trend inicial: {trend}")
    print(f"   HiLo inicial: {hilo_val:.2f}\n")
    
    for i in range(period, len(df)):
        close = df['close'].iloc[i]
        high_sma = df['sma_high'].iloc[i]
        low_sma = df['sma_low'].iloc[i]
        date = df['date'].iloc[i]
        
        prev_trend = trend
        
        # Debug ANTES da lógica
        if i >= len(df) - 2:
            print(f"\n📍 {date.strftime('%d/%m')} ANTES:")
            print(f"   Close: {close:.2f}")
            print(f"   SMA_H: {high_sma:.2f} | SMA_L: {low_sma:.2f}")
            print(f"   Trend atual: {trend}")
        
        # Lógica
        if trend == -1:
            if close > high_sma:
                if i >= len(df) - 2:
                    print(f"   ✅ {close:.2f} > {high_sma:.2f} → FLIP para ALTA")
                trend = 1
                hilo_val = low_sma
            else:
                if i >= len(df) - 2:
                    print(f"   ❌ {close:.2f} <= {high_sma:.2f} → Mantém BAIXA")
                hilo_val = high_sma
        
        elif trend == 1:
            if close < low_sma:
                if i >= len(df) - 2:
                    print(f"   ✅ {close:.2f} < {low_sma:.2f} → FLIP para BAIXA")
                trend = -1
                hilo_val = high_sma
            else:
                if i >= len(df) - 2:
                    print(f"   ❌ {close:.2f} >= {low_sma:.2f} → Mantém ALTA")
                hilo_val = low_sma
        
        df.at[df.index[i], 'hilo'] = hilo_val
        df.at[df.index[i], 'trend'] = trend
        
        if i >= len(df) - 2:
            print(f"   DEPOIS: Trend={trend}, HiLo={hilo_val:.2f}")
    
    return df

# Teste
brapi = BrapiClient()
raw_data = brapi.get_historical_data("BOVA11", range='1mo', interval='1d')
df = pd.DataFrame(raw_data)
df['date'] = pd.to_datetime(df['date'], unit='s')

df_result = calculate_hilo_ultra_debug(df, period=10)

print("\n📊 RESULTADO FINAL:")
last = df_result.iloc[-1]
print(f"Data: {last['date'].strftime('%d/%m/%Y')}")
print(f"Close: {last['close']}")
print(f"HiLo: {last['hilo']:.2f}")
print(f"Trend: {'UP' if last['trend'] == 1 else 'DOWN'}")
