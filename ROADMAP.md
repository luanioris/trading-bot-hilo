# Roadmap de Implementação: Trading Bot B3 (HiLo + Opções)

Este documento descreve o plano de desenvolvimento para o bot de swing trade na B3.

## 1. Visão Geral
Bot em Python para monitorar ativos da B3, detectar viradas de tendência via HiLo Activator (10 períodos) e sugerir compra de opções (Call/Put) ATM com vencimento em 30-40 dias.

## 2. Fases de Desenvolvimento

### Fase 1: Fundação & Conectividade (Atual)
- [x] Definição de Stack e Estrutura.
- [ ] Configuração do Ambiente Python (requirements.txt, .env).
- [ ] **Módulo Brapi**: Cliente para buscar cotações históricas e cadeia de opções.
- [ ] **Módulo Supabase**: Cliente para conexão e setup inicial do Banco de Dados.
- [ ] Teste de Conectividade: Script para validar acesso às APIs.

### Fase 2: Core Analítico (Engine)
- [ ] **Implementação do HiLo**: Usar `pandas-ta` ou implementação customizada do HiLo Activator (10).
- [ ] **Scanner de Ativos**: Lista de tickers para monitorar (ex: IBOV ou lista fixa).
- [ ] **Detector de Sinais**: Lógica que compara `Preço vs HiLo` e identifica cruzamentos (Dia D vs D-1).

### Fase 3: Seletor de Opções (Intelligence)
- [ ] **Filtro de Vencimento**: Algoritmo para selecionar vencimentos entre 30 e 40 dias úteis/corridos.
- [ ] **Filtro ATM**: Selecionar strike mais próximo do preço atual do ativo (Spot).
- [ ] **Filtro de Liquidez**: (Opcional V1) Evitar opções sem negócios.

### Fase 4: Persistência & Execução
- [ ] **Schema do Banco**: Tabelas `assets`, `market_data_daily`, `signals`, `options_opportunities`.
- [ ] **Pipeline de Execução**: Script `run_daily.py` que orquestra: Download -> Análise -> Seleção Opção -> Salvar no DB.

### Fase 5: Infraestrutura & Automação
- [ ] **GitHub Actions**: Configurar cronjob para rodar todo dia útil as 17:30.
- [ ] **Front/Dashboard** (Futuro): Interface Vercel para visualizar os sinais gerados.

## 3. Stack Tecnológica
- **Linguagem**: Python 3.9+
- **Dados**: Brapi.dev API
- **Database**: Supabase (PostgreSQL)
- **Libs Principais**: `pandas`, `pandas-ta`, `supabase`, `requests`, `python-dotenv`

## 4. Notas Técnicas
- **Brapi Token**: Necessário adicionar ao `.env`.
- **Supabase URL/Key**: Necessário adicionar ao `.env`.
- **HiLo Logic**: 
    - HiLo Top (Stop de Venda) = Média das Máximas (X períodos).
    - HiLo Bottom (Stop de Compra) = Média das Mínimas (X períodos).
    - Se Fechamento > HiLo Top anterior -> Tendência ALTA (Hilo Bottom passa a ser desenhado).
