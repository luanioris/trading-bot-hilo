"""
Script de teste para inspecionar a estrutura completa da resposta do opcoes.net.br
e identificar o índice do Delta
"""
import requests
import json

BASE_URL = "https://opcoes.net.br/listaopcoes/completa"

def test_opcoes_net_structure():
    ticker = "SUZB3"  # Usando SUZB3 como exemplo
    
    # 1. Buscar vencimentos
    params = {
        "idAcao": ticker,
        "listarVencimentos": "true",
        "cotacoes": "true"
    }
    headers = { 
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "X-Requested-With": "XMLHttpRequest" 
    }
    
    print(f"🔍 Buscando vencimentos para {ticker}...")
    r = requests.get(BASE_URL, params=params, headers=headers, timeout=10)
    data = r.json()
    
    vencimentos = data.get('data', {}).get('vencimentos', [])
    if not vencimentos:
        print("❌ Nenhum vencimento encontrado")
        return
    
    primeiro_vencimento = vencimentos[0]['value']
    print(f"✅ Primeiro vencimento: {primeiro_vencimento}")
    
    # 2. Buscar opções desse vencimento
    params2 = {
        "idAcao": ticker,
        "listarVencimentos": "false",
        "cotacoes": "true",
        "vencimentos": primeiro_vencimento
    }
    
    print(f"\n🔍 Buscando opções para vencimento {primeiro_vencimento}...")
    r2 = requests.get(BASE_URL, params=params2, headers=headers)
    data2 = r2.json()
    
    opcoes = data2.get('data', {}).get('cotacoesOpcoes', [])
    
    if not opcoes:
        print("❌ Nenhuma opção encontrada")
        return
    
    print(f"✅ Encontradas {len(opcoes)} opções\n")
    
    # 3. Inspecionar a primeira opção (CALL)
    primeira_opcao = None
    for opt in opcoes:
        if opt[2] == "CALL":  # Tipo
            primeira_opcao = opt
            break
    
    if not primeira_opcao:
        print("❌ Nenhuma CALL encontrada")
        return
    
    print("=" * 80)
    print("📊 ESTRUTURA COMPLETA DA PRIMEIRA OPÇÃO (CALL):")
    print("=" * 80)
    
    for i, valor in enumerate(primeira_opcao):
        print(f"Índice {i:2d}: {valor} (Tipo: {type(valor).__name__})")
    
    print("\n" + "=" * 80)
    print("🎯 MAPEAMENTO CONHECIDO:")
    print("=" * 80)
    print(f"[0] Ticker: {primeira_opcao[0]}")
    print(f"[2] Tipo: {primeira_opcao[2]}")
    print(f"[5] Strike: {primeira_opcao[5]}")
    print(f"[8] Último Preço: {primeira_opcao[8]}")
    print(f"[9] Negócios: {primeira_opcao[9]}")
    
    # Procurar pelo Delta (geralmente um valor entre 0 e 1 para CALL)
    print("\n" + "=" * 80)
    print("🔎 PROCURANDO DELTA (valor entre 0.0 e 1.0):")
    print("=" * 80)
    
    for i, valor in enumerate(primeira_opcao):
        if isinstance(valor, (int, float)):
            if 0.0 <= float(valor) <= 1.0 and i not in [0, 2, 5, 8, 9]:
                print(f"✅ Possível Delta no índice [{i}]: {valor}")

if __name__ == "__main__":
    test_opcoes_net_structure()
