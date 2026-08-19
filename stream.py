import requests
import subprocess
import time

# Ayarlar
M3U_URL = "https://raw.githubusercontent.com/sahind01/vidmoy/refs/heads/main/filmler/filmsss.m3u"
LOGO_URL = "https://i.ibb.co/VWX8m4Kd/1001539417.png"
RTMP_URL = "rtmp://ssh101.bozztv.com:1935/ssh101/sonycinematurk"

def get_video_urls():
    """M3U dosyasını indirir ve içindeki .mp4/.mkv vb. linkleri ayıklar."""
    try:
        response = requests.get(M3U_URL)
        urls = []
        for line in response.text.splitlines():
            # http ile başlayan satırları al (EXTINF gibi metadata satırlarını atla)
            if line.startswith("http"):
                urls.append(line.strip())
        return urls
    except Exception as e:
        print(f"M3U listesi çekilirken hata: {e}")
        return []

def stream_video(video_url):
    """FFmpeg kullanarak videoyu logoyla birlikte RTMP sunucusuna iletir."""
    print(f"\n>>> YAYINA GİRİYOR: {video_url}\n")
    
    command = [
        'ffmpeg',
        '-re',                  # Videoyu gerçek zamanlı (1x hızında) okutur (Canlı yayın için şart)
        '-i', video_url,        # Film kaynağı
        '-i', LOGO_URL,         # Logo kaynağı
        '-filter_complex', 'overlay=W-w-20:20', # Logoyu sağ üst köşeye 20px boşlukla yerleştirir
        '-c:v', 'libx264',      # Video kodeği
        '-preset', 'veryfast',  # İşlemci dostu hızlı kodlama
        '-maxrate', '2500k',    # Maksimum bit hızı (Donmaları önler)
        '-bufsize', '5000k',
        '-pix_fmt', 'yuv420p',  # Uyumluluk için renk formatı
        '-g', '50',             # Keyframe aralığı (Akıcılık için önemli)
        '-c:a', 'aac',          # Ses kodeği
        '-b:a', '128k',         # Ses kalitesi
        '-ar', '44100',
        '-f', 'flv',            # RTMP için çıkış formatı
        RTMP_URL
    ]
    
    try:
        # FFmpeg komutunu çalıştır ve video bitene kadar bekle
        subprocess.run(command)
    except Exception as e:
        print(f"Yayın sırasında hata oluştu: {e}")

def main():
    while True:
        urls = get_video_urls()
        
        if not urls:
            print("Listede film bulunamadı, 60 saniye sonra tekrar denenecek...")
            time.sleep(60)
            continue
            
        print(f"Toplam {len(urls)} film bulundu. Yayın döngüsü başlıyor...")
        
        # Listedeki filmleri tek tek oynat
        for url in urls:
            stream_video(url)
            # Film bitince diğerine geçmeden önce 2 saniye bekle
            time.sleep(2)
            
        print("M3U listesinin sonuna gelindi. Başa sarılıyor...")

if __name__ == "__main__":
    main()
