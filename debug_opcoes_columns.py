"""
Script de debug para mapear colunas do opcoes.net.br usando vencimento MENSAL (Jan 2025)
"""
import requests
import json

BASE_URL = "https://opcoes.net.br/listaopcoes/completa"

def debug_jan_2025_structure():
    ticker = "SUZB3"
    expiration_jan_25 = "2025-01-17"  # Vencimento provável Série A (3ª sexta)
    # Ou buscar dinamicamente
    
    print(f"🔍 Buscando opções JAN 2025 para {ticker}...")
    
    # 1. Buscar vencimentos para confirmar a data
    params = { "idAcao": ticker, "listarVencimentos": "true", "cotacoes": "true" }
    headers = { "User-Agent": "Mozilla/5.0", "X-Requested-With": "XMLHttpRequest" }
    r = requests.get(BASE_URL, params=params, headers=headers)
    vencimentos = r.json().get('data', {}).get('vencimentos', [])
    
    target_venc = None
    for v in vencimentos:
        # Procurar vencimento em Jan 2025
        if "2025-01" in v['value']:
            target_venc = v['value']
            print(f"✅ Vencimento Jan 2025 encontrado: {target_venc}")
            break
            
    if not target_venc:
        print("❌ Vencimento Jan 2025 não encontrado. Usando primeiro disp.")
        target_venc = vencimentos[0]['value']

    # 2. Buscar opções
    params2 = {
        "idAcao": ticker,
        "listarVencimentos": "false",
        "cotacoes": "true",
        "vencimentos": target_venc
    }
    r2 = requests.get(BASE_URL, params=params2, headers=headers)
    opcoes = r2.json().get('data', {}).get('cotacoesOpcoes', [])
    
    if not opcoes:
        print("❌ Nenhuma opção encontrada.")
        return

    # 3. Pegar uma ATM, uma ITM profunda e uma OTM profunda para comparar
    # SUZB3 aprox 51.67
    
    atm_opt = None # Perto de 51-52
    itm_opt = None # Perto de 40-45 (Delta deve ser alto, perto de 1)
    otm_opt = None # Perto de 60+ (Delta deve ser baixo, perto de 0)
    
    for opt in opcoes:
        if opt[2] != "CALL": continue
        try:
            strike = float(opt[5])
            if 51 <= strike <= 52 and not atm_opt: atm_opt = opt
            if 40 <= strike <= 42 and not itm_opt: itm_opt = opt
            if 60 <= strike <= 62 and not otm_opt: otm_opt = opt
        except: pass
        
    print("\n📊 COMPARAÇÃO DE COLUNAS (CALLs):")
    print(f"{'IDX':<3} {'ITM (Str ~41)':<20} {'ATM (Str ~51.5)':<20} {'OTM (Str ~61)':<20}")
    print("-" * 70)
    
    # Imprimir lado a lado para identificar pattern
    # Delta deve descer: ITM (~0.9) -> ATM (~0.5) -> OTM (~0.1)
    
    max_len = max(len(itm_opt or []), len(atm_opt or []), len(otm_opt or []))
    
    for i in range(max_len):
        v_itm = itm_opt[i] if itm_opt and i < len(itm_opt) else "-"
        v_atm = atm_opt[i] if atm_opt and i < len(atm_opt) else "-"
        v_otm = otm_opt[i] if otm_opt and i < len(otm_opt) else "-"
        print(f"{i:<3} {str(v_itm):<20} {str(v_atm):<20} {str(v_otm):<20}")

if __name__ == "__main__":
    debug_jan_2025_structure()
