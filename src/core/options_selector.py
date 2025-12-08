from datetime import datetime, timedelta
import pandas as pd
import math

class OptionsSelector:
    def __init__(self):
        pass

    def filter_options(self, options_list, current_price, signal_type):
        """
        Filtra a melhor opção com base no setup:
        - Vencimento: 30 a 45 dias.
        - Strike: ATM (O mais próximo do preço atual).
        - Tipo: CALL se Alta, PUT se Baixa.
        """
        if not options_list:
            return None

        # 1. Converter datas e criar DataFrame para facilitar
        df = pd.DataFrame(options_list)
        
        # Normalizar colunas da Brapi (exemplo de retorno)
        # keys comuns: 'stock', 'name', 'expirationDate', 'strike', 'type' (CALL/PUT)
        
        # Converter expirationDate para datetime
        # Supondo formato '2025-01-20' ou timestamp
        df['expirationDate'] = pd.to_datetime(df['expirationDate'])
        
        # 2. Calcular dias até o vencimento (Days To Expiration - DTE)
        today = pd.Timestamp.now().normalize()
        df['dte'] = (df['expirationDate'] - today).dt.days
        
        # 3. Filtrar Vencimento (Padrão Swing: >= 30 dias)
        # Janela segura que aceita a mensal de 40 dias.
        df_valid_date = df[(df['dte'] >= 30) & (df['dte'] <= 75)]
        
        if df_valid_date.empty:
            # Fallback: Se não achar nada longo, avisa e tenta pegar o mais longo disponível (>30)
            print("⚠️ Nenhuma opção > 45 dias encontrada. Tentando > 30...")
            df_valid_date = df[df['dte'] >= 30].sort_values('dte', ascending=False).head(50)
            if df_valid_date.empty:
                print("⚠️ Nenhuma opção com vencimento viável encontrada.")
                return None

        # 4. Filtrar pelo Tipo (CALL ou PUT)
        target_type = "CALL" if "ALTA" in signal_type else "PUT"
        df_type = df_valid_date[df_valid_date['type'] == target_type]
        
        if df_type.empty:
            print(f"⚠️ Nenhuma opção do tipo {target_type} encontrada na janela de datas.")
            return None

        # 5. Selecionar Strike ATM (At The Money)
        # O melhor strike é aquele onde a diferença absoluta entre Strike e Preço Atual é a menor
        df_type = df_type.copy() # Evitar SettingWithCopyWarning
        df_type['dist_price'] = abs(df_type['strike'] - current_price)
        
        # Ordenar pela menor distância
        # 5. Selecionar Strike ATM com SMART LIQUIDITY
        # Estratégia: Pegar os 5 strikes mais próximos (Candidatos ATM) e escolher o que tem MAIS NEGÓCIOS.
        
        # 5. Selecionar Strike ATM (Padrão "Professor")
        # Regra: A MELHOR Distância possível, desde que tenha liquidez mínima (> 0).
        # O professor prefere acertar o strike (Gamma) do que ter liquidez massiva.
        
        # 5. Selecionar pelo "Fluxo" (Liquidez na Vizinhança ATM)
        # Estratégia Final:
        # 1. Isolar as opções próximas ao preço (Vizinhança ATM) -> Top 4 strikes mais perto.
        # 2. Dessas 4 vizinhas, escolher a que tem MAIOR LIQUIDIDADE (Trades).
        # Isso simula o operador olhando para a grade e clicando onde tem gente negociando.
        
        df_type = df_type.copy()
        df_type['dist_price'] = abs(df_type['strike'] - current_price)
        
        # Pega os 4 "vizinhos" mais próximos da linha (2 pra cima, 2 pra baixo aprox)
        neighbors = df_type.sort_values('dist_price').head(4)
        
        if neighbors.empty:
            return None
            
        # Garante que trades é int
        if 'trades' not in neighbors.columns:
            neighbors['trades'] = 0
            
        # Escolhe o CAMPEÃO DE LIQUIDEZ da vizinhança
        best_option = neighbors.sort_values('trades', ascending=False).iloc[0]
        
        # Debug para entender a decisão
        # print(f"Vizinhos: {neighbors[['stock', 'strike', 'dist_price', 'trades']].to_dict('records')}")
        # print(f"Vencedor: {best_option['stock']}")
        
        return {
            "type": best_option['type'],
            "ticker": best_option['stock'],
            "strike": best_option['strike'],
            "expiration": best_option['expirationDate'].strftime('%Y-%m-%d'),
            "dte": best_option['dte'],
            "distance": best_option['dist_price'],
            "trades": int(best_option.get('trades', 0)),
            "last_price": float(best_option.get('lastPrice', 0.0))
        }
