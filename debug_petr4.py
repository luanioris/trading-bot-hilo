"""
Listar todos os vencimentos de PETR4 e inspecionar estrutura
"""
import requests
import json

BASE_URL = "https://opcoes.net.br/listaopcoes/completa"

def debug_petr4_expirations():
    ticker = "PETR4"
    
    print(f"🔍 Buscando vencimentos para {ticker}...")
    params = { "idAcao": ticker, "listarVencimentos": "true", "cotacoes": "true" }
    headers = { "User-Agent": "Mozilla/5.0", "X-Requested-With": "XMLHttpRequest" }
    
    r = requests.get(BASE_URL, params=params, headers=headers)
    vencimentos = r.json().get('data', {}).get('vencimentos', [])
    
    print(f"✅ Encontrados {len(vencimentos)} vencimentos.")
    for v in vencimentos:
        print(f"   - {v['value']} ({v['text']})")
        
    # Tentar pegar Jan 2025
    target = "2025-01-17"
    print(f"\n🔍 Buscando opções para {target}...")
    
    params2 = {
        "idAcao": ticker,
        "listarVencimentos": "false",
        "cotacoes": "true",
        "vencimentos": target
    }
    r2 = requests.get(BASE_URL, params=params2, headers=headers)
    opcoes = r2.json().get('data', {}).get('cotacoesOpcoes', [])
    
    if not opcoes:
        print("❌ Sem dados para Jan 2025")
        return
        
    # Procurar ATM
    # PETR4 ~36.00
    atm_opt = None
    for opt in opcoes:
        if opt[2] == "CALL":
            strike = float(opt[5])
            if 36 <= strike <= 37:
                atm_opt = opt
                break
                
    if atm_opt:
        print("\n📊 ESTRUTURA ATM (PETR4):")
        for i, val in enumerate(atm_opt):
            print(f"[{i}] {val}")
    else:
        print("❌ Nenhuma ATM encontrada")

if __name__ == "__main__":
    debug_petr4_expirations()
