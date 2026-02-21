-- ============================================================================
-- Migration: Multi-message + Audio refactor + Scheduling
-- Run this in Supabase SQL Editor for existing databases
-- ============================================================================

-- New column in cupido_orders: track how many messages have been sent
ALTER TABLE cupido_orders ADD COLUMN IF NOT EXISTS messages_sent INT DEFAULT 0;

-- New columns in cupido_messages
ALTER TABLE cupido_messages ADD COLUMN IF NOT EXISTS audio_text TEXT;
ALTER TABLE cupido_messages ADD COLUMN IF NOT EXISTS scheduled_at TIMESTAMPTZ;
ALTER TABLE cupido_messages ADD COLUMN IF NOT EXISTS delivered BOOLEAN DEFAULT FALSE;

-- Mark all existing messages as delivered (they were already sent)
UPDATE cupido_messages SET delivered = TRUE WHERE delivered IS NULL OR delivered = FALSE;

-- Update messages_sent count for existing orders based on actual message count
UPDATE cupido_orders o
SET messages_sent = (
    SELECT COUNT(*) FROM cupido_messages m WHERE m.order_id = o.id
)
WHERE o.status IN ('submitted', 'delivered');

-- Index for scheduled message lookups
CREATE INDEX IF NOT EXISTS idx_cupido_messages_scheduled
ON cupido_messages(scheduled_at)
WHERE delivered = FALSE AND scheduled_at IS NOT NULL;
