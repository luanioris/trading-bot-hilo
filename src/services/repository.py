from datetime import date
from src.services.supabase_client import get_supabase_client

class Repository:
    def __init__(self):
        self.supabase = get_supabase_client()

    def save_signal(self, analysis_result: dict):
        """
        Salva o sinal de virada e a oportunidade na base de dados.
        Verifica duplicidade para não salvar o mesmo sinal repetido no dia.
        """
        if not analysis_result.get('signal'):
            return None

        ticker = analysis_result['ticker']
        signal_date = analysis_result['date'].strftime('%Y-%m-%d')
        direction = "BUY" if "ALTA" in analysis_result['signal'] else "SELL"
        
        print(f"\t💾 Verificando duplicidade para {ticker} em {signal_date}...")

        # 1. Verificar se já existe sinal para este ticker nesta data
        existing = self.supabase.table("signals")\
            .select("id")\
            .eq("ticker", ticker)\
            .eq("signal_date", signal_date)\
            .execute()
            
        if existing.data:
            print(f"\t⚠️ Sinal já registrado para {ticker} hoje.")
            # Retorna ID e Flag indicando que NÃO É NOVO (False)
            return existing.data[0]['id'], False

        # 2. Inserir Sinal
        signal_payload = {
            "ticker": ticker,
            "signal_date": signal_date,
            "direction": direction,
            "price_at_signal": float(analysis_result['close']),
            "hilo_value": float(analysis_result['hilo']),
            "processed": True
        }
        
        response = self.supabase.table("signals").insert(signal_payload).execute()
        
        if not response.data:
            print(f"\t❌ Erro ao salvar sinal de {ticker}")
            return None
            
        signal_id = response.data[0]['id']
        print(f"\t✅ Sinal salvo com ID: {signal_id}")
        
        # 3. Inserir Oportunidade de Opção (se houver)
        if analysis_result.get('option'):
            opt = analysis_result['option']
            
            option_payload = {
                "signal_id": signal_id,
                "ticker_asset": ticker,
                "ticker_option": opt['ticker'],
                "option_type": opt['type'],
                "strike": float(opt['strike']),
                "expiration_date": opt['expiration'],
                "premium_at_signal": float(opt.get('last_price', 0.0)), # Preço capturado da Opcoes.net
                "distance_to_strike": float(opt['distance']),
                "days_to_expire": int(opt['dte'])
            }
            
            self.supabase.table("option_opportunities").insert(option_payload).execute()
            print(f"\t✅ Oportunidade de Opção ({opt['ticker']}) salva com sucesso!")
            
        return signal_id, True

    def get_open_positions_by_asset(self, ticker_asset: str):
        """Busca posições abertas no portfolio para um ativo específico (ex: PETR4)"""
        try:
            response = self.supabase.table("portfolio")\
                .select("*")\
                .eq("ticker_asset", ticker_asset)\
                .eq("status", "Aberta")\
                .execute()
            return response.data
        except Exception as e:
            print(f"⚠️ Erro ao buscar portfolio para {ticker_asset}: {e}")
            return []
