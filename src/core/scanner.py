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
        from datetime import date as dt_date
        
        # 1. Buscar dados históricos (SEM candle sintético para não distorcer HiLo)
        raw_data = self.brapi.get_historical_data(ticker, range='3mo', interval='1d', include_today=False)
        
        if not raw_data:
            return None

        # 2. Converter para DataFrame
        df = pd.DataFrame(raw_data)
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], unit='s', errors='coerce')
        
        # --- ETAPA CRÍTICA: LIMPEZA DE DADOS (DATA SANITIZATION) ---
        # A Brapi às vezes retorna o candle de hoje incompleto no histórico.
        # Isso destrói o cálculo de médias (HiLo). DEVEMOS REMOVÊ-LO.
        
        # 1. Remove candle de "Hoje" se existir (garante D-1)
        today_date = pd.Timestamp.now().normalize()
        if not df.empty and df.iloc[-1]['date'].normalize() == today_date:
            print(f"\t🧹 Removendo candle incompleto de hoje ({df.iloc[-1]['date'].strftime('%d/%m')}) do histórico.")
            df = df.iloc[:-1].copy()
            
        # 2. Remove candles inválidos (High == Low e Volume 0) que são erro de dados
        # O HiLo depende da volatilidade (High-Low). Candles flat distorcem a média.
        params_invalid = (df['high'] == df['low']) & (df['close'] > 0)
        if params_invalid.any():
            invalid_count = params_invalid.sum()
            # Se for apenas 1 ou 2 dias isolados, removemos. Se for muitos, abortamos.
            if invalid_count < 5:
                # print(f"\t🧹 Removendo {invalid_count} candles 'flat' (High=Low) do histórico.")
                df = df[~params_invalid].copy()
            else:
                print(f"\t⚠️ ALERTA CRÍTICO: Dados históricos de {ticker} parecem corrompidos ({invalid_count} dias flat). Abortando.")
                return None
            
        if df.empty:
            print(f"\t⚠️ Sem dados históricos suficientes após limpeza para {ticker}.")
            return None

        # 3. Aplicar HiLo com período dinâmico (usando dados históricos puros e limpos)
        df_hilo = Indicators.calculate_hilo(df, period=self.hilo_period)
        
        # 4. Analisar último candle HISTÓRICO
        last_candle = df_hilo.iloc[-1]
        prev_candle = df_hilo.iloc[-2]
        
        # 5. Buscar COTAÇÃO ATUAL (tempo real) para comparação
        current_quotes = self.brapi.get_quotes([ticker])
        current_price = current_quotes.get(ticker)
        
        if not current_price:
            # Se não conseguiu cotação atual, usa o último histórico
            current_price = float(last_candle['close'])
            print(f"\t⚠️ Usando preço histórico para {ticker}: R$ {current_price:.2f}")
        else:
            print(f"\t📊 Cotação atual de {ticker}: R$ {current_price:.2f}")
        
        signal = None
        
        # 6. Detectar flip comparando TENDÊNCIA ANTERIOR vs POSIÇÃO ATUAL DO PREÇO
        # O HiLo foi calculado até ontem/último dia disponível
        # Agora vemos se o preço ATUAL está acima ou abaixo do HiLo
        hilo_value = float(last_candle['hilo'])
        
        # Determinar tendência atual baseada no preço de agora
        current_trend = 1 if current_price > hilo_value else -1
        previous_trend = int(last_candle['trend'])

        # --- LOG VERBOSO RESTAURADO ---
        print(f"\n--- 🔍 Análise Detalhada: {ticker} ---")
        date_str = last_candle['date'].strftime('%d/%m/%Y') if hasattr(last_candle['date'], 'strftime') else str(last_candle['date'])
        print(f"1. Último Fechamento ({date_str}): R$ {last_candle['close']:.2f}")
        print(f"   SMA High (Teto): {last_candle.get('sma_high', 0):.2f} | SMA Low (Piso): {last_candle.get('sma_low', 0):.2f}")
        
        trend_label = "ALTA 🟢" if previous_trend == 1 else "BAIXA 🔴"
        print(f"2. Tendência Anterior: {trend_label}")
        print(f"3. Cotação Atual: R$ {current_price:.2f} (Tempo Real)")
        print(f"   HiLo Ativo (Stop): R$ {hilo_value:.2f}")
        # ------------------------------

        # Proximity Check (0.5%)
        # Calculate absolute percentage distance to HiLo
        proximity_pct = abs(current_price - hilo_value) / current_price if current_price > 0 else 1.0
        is_proximity_warning = proximity_pct < 0.005 # Menor que 0.5%
        
        warn_msg = "⚠️ ALERTA: Próximo da Reversão!" if is_proximity_warning else "OK (Distância segura)"
        print(f"   Distância do HiLo: {proximity_pct*100:.2f}% -> {warn_msg}")
        
        # Detectar virada
        if previous_trend == -1 and current_trend == 1:
            signal = "VIRADA PARA ALTA (Compra)"
        elif previous_trend == 1 and current_trend == -1:
            signal = "VIRADA PARA BAIXA (Venda)"
            
        if signal:
            print(f"4. Diagnóstico: 🚨 DETECTADO {signal}")
        else:
            print(f"4. Diagnóstico: Tendência Mantida (Sem Sinais)")
            
        suggested_option = None
        
        # Se houve sinal, buscar opção
        if signal:
            print(f"\t🔎 Buscando opções para {ticker} ({signal})...")
            options_chain = self.brapi.get_options_chain(ticker)
            if options_chain:
                suggested_option = self.selector.filter_options(
                    options_chain, 
                    current_price,  # Usar preço ATUAL, não histórico
                    signal
                )
            
        result = {
            "ticker": ticker,
            "date": datetime.now(),  # Data/hora ATUAL da análise
            "close": current_price,  # Preço ATUAL
            "hilo": hilo_value,
            "trend": "UP" if current_trend == 1 else "DOWN",
            "signal": signal,
            "option": suggested_option,
            "is_proximity_warning": is_proximity_warning
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

                if should_notify:
                    print("\t📲 Enviando notificação via WhatsApp...")
                    # Se não tiver sinal (só gestão), manda "MONITORAMENTO" como título
                    sig_title = signal if signal else "MONITORAMENTO DE CARTEIRA"
                    
                    self.notifier.send_signal_message(
                        ticker, 
                        sig_title, 
                        opt_payload, # Pode ser None agora
                        exit_alert=exit_alert_msg
                    )
            except Exception as e:
                print(f"\t❌ Erro ao salvar/notificar: {e}")
        
        return result
