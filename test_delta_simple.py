"""
Script de teste simplificado para validar a extração de Delta
"""
import requests
import pandas as pd

BASE_URL = "https://opcoes.net.br/listaopcoes/completa"

def test_delta_simple():
    ticker = "SUZB3"
    
    print("=" * 80)
    print(f"🧪 TESTE SIMPLIFICADO: Extração de Delta para {ticker}")
    print("=" * 80)
    
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
    
    r = requests.get(BASE_URL, params=params, headers=headers, timeout=10)
    data = r.json()
    
    vencimentos = data.get('data', {}).get('vencimentos', [])
    primeiro_vencimento = vencimentos[0]['value']
    
    # 2. Buscar opções
    params2 = {
        "idAcao": ticker,
        "listarVencimentos": "false",
        "cotacoes": "true",
        "vencimentos": primeiro_vencimento
    }
    
    r2 = requests.get(BASE_URL, params=params2, headers=headers)
    data2 = r2.json()
    opcoes = data2.get('data', {}).get('cotacoesOpcoes', [])
    
    # 3. Processar opções (igual ao OpcoesNetClient)
    clean = []
    for item in opcoes:
        delta_value = None
        try:
            if len(item) > 7 and item[7] is not None:
                delta_value = float(item[7])
        except (ValueError, TypeError):
            delta_value = None
        
        clean.append({
            "stock": item[0].split('_')[0],
            "type": item[2],
            "strike": float(item[5]) if item[5] is not None else 0.0,
            "delta": delta_value,
            "trades": int(item[9]) if len(item) > 9 and item[9] is not None else 0
        })
    
    # 4. Filtrar CALLs com Delta
    df = pd.DataFrame(clean)
    calls = df[df['type'] == 'CALL'].copy()
    calls_with_delta = calls[calls['delta'].notna()]
    
    print(f"\n✅ Total de opções: {len(clean)}")
    print(f"✅ CALLs: {len(calls)}")
    print(f"✅ CALLs com Delta: {len(calls_with_delta)}")
    
    # Mostrar distribuição de Deltas
    if len(calls_with_delta) > 0:
        print(f"\n📊 DISTRIBUIÇÃO DE DELTAS (CALLs):")
        print(f"   Mínimo: {calls_with_delta['delta'].min():.3f}")
        print(f"   Máximo: {calls_with_delta['delta'].max():.3f}")
        print(f"   Média: {calls_with_delta['delta'].mean():.3f}")
        
        # Mostrar todas as opções ordenadas por Delta
        print(f"\n📋 TODAS AS CALLs (ordenadas por Delta):")
        print("-" * 80)
        print(f"{'Ticker':<15} {'Strike':>8} {'Delta':>8} {'Trades':>8}")
        print("-" * 80)
        
        calls_sorted = calls_with_delta.sort_values('delta', ascending=False)
        for _, row in calls_sorted.iterrows():
            print(f"{row['stock']:<15} {row['strike']:>8.2f} {row['delta']:>8.3f} {row['trades']:>8}")
    
    # 5. Filtrar Delta 0.42-0.50
    filtered = calls_with_delta[(calls_with_delta['delta'] >= 0.42) & (calls_with_delta['delta'] <= 0.50)]
    
    print(f"\n🎯 CALLs no range Delta 0.42-0.50: {len(filtered)}")
    
    if len(filtered) > 0:
        # Ordenar por proximidade ao Delta 0.42, depois liquidez
        filtered['dist_to_042'] = abs(filtered['delta'] - 0.42)
        filtered = filtered.sort_values(by=['dist_to_042', 'trades'], ascending=[True, False])
        
        print("\n📊 TOP 5 OPÇÕES (ordenadas por Delta ~0.42 + Liquidez):")
        print("-" * 80)
        print(f"{'Ticker':<15} {'Strike':>8} {'Delta':>8} {'Trades':>8} {'Dist 0.42':>10}")
        print("-" * 80)
        
        for _, row in filtered.head(5).iterrows():
            print(f"{row['stock']:<15} {row['strike']:>8.2f} {row['delta']:>8.3f} {row['trades']:>8} {row['dist_to_042']:>10.3f}")
        
        best = filtered.iloc[0]
        print("\n" + "=" * 80)
        print("🏆 MELHOR OPÇÃO SELECIONADA:")
        print("=" * 80)
        print(f"   Ticker: {best['stock']}")
        print(f"   Strike: R$ {best['strike']:.2f}")
        print(f"   Delta: {best['delta']:.3f}")
        print(f"   Liquidez: {best['trades']} negócios")
        print(f"   Distância do alvo (0.42): {best['dist_to_042']:.3f}")
    
    print("\n" + "=" * 80)
    print("✅ TESTE CONCLUÍDO!")
    print("=" * 80)

if __name__ == "__main__":
    test_delta_simple()
