import sys
import os

# Adiciona o diretório raiz ao path para permitir imports absolutos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.notification_service import NotificationService

def teste_envio():
    print("🤖 Iniciando teste de notificação...")
    notifier = NotificationService()
    
    # Mock de dados para simular um sinal real
    ticker = "TESTE3"
    signal = "VIRADA PARA ALTA (Compra) [TESTE]"
    option_data = {
        "ticker": "TESTE123",
        "strike": 10.50,
        "dte": 30,
        "trades": 999
    }
    
    print(f"📨 Tentando enviar mensagem para {notifier.target_number}...")
    sucesso = notifier.send_signal_message(ticker, signal, option_data)
    
    if sucesso:
        print("\n✅ SUCESSO! Verifique seu WhatsApp.")
    else:
        print("\n❌ FALHA. Verifique os logs acima.")

if __name__ == "__main__":
    teste_envio()
