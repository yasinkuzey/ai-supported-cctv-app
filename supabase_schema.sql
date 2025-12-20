-- ============================================
-- SUPABASE DATABASE SCHEMA
-- AI-Supported CCTV Application
-- ============================================

-- ============ SETTINGS TABLE ============
CREATE TABLE IF NOT EXISTS settings (
    id SERIAL PRIMARY KEY,
    anomalies_to_watch TEXT NOT NULL DEFAULT 'Yangın, Hırsız, Yerde yatan insan, Şüpheli hareket'
);

INSERT INTO settings (anomalies_to_watch) 
VALUES ('Yangın, Hırsız, Yerde yatan insan, Şüpheli hareket')
ON CONFLICT DO NOTHING;


-- ============ EMAIL LIST TABLE ============
CREATE TABLE IF NOT EXISTS email_list (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);


-- ============ LOGS TABLE ============
CREATE TABLE IF NOT EXISTS logs (
    id SERIAL PRIMARY KEY,
    is_anomaly BOOLEAN NOT NULL DEFAULT FALSE,
    reason TEXT NOT NULL,
    diff_percentage FLOAT NOT NULL DEFAULT 0.0,
    image_url TEXT,
    previous_image_url TEXT,  -- Yeni kolon: Karşılaştırma için
    image_path TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Eğer tablo zaten varsa bu kolonu eklemek için:
-- ALTER TABLE logs ADD COLUMN previous_image_url TEXT;
