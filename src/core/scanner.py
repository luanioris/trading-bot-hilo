import pandas as pd
from datetime import datetime
from src.services.brapi import BrapiClient
from src.core.indicators import Indicators
from src.core.options_selector import OptionsSelector
from src.services.repository import Repository
from src.services.notification_service import NotificationService

class MarketScanner:
    def __init__(self, hilo_period: int = 10, profit_target: float = 50.0):
        self.brapi = BrapiClient()
        self.selector = OptionsSelector()
        self.repository = Repository()
        self.notifier = NotificationService()
        self.hilo_period = hilo_period
        self.profit_target = profit_target

    def analyze_asset(self, ticker: str, force_notification: bool = False):
        """
        Analisa um ativo específico para buscar sinais de HiLo e gerenciar posições.
        """
        # 1. Buscar dados históricos
        raw_data = self.brapi.get_historical_data(ticker, range='3mo', interval='1d')
        
        if not raw_data:
            return None

        # 2. Converter para DataFrame
        df = pd.DataFrame(raw_data)
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], unit='s', errors='coerce')
        
        # 3. Aplicar HiLo com período dinâmico
        df_hilo = Indicators.calculate_hilo(df, period=self.hilo_period)
        
        # 4. Analisar último candle
        last_candle = df_hilo.iloc[-1]
        prev_candle = df_hilo.iloc[-2]
        
        signal = None
        
        # Detectar flip
        if prev_candle['trend'] == -1 and last_candle['trend'] == 1:
            signal = "VIRADA PARA ALTA (Compra)"
        elif prev_candle['trend'] == 1 and last_candle['trend'] == -1:
            signal = "VIRADA PARA BAIXA (Venda)"
            
        suggested_option = None
        
        # Se houve sinal, buscar opção
        if signal:
            print(f"\t🔎 Buscando opções para {ticker} ({signal})...")
            options_chain = self.brapi.get_options_chain(ticker)
            if options_chain:
                suggested_option = self.selector.filter_options(
                    options_chain, 
                    last_candle['close'], 
                    signal
                )
            
        result = {
            "ticker": ticker,
            "date": last_candle['date'],
            "close": last_candle['close'],
            "hilo": last_candle['hilo'],
            "trend": "UP" if last_candle['trend'] == 1 else "DOWN",
            "signal": signal,
            "option": suggested_option
        }
        
        # --- VERIFICAÇÃO DE GESTÃO (Sinal ou Monitoramento de Lucro) ---
        # Mesmo se não tiver sinal novo, podemos querer checar lucro.
        
        # Buscar posições abertas deste ativo
        open_positions = self.repository.get_open_positions_by_asset(ticker)
        exit_alert_msg = None
        exit_lines = []

        if open_positions:
            # 1. Verificar conflito de tendência (Inversão de Mão)
            if signal:
                for pos in open_positions:
                    pos_type_normalized = "PUT" if "PUT" in pos['type'].upper() else "CALL"
                    
                    if "ALTA" in signal and pos_type_normalized == "PUT":
                        exit_lines.append(f"⚠️ SAÍDA IMEDIATA (Inversão): Put *{pos['ticker_option']}*")
                    elif "BAIXA" in signal and pos_type_normalized == "CALL":
                        exit_lines.append(f"⚠️ SAÍDA IMEDIATA (Inversão): Call *{pos['ticker_option']}*")

            # 2. Verificar Meta de Lucro (Profit Target)
            # Buscar cotações atuais das opções em carteira
            tickers_opts = [pos['ticker_option'] for pos in open_positions]
            quotes = self.brapi.get_quotes(tickers_opts)
            
            for pos in open_positions:
                tk_opt = pos['ticker_option']
                curr_price = float(quotes.get(tk_opt, 0.0))
                entry_price = float(pos['entry_price'])
                
                if curr_price > 0 and entry_price > 0:
                    profit_pct = ((curr_price - entry_price) / entry_price) * 100
                    
                    # Se lucro maior que o target definido no JSON
                    if profit_pct >= self.profit_target:
                        emoji_rocket = "🚀"
                        exit_lines.append(f"{emoji_rocket} META BATIDA ({profit_pct:.1f}%): *{tk_opt}* a R$ {curr_price:.2f}")
                        print(f"\t💰 ALERTA LUCRO: {tk_opt} bateu {profit_pct:.1f}% (Meta: {self.profit_target}%)")

            if exit_lines:
                exit_alert_msg = "\n".join(exit_lines)

        # Persistência e Notificação
        # Notificar se: (Tem Sinal Novo) OU (Forced) OU (Tem Alerta de Gestão/Lucro)
        if signal or exit_alert_msg:
            try:
                # Salvar sinal apenas se existir (pode ser só um check de lucro sem sinal de hilo)
                is_new = False
                if signal:
                    signal_id, is_new = self.repository.save_signal(result)
                
                should_notify = is_new or force_notification or (exit_alert_msg is not None)
                
                # Se for só alerta de gestão sem opção sugerida (ex: só lucro), montamos payload minimo
                opt_payload = result.get('option')
                if not opt_payload and exit_alert_msg:
                    # Mock payload para não quebrar notification service
                    opt_payload = {'ticker_option': 'GESTÃO', 'strike': 0, 'last_price': 0, 'days_to_expire': 0}

                if should_notify and opt_payload:
                    print("\t📲 Enviando notificação via WhatsApp...")
                    # Se não tiver sinal (só gestão), manda "MONITORAMENTO" como título
                    sig_title = signal if signal else "MONITORAMENTO DE CARTEIRA"
                    
                    self.notifier.send_signal_message(
                        ticker, 
                        sig_title, 
                        opt_payload,
                        exit_alert=exit_alert_msg
                    )
            except Exception as e:
                print(f"\t❌ Erro ao salvar/notificar: {e}")
        
        return result
