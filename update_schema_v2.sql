-- Tabela para guardar configurações do App (ex: Telefone)
CREATE TABLE IF NOT EXISTS app_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Inserir valor padrão do seu número (baseado no teste)
INSERT INTO app_config (key, value)
VALUES ('whatsapp_number', '5562981867784')
ON CONFLICT (key) DO NOTHING;

-- Tabela de Portfolio (Trade System)
CREATE TABLE IF NOT EXISTS portfolio (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Dados do Ativo
    ticker_asset TEXT NOT NULL,       -- Ex: PETR4
    ticker_option TEXT NOT NULL,      -- Ex: PETRM333
    type TEXT NOT NULL,               -- CALL ou PUT
    strike NUMERIC,
    expiration_date DATE,
    
    -- Dados da Operação
    operation_type TEXT DEFAULT 'COMPRA SEC', -- Compra a Seco, Trava, etc.
    entry_date DATE NOT NULL,
    entry_price NUMERIC NOT NULL,     -- Preço Pago (Premium)
    quantity INTEGER NOT NULL,
    
    -- Dados de Saída (Encerramento)
    exit_date DATE,
    exit_price NUMERIC,               -- Valor Recebido na venda
    result_value NUMERIC,             -- Lucro/Prejuízo R$
    result_percent NUMERIC,           -- Lucro/Prejuízo %
    
    status TEXT DEFAULT 'ABERTA',     -- ABERTA, ENCERRADA, EXERCIDA, PO
    notes TEXT
);

-- Criar índices para performance
CREATE INDEX IF NOT EXISTS idx_portfolio_status ON portfolio(status);
CREATE INDEX IF NOT EXISTS idx_portfolio_ticker ON portfolio(ticker_asset);
