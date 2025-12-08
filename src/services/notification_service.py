import requests
import json
import os
from datetime import date

from src.services.supabase_client import get_supabase_client

class NotificationService:
    def __init__(self):
        # URL e Key fornecidas pelo usuário
        self.api_url = "https://fr-evolution.cloudfy.cloud/message/sendText/whats-pessoal-luan"
        self.api_key = "HCpB8KZrD4GfzvApf8uYydMopc4XW9Qb"
        
        # Conectar ao banco para pegar configuração dinâmica
        self.supabase = get_supabase_client()
        self.target_number = self._get_target_number()

    def _get_target_number(self):
        """Busca o número de telefone salvo nas configurações do App."""
        try:
            resp = self.supabase.table("app_config").select("value").eq("key", "whatsapp_number").execute()
            if resp.data:
                return resp.data[0]['value']
        except Exception as e:
            print(f"\t⚠️ Erro ao ler config de telefone: {e}")
        
        return "5562981867784" # Fallback (seu número padrão)

    def send_signal_message(self, ticker, signal_type, option_data, exit_alert=None):
        """
        Formata e envia a mensagem do sinal via WhatsApp.
        :param exit_alert: Texto opcional com instrução de saída (gestão de carteira).
        """
        
        emoji = "🚀" if "ALTA" in signal_type else "🔻"
        direction = "COMPRA (CALL)" if "ALTA" in signal_type else "VENDA (PUT)"
        
        # Formatar valor monetário (se disponível)
        strike_fmt = f"R$ {option_data['strike']:.2f}"
        price_fmt = f"R$ {option_data.get('last_price', 0.0):.2f}"
        
        msg_date = date.today().strftime('%d/%m/%Y')
        
        # Montar cabeçalho (com ou sem alerta de saída)
        header = f"*{emoji} NOVO SINAL DETECTADO: {ticker}*\n📅 {msg_date}\n"
        
        if exit_alert:
            header = f"🚨 *ATENÇÃO: GESTÃO DE CARTEIRA*\n{exit_alert}\n\n" + header
        
        message_text = (
            f"{header}\n"
            f"📊 *Direção:* {signal_type}\n"
            f"💎 *Sugestão:* {option_data['ticker']}\n"
            f"💰 *Preço Opção:* {price_fmt}\n"
            f"🎯 *Strike:* {strike_fmt} ({direction})\n"
            f"📅 *Vencimento:* {option_data['dte']} dias\n"
            f"🌊 *Liquidez:* {option_data.get('trades', 0)} negócios\n\n"
            f"_Verifique o gráfico antes de operar._"
        )
        
        return self._send_whatsapp(message_text)

    def send_daily_summary(self, results):
        """
        Envia um relatório resumido com o status de TODOS os ativos analisados.
        """
        if not results:
            return False
            
        lines = []
        lines.append("📊 *RELATÓRIO DE FECHAMENTO* 📊")
        lines.append(f"📅 {date.today().strftime('%d/%m/%Y')}\n")
        
        for r in results:
            ticker = r['ticker']
            price = f"R$ {r['close']:.2f}"
            
            # Ícone baseado no Status
            if r['trend'] == 'UP':
                if r['signal']: # Virada de alta hoje
                    status = "🚀 *COMPRA (Novo)*"
                else: 
                    status = "🟢 Segue Alta"
            else:
                if r['signal']: # Virada de baixa hoje
                    status = "🔻 *VENDA (Novo)*"
                else:
                    status = "🔴 Segue Baixa"
            
            lines.append(f"*{ticker}* ({price}): {status}")
            
        lines.append(f"\n_Total analisados: {len(results)}_")
        
        full_text = "\n".join(lines)
        return self._send_whatsapp(full_text)

    def _send_whatsapp(self, text):
        headers = {
            "apikey": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "number": self.target_number,
            "text": text
        }
        
        try:
            print(f"\t📨 Enviando WhatsApp para {self.target_number}...")
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=10)
            
            if response.status_code in [200, 201]:
                print("\t✅ Mensagem enviada com sucesso!")
                return True
            else:
                print(f"\t❌ Erro Evolution API: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"\t❌ Falha na conexão com WhatsApp: {e}")
            return False

# Teste rápido se rodar direto
if __name__ == "__main__":
    svc = NotificationService()
    svc._send_whatsapp("🤖 Teste de conexão: Trading Bot Ativo!")
