# Raspberry Pi CCTV Client

## Kurulum

1. Dosyayı Raspberry Pi'a kopyala:
```bash
scp client.py pi@raspberrypi.local:~/
```

2. Bağımlılıkları yükle:
```bash
pip install requests
```

3. Çalıştır:
```bash
python client.py
```

## Otomatik Başlatma (Opsiyonel)

Raspberry Pi açıldığında otomatik çalışması için:

```bash
# Crontab aç
crontab -e

# Bu satırı ekle:
@reboot python /home/pi/client.py >> /home/pi/cctv.log 2>&1
```

## Notlar

- `rpicam-still` komutu Raspberry Pi OS'ta varsayılan olarak gelir
- Kamera modülü bağlı ve etkin olmalı
- İnternet bağlantısı gerekli
