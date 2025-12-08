import pandas as pd
import numpy as np

class Indicators:
    @staticmethod
    def calculate_hilo(df: pd.DataFrame, period: int = 10) -> pd.DataFrame:
        """
        Calcula o HiLo Activator (High Low Activator) de X períodos.
        
        Lógica:
        - HiLo Top (Stop de Venda) = SMA das Máximas 
        - HiLo Bottom (Stop de Compra) = SMA das Mínimas
        - Se Fechamento > Top -> Tendência UP (desenha Bottom)
        - Se Fechamento < Bottom -> Tendência DOWN (desenha Top)
        
        Retorna o DataFrame com colunas adicionais: 'hilo', 'trend' (1 = Alta, -1 = Baixa)
        """
        # Garante que temos dados suficientes
        if len(df) < period:
            return df
        
        # 1. Calcular as médias móveis simples de High e Low
        # Testando SEM shift para ver se bate com Profit
        df['sma_high'] = df['high'].rolling(window=period).mean()
        df['sma_low'] = df['low'].rolling(window=period).mean()
        
        # 2. Inicializar colunas
        df['hilo'] = np.nan
        df['trend'] = 0 # 0 = undefined, 1 = up, -1 = down
        
        # 3. Iterar para definir a tendência (HiLo é path-dependent)
        
        trend = -1 # Default inicial
        # Warmup inicial
        hilo_val = df['sma_high'].iloc[period] 
        
        # Começamos a iterar a partir do ponto onde temos dados (period)
        for i in range(period, len(df)):
            close = df['close'].iloc[i]
            high_sma = df['sma_high'].iloc[i]
            low_sma = df['sma_low'].iloc[i]
            
            # Lógica Alternativa: Comparar com as SMAs diretamente
            if trend == -1: # Tendência de Baixa
                if close > high_sma:
                    trend = 1 # Flip para Alta
                    hilo_val = low_sma
                else:
                    hilo_val = high_sma
            
            elif trend == 1: # Tendência de Alta
                if close < low_sma:
                    trend = -1 # Flip para Baixa
                    hilo_val = high_sma
                else:
                    hilo_val = low_sma
            
            df.at[df.index[i], 'hilo'] = hilo_val
            df.at[df.index[i], 'trend'] = trend

        return df
