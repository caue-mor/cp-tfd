-- ============================================================
-- Teste de Fidelidade — Setup Supabase
-- ============================================================

-- 1. Tabela de usuarios
CREATE TABLE IF NOT EXISTS fidelidade_users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    nome TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    telefone TEXT NOT NULL,
    senha_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 2. Tabela de testes
CREATE TABLE IF NOT EXISTS fidelidade_tests (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES fidelidade_users(id) NOT NULL,
    target_phone TEXT NOT NULL,
    first_message TEXT NOT NULL,
    status TEXT DEFAULT 'pending',  -- pending | active | expired
    sale_id TEXT,
    paid_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 3. Tabela de mensagens
CREATE TABLE IF NOT EXISTS fidelidade_messages (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    test_id UUID REFERENCES fidelidade_tests(id) NOT NULL,
    direction TEXT NOT NULL,  -- 'outbound' (mulher->alvo) | 'inbound' (alvo->mulher)
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Indices para performance
CREATE INDEX IF NOT EXISTS idx_fidelidade_tests_user_id ON fidelidade_tests(user_id);
CREATE INDEX IF NOT EXISTS idx_fidelidade_tests_target_phone ON fidelidade_tests(target_phone);
CREATE INDEX IF NOT EXISTS idx_fidelidade_tests_status ON fidelidade_tests(status);
CREATE INDEX IF NOT EXISTS idx_fidelidade_messages_test_id ON fidelidade_messages(test_id);
CREATE INDEX IF NOT EXISTS idx_fidelidade_users_email ON fidelidade_users(email);

-- RLS (Row Level Security) — desabilitado para acesso via service_role key
-- Se quiser habilitar depois:
-- ALTER TABLE fidelidade_users ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE fidelidade_tests ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE fidelidade_messages ENABLE ROW LEVEL SECURITY;
