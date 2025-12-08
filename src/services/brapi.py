import requests
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

    def get_historical_data(self, ticker: str, range: str = "3mo", interval: str = "1d"):
        """
        Busca dados históricos (candles) para um ticker.
        Params:
            ticker: Símbolo do ativo (ex: PETR4)
            range: Janela de dados (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Intervalo dos candles (1m, 2m, 5m, 15m, 30m, 60m, 1d, 1wk, 1mo)
        """
        params = {
            'token': self.token,
            'range': range,
            'interval': interval,
            'fundamental': 'false', # Otimiza payload
        }
        url = f"{self.BASE_URL}/quote/{ticker}"
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Validar se retornou resultados
        if 'results' not in data or not data['results']:
            print(f"⚠️ Sem dados para {ticker}")
            return None

        # A Brapi retorna 'historicalDataPrice' dentro do primeiro resultado
        return data['results'][0].get('historicalDataPrice', [])
