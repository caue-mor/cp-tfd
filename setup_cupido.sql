-- ============================================================================
-- Cupido - Database Setup (Supabase)
-- Execute this in Supabase SQL Editor to create the tables
-- ============================================================================

-- Orders table
CREATE TABLE IF NOT EXISTS cupido_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sale_id TEXT UNIQUE,
    plan TEXT NOT NULL CHECK (plan IN ('basico','com_audio','multi_mensagem','premium_historia')),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','approved','submitted','delivered','refunded','canceled')),
    buyer_name TEXT,
    buyer_phone TEXT NOT NULL,
    buyer_email TEXT,
    product_name TEXT,
    recipient_phone TEXT,
    form_token UUID UNIQUE DEFAULT gen_random_uuid(),
    is_test BOOLEAN DEFAULT FALSE,
    messages_sent INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    delivered_at TIMESTAMPTZ
);

-- Messages table
CREATE TABLE IF NOT EXISTS cupido_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID REFERENCES cupido_orders(id) ON DELETE CASCADE,
    message_index INT DEFAULT 0,
    content TEXT NOT NULL,
    audio_url TEXT,
    audio_text TEXT,
    sender_nickname TEXT,
    scheduled_at TIMESTAMPTZ,
    delivered BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Presentations table (premium plan)
CREATE TABLE IF NOT EXISTS cupido_presentations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID REFERENCES cupido_orders(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    slides JSONB NOT NULL DEFAULT '[]',
    view_count INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Migration: Multi-message + Audio refactor + Scheduling ──────────
-- Run these ALTER TABLEs if tables already exist:
-- ALTER TABLE cupido_orders ADD COLUMN IF NOT EXISTS messages_sent INT DEFAULT 0;
-- ALTER TABLE cupido_messages ADD COLUMN IF NOT EXISTS audio_text TEXT;
-- ALTER TABLE cupido_messages ADD COLUMN IF NOT EXISTS scheduled_at TIMESTAMPTZ;
-- ALTER TABLE cupido_messages ADD COLUMN IF NOT EXISTS delivered BOOLEAN DEFAULT FALSE;

-- Indexes
CREATE INDEX IF NOT EXISTS idx_cupido_orders_form_token ON cupido_orders(form_token);
CREATE INDEX IF NOT EXISTS idx_cupido_orders_sale_id ON cupido_orders(sale_id);
CREATE INDEX IF NOT EXISTS idx_cupido_orders_status ON cupido_orders(status);
CREATE INDEX IF NOT EXISTS idx_cupido_messages_order_id ON cupido_messages(order_id);
CREATE INDEX IF NOT EXISTS idx_cupido_presentations_order_id ON cupido_presentations(order_id);

-- Enable RLS (Row Level Security)
ALTER TABLE cupido_orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE cupido_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE cupido_presentations ENABLE ROW LEVEL SECURITY;

-- Policies: allow service role full access
CREATE POLICY "Service role full access" ON cupido_orders FOR ALL USING (true);
CREATE POLICY "Service role full access" ON cupido_messages FOR ALL USING (true);
CREATE POLICY "Service role full access" ON cupido_presentations FOR ALL USING (true);

-- Public read for presentations (needed for slideshow viewer)
CREATE POLICY "Public read presentations" ON cupido_presentations FOR SELECT USING (true);

-- ============================================================================
-- Storage Bucket: cupido-assets (create via Supabase Dashboard)
-- Settings: Public bucket, allowed MIME types: image/*, audio/*
-- ============================================================================
