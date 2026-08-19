import requests
import subprocess
import time
import os

# Ayarlar
M3U_URL = "https://raw.githubusercontent.com/sahind01/vidmoy/refs/heads/main/filmler/filmsss.m3u"
LOGO_URL = "https://i.ibb.co/VWX8m4Kd/1001539417.png"
RTMP_URL = "rtmp://ssh101.bozztv.com:1935/ssh101/sonycinematurk"
LOCAL_LOGO = "logo.png"

def download_logo():
    """Logoyu her seferinde internetten okumak yerine sunucuya indirir (Hataları önler)."""
    if not os.path.exists(LOCAL_LOGO):
        print("Kanal logosu indiriliyor...")
        try:
            r = requests.get(LOGO_URL)
            with open(LOCAL_LOGO, 'wb') as f:
                f.write(r.content)
        except Exception as e:
            print(f"Logo indirilemedi: {e}")

def get_video_urls():
    """M3U dosyasını indirir ve içindeki linkleri ayıklar."""
    try:
        response = requests.get(M3U_URL)
        urls = [line.strip() for line in response.text.splitlines() if line.startswith("http")]
        return urls
    except Exception as e:
        print(f"M3U listesi çekilirken hata: {e}")
        return []

def stream_video(video_url):
    """Vidyoyu logoyla birlikte RTMP sunucusuna iletir."""
    print(f"\n>>> YAYINA GİRİYOR: {video_url}\n")
    
    command = [
        'ffmpeg',
        '-hide_banner',         # Log kirliliğini önler, sadece asıl hatayı gösterir
        '-re',
        '-i', video_url,
        '-i', LOCAL_LOGO,
        '-filter_complex', 'overlay=W-w-20:20',
        '-c:v', 'libx264',
        '-preset', 'veryfast',
        '-maxrate', '2500k',
        '-bufsize', '5000k',
        '-pix_fmt', 'yuv420p',
        '-g', '50',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-ar', '44100',
        '-f', 'flv',
        RTMP_URL
    ]
    
    # Hataları yakalamak için logları konsola bas
    subprocess.run(command)

def main():
    download_logo()
    
    while True:
        urls = get_video_urls()
        
        if not urls:
            print("Listede film bulunamadı, 60 saniye sonra tekrar denenecek...")
            time.sleep(60)
            continue
            
        print(f"Toplam {len(urls)} film bulundu. Yayın döngüsü başlıyor...")
        
        for url in urls:
            stream_video(url)
            time.sleep(2)
            
        print("M3U listesinin sonuna gelindi. Başa sarılıyor...")

if __name__ == "__main__":
    main()
