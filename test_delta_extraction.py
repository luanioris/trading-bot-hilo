"""
Script de teste para validar a extração de Delta do opcoes.net.br
"""
import sys
sys.path.append('.')

from src.services.brapi import BrapiClient

def test_delta_extraction():
    print("=" * 80)
    print("🧪 TESTE: Extração de Delta do opcoes.net.br")
    print("=" * 80)
    
    client = BrapiClient()
    ticker = "SUZB3"
    
    print(f"\n1️⃣ Buscando cotação de {ticker}...")
    quotes = client.get_quotes([ticker])
    price = quotes.get(ticker)
    print(f"   ✅ Preço atual: R$ {price:.2f}")
    
    print(f"\n2️⃣ Buscando cadeia de opções...")
    options = client.get_options_chain(ticker)
    print(f"   ✅ Encontradas {len(options)} opções")
    
    print(f"\n3️⃣ Verificando campo Delta...")
    
    # Filtrar CALLs com Delta disponível
    calls_with_delta = [opt for opt in options if opt['type'] == 'CALL' and opt.get('delta') is not None]
    
    if not calls_with_delta:
        print("   ❌ ERRO: Nenhuma CALL com Delta encontrada!")
        return False
    
    print(f"   ✅ {len(calls_with_delta)} CALLs com Delta disponível")
    
    print(f"\n4️⃣ Exibindo primeiras 5 CALLs com Delta:")
    print("   " + "-" * 76)
    print(f"   {'Ticker':<15} {'Strike':>8} {'Delta':>8} {'Trades':>8} {'Último':>10}")
    print("   " + "-" * 76)
    
    for opt in calls_with_delta[:5]:
        print(f"   {opt['stock']:<15} {opt['strike']:>8.2f} {opt['delta']:>8.3f} {opt['trades']:>8} {opt['lastPrice']:>10.2f}")
    
    print("\n5️⃣ Testando filtro Delta 0.42-0.50...")
    filtered = [opt for opt in calls_with_delta if 0.42 <= opt['delta'] <= 0.50]
    
    if not filtered:
        print("   ⚠️ Nenhuma CALL no range Delta 0.42-0.50")
    else:
        print(f"   ✅ {len(filtered)} CALLs no range Delta 0.42-0.50")
        
        # Ordenar por proximidade ao Delta 0.42, depois liquidez
        filtered_sorted = sorted(
            filtered,
            key=lambda x: (abs(x['delta'] - 0.42), -x['trades'])
        )
        
        best = filtered_sorted[0]
        print(f"\n   🎯 MELHOR OPÇÃO:")
        print(f"      Ticker: {best['stock']}")
        print(f"      Strike: R$ {best['strike']:.2f}")
        print(f"      Delta: {best['delta']:.3f}")
        print(f"      Liquidez: {best['trades']} negócios")
        print(f"      Último: R$ {best['lastPrice']:.2f}")
    
    print("\n" + "=" * 80)
    print("✅ TESTE CONCLUÍDO COM SUCESSO!")
    print("=" * 80)
    return True

if __name__ == "__main__":
    test_delta_extraction()
