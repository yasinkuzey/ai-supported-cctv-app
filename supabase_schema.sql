-- ============================================
-- SUPABASE DATABASE SCHEMA
-- AI-Supported CCTV Application
-- ============================================
-- Bu SQL'i Supabase Dashboard > SQL Editor'da çalıştırın.

-- ============ SETTINGS TABLE ============
-- Sistem ayarları (anomali türleri vb.)
CREATE TABLE IF NOT EXISTS settings (
    id SERIAL PRIMARY KEY,
    anomalies_to_watch TEXT NOT NULL DEFAULT 'Yangın, Hırsız, Yerde yatan insan, Şüpheli hareket'
);

-- Başlangıç ayarlarını ekle
INSERT INTO settings (anomalies_to_watch) 
VALUES ('Yangın, Hırsız, Yerde yatan insan, Şüpheli hareket')
ON CONFLICT DO NOTHING;


-- ============ EMAIL LIST TABLE ============
-- Anomali bildirim alıcıları
CREATE TABLE IF NOT EXISTS email_list (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);


-- ============ LOGS TABLE ============
-- Analiz sonuçları ve fotoğraf referansları
CREATE TABLE IF NOT EXISTS logs (
    id SERIAL PRIMARY KEY,
    is_anomaly BOOLEAN NOT NULL DEFAULT FALSE,
    reason TEXT NOT NULL,
    diff_percentage FLOAT NOT NULL DEFAULT 0.0,
    image_url TEXT,
    image_path TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
