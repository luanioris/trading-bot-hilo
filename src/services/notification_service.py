import requests
import json
import os
from datetime import date

from src.services.supabase_client import get_supabase_client

class NotificationService:
    def __init__(self):
        # Carregar configurações do Ambiente (Prioridade) ou Fallback para código
        base_url = os.getenv("EVOLUTION_API_URL", "https://fr-evolution.cloudfy.cloud")
        instance = os.getenv("EVOLUTION_INSTANCE", "whats-pessoal-luan")
        self.api_key = os.getenv("EVOLUTION_API_TOKEN", "HCpB8KZrD4GfzvApf8uYydMopc4XW9Qb")
        
        # Monta URL completa: {BASE}/message/sendText/{INSTANCE}
        base_url = base_url.rstrip("/")
        self.api_url = f"{base_url}/message/sendText/{instance}"
        
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
        
        return "5562981867784" # Fallback

    def send_signal_message(self, ticker, signal_type, option_data, exit_alert=None):
        """
        Formata e envia a mensagem do sinal via WhatsApp.
        :param exit_alert: Texto opcional com instrução de saída (gestão de carteira).
        """
        emoji = "🚀" if "ALTA" in signal_type else "🔻"
        direction = "COMPRA (CALL)" if "ALTA" in signal_type else "VENDA (PUT)"
        
        msg_date = date.today().strftime('%d/%m/%Y')
        header = f"*{emoji} NOVO SINAL DETECTADO: {ticker}*\n📅 {msg_date}"
        
        if exit_alert:
            header = f"🚨 *ATENÇÃO: GESTÃO DE CARTEIRA*\n{exit_alert}\n\n" + header

        if option_data:
            # Formatar valor monetário (se disponível)
            strike_fmt = f"R$ {option_data['strike']:.2f}"
            price_fmt = f"R$ {option_data.get('last_price', 0.0):.2f}"
            
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
        else:
            # Caso sem opções
            message_text = (
                f"{header}\n"
                f"📊 *Direção:* {signal_type}\n"
                f"⚠️ *Aviso:* Oportunidade identificada, mas nenhuma opção atendeu aos critérios de filtro (Delta 0.40 ou Liquidez).\n\n"
                f"_Acompanhe o ativo manualmente._"
            )
        
        return self._send_whatsapp(message_text)

    def send_error_alert(self, error_msg):
        """
        Envia alerta crítico de falha no sistema.
        """
        msg_date = date.today().strftime('%d/%m/%Y %H:%M')
        text = (
            f"🚨 *ERRO CRÍTICO NO ROBÔ* 🚨\n"
            f"📅 {msg_date}\n\n"
            f"⚠️ *Detalhe:* {error_msg}\n\n"
            f"_A execução foi interrompida. Verifique os logs._"
        )
        return self._send_whatsapp(text)

    def send_daily_summary(self, results):
        """
        Envia um relatório resumido com o status de TODOS os ativos analisados.
        :param results: Lista de dicts com o resultado de cada ativo.
        """
        if not results:
            return False
            
        lines = []
        lines.append("📊 *RELATÓRIO DE FECHAMENTO* 📊")
        lines.append(f"📅 {date.today().strftime('%d/%m/%Y')}\n")
        
        # Ordenar alfabeticamente
        sorted_results = sorted(results, key=lambda x: x['ticker'])
        
        for r in sorted_results:
            ticker = r['ticker']
            price = f"R$ {r['close']:.2f}"
            
            # Ícone baseado no Status
            if r['trend'] == 'UP':
                if r.get('signal'): # Virada de alta hoje
                    status = "🚀 *COMPRA (Novo)*"
                else: 
                    # Verifica proximidade
                    if r.get('is_proximity_warning'):
                        status = "⚠️ *ALERTA (Próximo Reversão)*"
                    else:
                        status = "🟢 Segue Tendência de Alta"
            else:
                if r.get('signal'): # Virada de baixa hoje
                    status = "🔻 *VENDA (Novo)*"
                else:
                    if r.get('is_proximity_warning'):
                        status = "⚠️ *ALERTA (Próximo Reversão)*"
                    else:
                        status = "🔴 Segue Tendência de Baixa"
            
            lines.append(f"*{ticker}* ({price}): {status}")
            
        lines.append(f"\n_Total monitorados: {len(results)}_")
        
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

if __name__ == "__main__":
    svc = NotificationService()
    svc._send_whatsapp("🤖 Teste de conexão: Trading Bot Ativo!")
