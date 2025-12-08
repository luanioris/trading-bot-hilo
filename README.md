# 🤖 Trading Bot B3 - HiLo System

## 📋 Resumo do Projeto
Este é um sistema autônomo de Trading Quantitativo focado no mercado brasileiro (B3). Ele utiliza o indicador técnico **HiLo Activator** para identificar tendências em ativos (Ações) e sugere automaticamente operações estruturadas com **Opções** (Calls e Puts) para maximizar lucros.

O sistema opera na nuvem, realiza varreduras periódicas, notifica sinais via WhatsApp e possui um Dashboard completo para gestão de carteira.

---

## 🏗️ Arquitetura e Tecnologias
O projeto é construído sobre uma pilha moderna e robusta:

*   **Linguagem:** Python 3.10+
*   **Interface (Frontend):** Streamlit (Cloud)
*   **Banco de Dados:** Supabase (PostgreSQL)
*   **Dados de Mercado:**
    *   *Brapi.dev* (Cotações de Ações)
    *   *Opcoes.net.br* (Cadeia de Opções e Greeks)
*   **Notificações:** Evolution API (WhatsApp Gateway)
*   **Automação (Cron):** GitHub Actions (Scanner agendado)
*   **Hospedagem:** Streamlit Cloud + GitHub

---

## ✅ Funcionalidades Implementadas (Fase 1 - Core)

### 🧠 Cérebro (Scanner & Lógica)
- [x] **Cálculo HiLo Dinâmico:** Identifica reversões de tendência (Alta/Baixa) com período ajustável (padrão 10).
- [x] **Seletor de Opções Inteligente:** Filtra opções por liquidez, Delta (0.3-0.7) e vencimento ideal.
- [x] **Gestão de Sinais:** Evita duplicidade de sinais no mesmo dia.
- [x] **Boletim Diário:** Envia resumo de fechamento de mercado com status de todos os ativos monitorados.

### 📱 Comunicação (WhatsApp)
- [x] **Alerta de Oportunidade:** Envia "Foguete" 🚀 ou "Venda" 🔻 com todos os dados da opção (Strike, Vencimento, Código).
- [x] **Alerta de Lucro:** Monitora carteira e avisa quando uma opção atinge a Meta de Lucro (ex: 50%).
- [x] **Alerta de Inversão:** Avisa se o mercado virou contra uma posição aberta (Stop/Gestão).

### 💻 Dashboard (Painel de Controle)
- [x] **Monitoramento de Carteira:** Tabela de custódia com cálculo de resultado em tempo real.
- [x] **Simulador de Saída:** Calculadora projetiva para ajudar na tomada de decisão de venda.
- [x] **Gestão de Sinais:** Visualização e exclusão de sinais do dia.
- [x] **Controle do Robô:** Botão para ativar/pausar a automação e execução manual.
- [x] **Gestão de Ativos:** Adicionar/Remover ativos monitorados com busca automática de Nome/Setor.
- [x] **Segurança:** Sistema de Login Simples para proteção na nuvem.

### ☁️ Infraestrutura
- [x] **Agendamento Automático:** Robô roda sozinho de Seg-Sex às 17:10 (Fechamento).
- [x] **Persistência de Config:** Configurações de usuário salvas e sincronizadas (JSON/Secrets).

---

## 🛣️ Roadmap e Próximos Passos

### 🔜 Fase 2: Inteligência e Analytics (O Próximo Grande Passo)
O foco agora muda de "Execução" para **"Análise de Performance"**.
- [ ] **Dashboard de Relatórios:**
    - Gráfico de Evolução de Patrimônio.
    - Taxa de Acerto (Win Rate) do Robô.
    - Lucro Médio por Operação vs Prejuízo Médio.
    - Tabela de Performance por Ativo (ex: "PETR4 dá mais lucro que VALE3?").
- [ ] **Backtesting Simples:** Rodar o setup HiLo no passado para validar parâmetros.

### 🔮 Fase 3: Expansão
- [ ] **Multi-Estratégia:** Adicionar suporte a IFR (RSI) e Bandas de Bollinger.
- [ ] **Multi-Usuário:** Suportar múltiplos números de WhatsApp e carteiras separadas.
- [ ] **Integração Corretora:** (Futuro distante) Envio de ordens reais via API da corretora.

---

## 🚀 Como Rodar o Projeto

### 1. Instalação Local
```bash
git clone https://github.com/SEU_USER/trading-bot-hilo.git
cd trading-bot-hilo
pip install -r requirements.txt
streamlit run dashboard.py
```

### 2. Configuração (.env)
Crie um arquivo `.env` na raiz com:
```ini
SUPABASE_URL="seu_url"
SUPABASE_KEY="sua_chave"
BRAPI_TOKEN="seu_token"
EVOLUTION_API_URL="https://api..."
EVOLUTION_INSTANCE="sua_instancia"
EVOLUTION_API_TOKEN="seu_token"
APP_PASSWORD="sua_senha_local"
```

### 3. Deploy na Nuvem
1. Suba o código no GitHub.
2. Conecte ao **Streamlit Cloud**.
3. Configure os **Secrets** (mesmas chaves do .env) no painel do Streamlit.
4. Configure os **Secrets** no GitHub Actions para o robô funcionar.

---
*Desenvolvido com 🤖 por Luan Ioris & Antigravity AI*
