import requests
import pandas as pd
from datetime import datetime
import yfinance as yf
from src.config import Config
from src.services.opcoes_net import OpcoesNetClient

class BrapiClient:
    BASE_URL = "https://brapi.dev/api"

    def __init__(self):
        self.token = Config.BRAPI_TOKEN
        self.opcoes_net = OpcoesNetClient() # Cliente Scraping seguro
        if not self.token:
            raise ValueError("Token da Brapi não configurado.")

    def get_options_chain(self, ticker: str):
        """
        Busca a lista de opções.
        Prioriza Opcoes.net.br via scraping seguro.
        """
        try:
            print(f"\t🔄 Usando Opcoes.net.br para dados de opções de {ticker}")
            return self.opcoes_net.get_options_chain(ticker)
        except Exception as e:
            print(f"⚠️ Erro no gateway de opções: {e}")
            return []

    def get_quotes(self, tickers: list):
        """
        Busca cotações atuais para uma lista de tickers.
        Ex: tickers=['PETR4', 'VALE3', 'PETRM400']
        Retorna: {'PETR4': 34.50, 'VALE3': 60.10}
        """
        if not tickers:
            return {}
            
        params = {
            'token': self.token,
        }
        # A Brapi aceita tickers separados por vírgula na URL para o endpoint /quote/
        tickers_str = ",".join(tickers)
        url = f"{self.BASE_URL}/quote/{tickers_str}"
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Mapear resposta para dict {ticker: price}
            results = {}
            if 'results' in data:
                for item in data['results']:
                    sym = item.get('symbol')
                    price = item.get('regularMarketPrice')
                    if sym and price:
                        results[sym] = price
            return results
            
        except Exception as e:
            print(f"⚠️ Erro ao buscar cotações na Brapi: {e}")
            return {}

    def get_ticker_details(self, ticker: str):
        """Busca detalhes cadastrais (Nome, Setor) do ativo."""
        try:
            url = f"{self.BASE_URL}/quote/{ticker}"
            params = {'token': self.token, 'fundamental': 'true'} # Fundamental pode vir no quote default as vezes
            response = requests.get(url, params=params)
            data = response.json()
            
            if 'results' in data and data['results']:
                res = data['results'][0]
                return {
                     'longName': res.get('longName') or res.get('shortName'),
                     'sector': res.get('sector')
                }
        except Exception:
            pass
        return {'longName': None, 'sector': None}


    
    def get_historical_data(self, ticker: str, range: str = '3mo', interval: str = '1d', include_today: bool = False):
        """
        Busca candles históricos.
        SUBSTITUÍDO POR YFINANCE (Dados Ajustados) para garantir consistência com ProfitChart.
        Mantém interface original da Brapi.
        """
        try:
            # print(f"\t🔄 [YF] Buscando histórico ajustado de {ticker} ({range})...")
            
            # Adicionar sufixo .SA se não tiver
            yf_ticker = f"{ticker}.SA" if not ticker.endswith(".SA") else ticker
            
            # Mapeamento de ranges da API Brapi -> YFinance
            # (Geralmente são compatíveis: 1d, 5d, 1mo, 3mo, 6mo, 1y, 5y, max)
            
            # Baixar dados (auto_adjust=True garante Split/Dividendos ajustados)
            # progress=False desativa barra de progresso do YF
            df = yf.download(yf_ticker, period=range, interval=interval, auto_adjust=True, progress=False, multi_level_index=False)
            
            if df.empty:
                print(f"⚠️ YFinance retornou vazio para {ticker}")
                return []

            # Tratar include_today
            if not include_today:
                today = pd.Timestamp.now().normalize()
                # Remove se o último registro for de hoje
                if df.index[-1].normalize() == today:
                    # print(f"\t🧹 [YF] Removendo candle de hoje ({df.index[-1].date()})")
                    df = df.iloc[:-1]

            results = []
            for date, row in df.iterrows():
                # Converter para formato padrão do sistema (Timestamp Unix)
                # YFinance date é Timestamp. timestamp() retorna float.
                ts = int(date.timestamp())
                
                # Tratamento seguro de NaN
                val_close = float(row['Close']) if pd.notnull(row['Close']) else 0.0
                val_open = float(row['Open']) if pd.notnull(row['Open']) else val_close
                val_high = float(row['High']) if pd.notnull(row['High']) else val_close
                val_low = float(row['Low']) if pd.notnull(row['Low']) else val_close
                
                # Sanity Check para High/Low Zeros (Raríssimo no YF Ajustado, mas mantendo a lógica)
                if val_high == 0.0 or val_low == 0.0:
                     val_high = max(val_open, val_close)
                     val_low = min(val_open, val_close)

                results.append({
                    'date': ts,
                    'open': val_open,
                    'high': val_high,
                    'low': val_low,
                    'close': val_close,
                    'volume': int(row['Volume']) if pd.notnull(row['Volume']) else 0
                })
                
            return results

        except Exception as e:
            print(f"❌ Erro ao buscar histórico via YFinance: {e}")
            return []
