import requests
import json

def test_opcoes_net_br():
    ticker = "PETR4"
    print(f"🕵️ Investigando API do Opcoes.net.br para {ticker}...")
    
    # URL que o site usa para carregar a grade (Descoberta via Network Tab do Chrome)
    # Normalmente é algo como: https://opcoes.net.br/listaopcoes/completa?idAcao=PETR4&listarVencimentos=true&cotacoes=true
    
    url = f"https://opcoes.net.br/listaopcoes/completa"
    
    params = {
        "idAcao": ticker,
        "listarVencimentos": "true",
        "cotacoes": "true"
    }
    
    # Headers são cruciais para não ser bloqueado (fingir ser um navegador)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Referer": f"https://opcoes.net.br/opcoes/bovespa/{ticker}",
        "X-Requested-With": "XMLHttpRequest"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Analisar estrutura
            # Geralmente retorna: { "cotacoesOpcoes": [ ... ] }
            
            opcoes = data.get('data', {}).get('cotacoesOpcoes', [])
            
            if not opcoes:
                 # Tentar outra chave se a estrutura mudou
                 print(f"⚠️ JSON retornado, mas lista vazia. Chaves raiz: {data.keys()}")
                 return

            print(f"✅ SUCESSO! Encontradas {len(opcoes)} opções.")
            
            # Mostrar exemplo
            first = opcoes[0]
            # Mapear campos (eles usam codigos tipo 'A' = Ticker, 'B' = Strike, etc)
            print(f"🔍 Exemplo de Opção (Dados Brutos): {str(first)[:200]}...")
            
        else:
            print(f"❌ Falha: Status Code {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")

if __name__ == "__main__":
    test_opcoes_net_br()
