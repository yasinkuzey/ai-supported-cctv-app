# main.py
import os
import io
import json
import smtplib
import hashlib
from email.message import EmailMessage
from datetime import datetime, timedelta
import math

from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client
import google.generativeai as genai
from PIL import Image
import numpy as np

# ============ CONFIG ============
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
STORAGE_BUCKET = "cctv-photos"

# ============ INIT ============
app = FastAPI(title="CCTV Backend")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
genai.configure(api_key=GEMINI_API_KEY)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ AUTH CHECK ============
def check_auth(username: str, password: str):
    """Basit auth kontrolü - env'deki değerlerle karşılaştır."""
    if username != ADMIN_USERNAME or password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Hatalı kullanıcı adı veya şifre")
    return True



# ============ HELPERS ============
def calculate_image_diff(current_img, last_image_path):
    """İki resim arasındaki fark yüzdesini hesapla."""
    if not last_image_path:
        return 0.0
    
    try:
        response = supabase.storage.from_(STORAGE_BUCKET).download(last_image_path)
        last_img = Image.open(io.BytesIO(response)).convert('RGB')
        
        size = (320, 240)
        current_resized = current_img.resize(size)
        last_resized = last_img.resize(size)
        
        current_array = np.array(current_resized, dtype=np.float32)
        last_array = np.array(last_resized, dtype=np.float32)
        
        diff = np.abs(current_array - last_array)
        percentage = (np.mean(diff) / 255.0) * 100
        return float(round(percentage, 2))
    except:
        return 0.0


def analyze_with_gemini(image, anomalies_to_watch):
    """Gemini ile görüntü analizi."""
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""Sen bir güvenlik kamerası analiz asistanısın.
Görüntüyü analiz et ve şu riskleri kontrol et: "{anomalies_to_watch}"

Sadece JSON döndür:
{{"is_anomaly": true/false, "reason": "kısa açıklama"}}"""

    try:
        response = model.generate_content([prompt, image])
        text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(text)
    except:
        return {"is_anomaly": False, "reason": "Analiz hatası"}


def send_alert_email(reason, image_url):
    """Anomali mail'i gönder."""
    try:
        recipients = supabase.table('email_list').select("email").execute()
        if not recipients.data:
            return
        
        msg = EmailMessage()
        msg['Subject'] = '⚠️ GÜVENLİK UYARISI'
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = ", ".join([r['email'] for r in recipients.data])
        msg.set_content(f"""
Anomali tespit edildi!

Sebep: {reason}
Zaman: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
Görüntü: {image_url or 'Yok'}
        """)
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
    except Exception as e:
        print(f"Mail hatası: {e}")


# ============ ENDPOINTS ============

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/auth/login")
async def login(username: str, password: str):
    """Basit login - 200 dönerse başarılı."""
    check_auth(username, password)
    return {"status": "ok", "message": "Giriş başarılı"}


@app.get("/settings")
async def get_settings(username: str, password: str):
    """Anomali ayarlarını getir."""
    check_auth(username, password)
    result = supabase.table('settings').select("*").limit(1).execute()
    return result.data[0] if result.data else {}


@app.put("/settings")
async def update_settings(username: str, password: str, anomalies_to_watch: str):
    """Anomali ayarlarını güncelle."""
    check_auth(username, password)
    result = supabase.table('settings').update({
        'anomalies_to_watch': anomalies_to_watch
    }).eq('id', 1).execute()
    return result.data[0] if result.data else {}


@app.get("/email-list")
async def get_email_list(username: str, password: str):
    """Mail listesini getir."""
    check_auth(username, password)
    result = supabase.table('email_list').select("*").execute()
    return result.data


@app.post("/email-list")
async def add_email(username: str, password: str, email: str, name: str = None):
    """Mail ekle."""
    check_auth(username, password)
    result = supabase.table('email_list').insert({
        'email': email,
        'name': name
    }).execute()
    return result.data[0] if result.data else {}


@app.delete("/email-list/{id}")
async def delete_email(id: int, username: str, password: str):
    """Mail sil."""
    check_auth(username, password)
    supabase.table('email_list').delete().eq('id', id).execute()
    return {"status": "ok"}


@app.get("/logs")
async def get_logs(
    username: str, 
    password: str,
    page: int = 1,
    per_page: int = 20,
    is_anomaly: bool = None
):
    """Logları getir."""
    check_auth(username, password)
    
    query = supabase.table('logs').select("*", count='exact')
    if is_anomaly is not None:
        query = query.eq('is_anomaly', is_anomaly)
    
    offset = (page - 1) * per_page
    result = query.order('created_at', desc=True).range(offset, offset + per_page - 1).execute()
    
    return {
        "logs": result.data,
        "total": result.count or len(result.data),
        "page": page
    }


@app.get("/logs/{id}")
async def get_log(id: int, username: str, password: str):
    """Tek log getir."""
    check_auth(username, password)
    result = supabase.table('logs').select("*").eq('id', id).execute()
    return result.data[0] if result.data else {}


@app.get("/stats")
async def get_stats(username: str, password: str):
    """İstatistikler."""
    check_auth(username, password)
    
    total = supabase.table('logs').select("id", count='exact').execute()
    anomalies = supabase.table('logs').select("id", count='exact').eq('is_anomaly', True).execute()
    
    return {
        "total_logs": total.count or 0,
        "total_anomalies": anomalies.count or 0
    }


@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    """Raspberry'den fotoğraf al ve analiz et."""
    
    # Fotoğrafı oku
    contents = await file.read()
    image = Image.open(io.BytesIO(contents)).convert('RGB')
    
    # Dosya adı
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"captures/{timestamp}.jpg"
    
    # Önceki fotoğrafı al
    last_log = supabase.table('logs').select("image_path").order('created_at', desc=True).limit(1).execute()
    last_path = last_log.data[0]['image_path'] if last_log.data else None
    
    # Fark hesapla
    diff = calculate_image_diff(image, last_path)
    
    # Storage'a yükle
    image_url = None
    try:
        img_bytes = io.BytesIO()
        image.save(img_bytes, format='JPEG', quality=85)
        
        supabase.storage.from_(STORAGE_BUCKET).upload(
            path=filename,
            file=img_bytes.getvalue(),
            file_options={"content-type": "image/jpeg"}
        )
        image_url = supabase.storage.from_(STORAGE_BUCKET).get_public_url(filename)
    except Exception as e:
        print(f"Storage hatası: {e}")
    
    # Ayarları al
    settings = supabase.table('settings').select("anomalies_to_watch").limit(1).execute()
    anomalies = settings.data[0]['anomalies_to_watch'] if settings.data else "Yangın, Hırsız"
    
    # Gemini analizi
    result = analyze_with_gemini(image, anomalies)
    
    # Log kaydet
    supabase.table('logs').insert({
        "is_anomaly": result['is_anomaly'],
        "reason": result['reason'],
        "diff_percentage": diff,
        "image_url": image_url,
        "image_path": filename
    }).execute()
    
    # Anomali varsa mail
    if result['is_anomaly']:
        send_alert_email(result['reason'], image_url)
    
    return {
        "status": "ok",
        "diff": diff,
        "is_anomaly": result['is_anomaly'],
        "reason": result['reason']
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)