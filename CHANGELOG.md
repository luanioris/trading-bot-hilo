# 🔧 Changelog - Correções Críticas

## [08/12/2024] - Correção de Dados em Tempo Real

### Corrigido
- **Candle Intraday:** O sistema agora busca o candle do dia atual (em formação) durante o pregão, permitindo análise em tempo real às 17:10.
- **GitHub Actions Cron:** Commit de ativação para garantir que o agendamento automático funcione após mudança de visibilidade do repositório.

### Detalhes Técnicos
- Modificado `BrapiClient.get_historical_data()` para incluir parâmetro `include_today=True`
- Quando ativado, faz uma segunda chamada à API buscando `range=1d` e concatena o candle atual ao histórico
- Evita duplicação verificando timestamps

### Próximos Passos
- Monitorar execução automática de segunda-feira (09/12) às 17:10
- Validar que os dados refletem o fechamento do dia
