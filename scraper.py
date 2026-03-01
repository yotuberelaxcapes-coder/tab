import requests
import re
import os

# Kazımak istediğin TRT Çocuk programlarının linklerini buraya ekleyebilirsin
SHOW_URLS = [
    "https://www.trtcocuk.net.tr/ekip-siberay"
    # İstersen buraya "https://www.trtcocuk.net.tr/rafadan-tayfa" gibi diğer dizileri de ekleyebilirsin.
]

def get_episodes(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # TRT Çocuk verileri JSON objesi içinde \u002F şeklinde (slash) tutuyor. Bunu düzeltiyoruz.
        html_content = response.text.replace('\\u002F', '/')

        # Regex ile Başlık, Görsel(Logo) ve m3u8 Video Linkini yakalıyoruz
        # Nuxt objesi içindeki title:"...", mainImageUrl:"...", video:"..." yapısını hedefler
        pattern = re.compile(r'title:"([^"]+)",.*?mainImageUrl:"([^"]+)",.*?video:"([^"]+\.m3u8)"', re.IGNORECASE | re.DOTALL)
        matches = pattern.findall(html_content)

        # Aynı videonun tekrar eklenmesini önlemek için set kullanıyoruz
        seen = set()
        episodes = []
        
        for title, logo, video_url in matches:
            if video_url not in seen:
                seen.add(video_url)
                episodes.append({
                    "title": title.strip(),
                    "logo": logo.strip(),
                    "video": video_url.strip()
                })
                
        return episodes

    except Exception as e:
        print(f"Hata oluştu ({url}): {e}")
        return []

def generate_m3u(all_episodes, filename="trtcocuk.m3u"):
    with open(filename, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for ep in all_episodes:
            # tvg-logo ve grup adını IPTV oynatıcılarının tanıyacağı formatta ekliyoruz
            f.write(f'#EXTINF:-1 tvg-logo="{ep["logo"]}" group-title="TRT Çocuk", {ep["title"]}\n')
            f.write(f'{ep["video"]}\n')

if __name__ == "__main__":
    all_eps = []
    for url in SHOW_URLS:
        print(f"Veriler çekiliyor: {url}")
        eps = get_episodes(url)
        print(f"{len(eps)} bölüm bulundu.")
        all_eps.extend(eps)

    if all_eps:
        generate_m3u(all_eps, "trtcocuk.m3u")
        print("M3U dosyası başarıyla oluşturuldu ve kaydedildi: trtcocuk.m3u")
    else:
        print("Hiç video verisi bulunamadı. Sitenin yapısı değişmiş olabilir.")
