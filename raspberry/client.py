# client.py - Raspberry Pi CCTV Client
import requests
import subprocess
import time
import io

API_URL = "https://ai-supported-cctv-app.onrender.com/upload"
INTERVAL = 10

def capture_and_upload():
    """Fotoğraf çek ve RAM'den direkt gönder."""
    try:
        result = subprocess.run(
            ["rpicam-still", "-t", "1", "-o", "-", "--width", "640", "--height", "480"],
            capture_output=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return
        
        requests.post(
            API_URL,
            files={"file": ("capture.jpg", io.BytesIO(result.stdout), "image/jpeg")},
            timeout=30
        )
        print("Fotoğraf gönderildi")
        
    except:
        pass

if __name__ == "__main__":
    print("CCTV Client başlatıldı")
    while True:
        capture_and_upload()
        time.sleep(INTERVAL)
