# 🎥 AI-Supported CCTV Application

Raspberry Pi ile çalışan AI destekli güvenlik kamerası.

## Özellikler
- Gemini AI ile anomali tespiti (yangın, hırsız vb.)
- Her 10 sn'de fotoğraf çekimi
- Fotoğraflar arası fark analizi
- Anomali durumunda email bildirimi

## Kurulum

### 1. Supabase
1. [supabase.com](https://supabase.com) → New Project
2. SQL Editor'da `supabase_schema.sql` çalıştır
3. Storage → New bucket → `cctv-photos`

### 2. Render
1. GitHub'a push et
2. [render.com](https://render.com) → New → Web Service
3. Environment variables ekle (`.env.example`'a bak)

## API

```
GET  /health                     → Health check
POST /auth/login?username=x&password=y → Giriş
GET  /settings?username=x&password=y   → Ayarlar
PUT  /settings?username=x&password=y&anomalies_to_watch=... → Ayar güncelle
GET  /email-list?username=x&password=y → Mail listesi
POST /email-list?username=x&password=y&email=... → Mail ekle
DELETE /email-list/{id}?username=x&password=y → Mail sil
GET  /logs?username=x&password=y → Loglar
GET  /stats?username=x&password=y → İstatistikler
POST /upload (file) → Fotoğraf yükle (Raspberry)
```

## Dosyalar
```
├── main.py              # Tüm backend kodu
├── requirements.txt     # Bağımlılıklar
├── render.yaml          # Render config
├── supabase_schema.sql  # Database
└── .env.example         # Örnek env
```
