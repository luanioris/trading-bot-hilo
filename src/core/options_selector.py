from datetime import datetime, timedelta
import pandas as pd
import math

class OptionsSelector:
    def __init__(self):
        pass

    def _calculate_bs_delta(self, S, K, days, r=0.1125, sigma=0.32, type_='CALL'):
        """
        Estima Delta usando Black-Scholes.
        S: Preço Ativo, K: Strike, days: Dias úteis (DTE), r: Taxa Livre Risco (11.25%), sigma: Volatilidade (32%)
        """
        if days <= 0 or S <= 0 or K <= 0: return 0.0
        T = days / 365.0
        try:
            d1 = (math.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*math.sqrt(T))
            # Aproximação da CDF Normal usando math.erf
            cdf_d1 = 0.5 * (1 + math.erf(d1 / math.sqrt(2)))
            
            if type_ == 'CALL':
                return cdf_d1
            else:
                return cdf_d1 - 1
        except Exception:
            return 0.0

    def filter_options(self, options_list, current_price, signal_type):
        """
        Filtra a melhor opção com base no setup Vencedor:
        - Vencimento: 30 a 75 dias (Mensal).
        - Delta: 0.42 a 0.50 (Calculado via Black-Scholes Vol 32%).
        - Liquidez: Tie-breaker.
        """
        if not options_list:
            return None

        # 1. Converter datas e criar DataFrame
        df = pd.DataFrame(options_list)
        df['expirationDate'] = pd.to_datetime(df['expirationDate'])
        
        # 2. Calcular DTE
        today = pd.Timestamp.now().normalize()
        df['dte'] = (df['expirationDate'] - today).dt.days
        
        # 3. Filtrar Vencimento (Janela Segura)
        df_valid = df[(df['dte'] >= 25) & (df['dte'] <= 80)].copy()
        
        if df_valid.empty:
            print("⚠️ Nenhuma opção com vencimento entre 25-80 dias.")
            return None

        # 4. Filtrar pelo Tipo (CALL ou PUT)
        target_type = "CALL" if "ALTA" in signal_type else "PUT"
        df_type = df_valid[df_valid['type'] == target_type].copy()
        
        if df_type.empty:
            return None

        # 5. Calcular Delta Black-Scholes
        df_type['delta_bs'] = df_type.apply(
            lambda row: self._calculate_bs_delta(
                S=current_price,
                K=float(row['strike']),
                days=row['dte'],
                type_=row['type']
            ), axis=1
        )

        # 6. Filtrar Range Delta 0.40 - 0.50 (User Request)
        if target_type == "CALL":
            # Alvo: 0.40 a 0.50 (com leve margem superior)
            mask = (df_type['delta_bs'] >= 0.39) & (df_type['delta_bs'] <= 0.53) 
            target_delta = 0.40
        else:
            # PUT (Deltas negativos): -0.40 a -0.50
            # Note: 0.40 delta put means -0.40
            mask = (df_type['delta_bs'] >= -0.53) & (df_type['delta_bs'] <= -0.39)
            target_delta = -0.40
            
        candidates = df_type[mask].copy()
        
        if candidates.empty:
            print(f"⚠️ Nenhuma opção no range de Delta (0.42-0.50).")
            # Opcional: Fallback para moneyness se crítico, mas por segurança retornamos None
            return None

        # 7. Filtrar Liquidez (> 0) e Ordenar
        if 'trades' not in candidates.columns:
            candidates['trades'] = 0
            
        candidates = candidates[candidates['trades'] > 0]
        
        if candidates.empty:
            print(f"⚠️ Opções encontradas no Delta, mas sem liquidez.")
            return None

        # Ordenar: Mais próximo do Delta 0.40 (User Request), desempate por Liquidez
        # O usuário quer priorizar o delta mais próximo de 0.40 e ir subindo.
        candidates['dist_to_target'] = abs(candidates['delta_bs'] - target_delta)
        
        best_option = candidates.sort_values(
            by=['dist_to_target', 'trades'],
            ascending=[True, False]
        ).iloc[0]

        return {
            "type": best_option['type'],
            "ticker": best_option['stock'],
            "strike": best_option['strike'],
            "expiration": best_option['expirationDate'].strftime('%Y-%m-%d'),
            "dte": best_option['dte'],
            "trades": int(best_option.get('trades', 0)),
            "last_price": float(best_option.get('lastPrice', 0.0)),
            "delta_bs": float(best_option['delta_bs'])
        }
