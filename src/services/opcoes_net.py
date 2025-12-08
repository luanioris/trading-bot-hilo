from datetime import datetime, timedelta
import requests
import pandas as pd

class OpcoesNetClient:
    """
    Cliente reverso otimizado para Opcoes.net.br.
    Estratégia: 
    1. Buscar lista de Vencimentos Disponíveis (via endpoint main).
    2. Calcular qual vencimento cai na janela ideal (30-45 dias).
    3. Buscar opções APENAS desse vencimento específico.
    """
    
    BASE_URL = "https://opcoes.net.br/listaopcoes/completa"
    
    def get_options_chain(self, ticker: str):
        print(f"\t🔌 Conectando Opcoes.net.br para {ticker}...")
        
        # 1. Obter Vencimentos usando o endpoint "Completa" que sabemos que funciona
        vencimentos = self._get_vencimentos_robust(ticker)
        if not vencimentos:
            print("\t⚠️ Não foi possível obter vencimentos.")
            return []
            
        # 2. Encontrar Vencimento Ideal (entre 25 e 45 dias)
        target_vencimento = self._select_ideal_expiration(vencimentos)
        
        if not target_vencimento:
            print("\t⚠️ Sem vencimentos na janela ideal. Pegando o segundo mais próximo.")
            target_vencimento = vencimentos[1] if len(vencimentos) > 1 else vencimentos[0]
            
        print(f"\t📅 Vencimento Alvo: {target_vencimento['value']} (DTE: {target_vencimento['dte']}d)")
        
        # 3. Buscar Grade
        return self._fetch_options_by_expiration(ticker, target_vencimento['value'])

    def _get_vencimentos_robust(self, ticker):
        """Busca JSON de vencimentos disponíveis usando a rota principal"""
        params = {
            "idAcao": ticker,
            "listarVencimentos": "true",
            "cotacoes": "true" # Traz tudo
        }
        headers = { 
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest" 
        }
        
        try:
            r = requests.get(self.BASE_URL, params=params, headers=headers, timeout=10)
            data = r.json()
            
            # O site retorna os vencimentos dentro de 'data' -> 'vencimentos'
            raw_vencimentos = data.get('data', {}).get('vencimentos', [])
            
            if not raw_vencimentos:
                return []
            
            print(f"\t🔍 DEBUG RAW VENCIMENTOS (Primeiro item): {raw_vencimentos[0]} (Tipo: {type(raw_vencimentos[0])})")
                
            return [self._parse_vencimento(d) for d in raw_vencimentos]
            
        except Exception as e:
            print(f"\t❌ Erro ao buscar vencimentos (rota robusta): {e}")
            return []

    def _parse_vencimento(self, item):
        # O item é um dict: {'value': '2025-12-12', ..., 'dataAttributes': {'w': '...'} }
        date_str = item['value']
        
        # Identificar se é Weekly
        # Se 'w' tiver valor (ex: 'W2', 'W4'), é Weekly. Se vazio ou inexistente, é Standard (Mensal).
        attrs = item.get('dataAttributes', {})
        is_weekly = bool(attrs.get('w'))
        
        try:
            dt = pd.to_datetime(date_str, dayfirst=False) 
        except:
            dt = pd.to_datetime(date_str, errors='coerce')
            
        today = pd.Timestamp.now().normalize()
        dte = (dt - today).days
        
        return {
            "value": date_str, 
            "date": dt, 
            "dte": dte,
            "is_weekly": is_weekly
        }

    def _select_ideal_expiration(self, vencimentos_list):
        # 1. Ajuste de Janela para pegar a MENSAL (que está em ~41 dias hoje)
        # Janela 30-75 cobre o próximo vencimento e o seguinte.
        # Antes estava >45, o que matava a mensal de 41 dias.
        candidates = [v for v in vencimentos_list if 35 <= v['dte'] <= 75]
        
        if not candidates:
            return None
            
        # 2. Prioridade ABSOLUTA para Opções PADRÃO (Mensais)
        # Filtra fora as weeklies (is_weekly=True)
        standard_candidates = [v for v in candidates if not v['is_weekly']]
        
        if standard_candidates:
            # Pega a primeira mensal disponível na janela
            return standard_candidates[0]
            
        # Fallback: Se só tiver weekly (muito raro), usa weekly
        return candidates[0]

    def _fetch_options_by_expiration(self, ticker, vencimento):
        params = {
            "idAcao": ticker,
            "listarVencimentos": "false",
            "cotacoes": "true",
            "vencimentos": vencimento
        }
        headers = { "User-Agent": "Mozilla/5.0...", "X-Requested-With": "XMLHttpRequest" }
        
        try:
            r = requests.get(self.BASE_URL, params=params, headers=headers)
            data = r.json()
            raw_list = data.get('data', {}).get('cotacoesOpcoes', [])
            
            clean = []
            for item in raw_list:
                # Estrutura observada:
                # 0: Ticker_Vencimento
                # 2: Tipo (CALL/PUT)
                # 5: Strike
                # 8: Ultimo Preço
                # 9: Número de Negócios (Liquidez)
                
                clean.append({
                    "stock": item[0].split('_')[0],
                    "type": item[2],
                    "strike": float(item[5]) if item[5] is not None else 0.0,
                    "expirationDate": vencimento,
                    "lastPrice": item[8] if len(item) > 8 else 0,
                    "trades": int(item[9]) if len(item) > 9 and item[9] is not None else 0
                })
            return clean
            
        except Exception as e:
            print(f"\t❌ Erro ao buscar grade final: {e}")
            return []

