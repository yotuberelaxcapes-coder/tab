import requests
import re
from bs4 import BeautifulSoup

BASE_URL = "https://www.trtcocuk.net.tr"

def get_all_shows():
    print("Tüm programlar taranıyor...")
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}
        response = requests.get(f"{BASE_URL}/video", headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        shows = set()
        # "show-img" sınıfına sahip div'leri barındıran a etiketlerini (dizi linklerini) buluyoruz
        for a in soup.find_all("a", href=True):
            if a.find("div", class_="show-img"):
                href = a['href']
                if not href.startswith("http"):
                    href = BASE_URL + href
                shows.add(href)
        
        print(f"Toplam {len(shows)} farklı program bulundu.")
        return list(shows)
    except Exception as e:
        print(f"Programlar alınırken hata oluştu: {e}")
        return []

def get_episodes(show_url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(show_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # TRT Çocuk verileri JSON objesinde \u002F şeklinde (slash) tutuyor. Düzeltiyoruz.
        html_content = response.text.replace('\\u002F', '/')
        
        # URL'den dizi adını çıkartıp kategori adı olarak kullanıyoruz (Örn: /ekip-siberay -> Ekip Siberay)
        show_name = show_url.split("/")[-1].replace("-", " ").title()
        
        episodes = []
        seen = set()
        
        # M3U8 linklerini Nuxt objesi içerisinden güvenli bir şekilde ayıklıyoruz
        blocks = html_content.split('video:"')
        for i in range(1, len(blocks)):
            video_url = blocks[i].split('"', 1)[0]
            
            if not video_url.endswith('.m3u8') or video_url in seen:
                continue
            
            seen.add(video_url)
            
            # Videonun etrafındaki metni (öncesi ve sonrası) alıp başlık ve görseli arıyoruz
            context = blocks[i-1][-400:] + blocks[i][:400]
            
            title_match = re.search(r'title:"([^"]+)"', context)
            title = title_match.group(1).strip() if title_match else f"{show_name} Bölümü"
            
            img_match = re.search(r'(?:mainImage|mainImageUrl|artWork|logo):"([^"]+)"', context)
            logo = img_match.group(1).strip() if img_match else ""
            
            episodes.append({
                "title": title,
                "logo": logo,
                "video": video_url,
                "group": show_name
            })
            
        return episodes
    except Exception as e:
        print(f"Hata ({show_url}): {e}")
        return []

def generate_m3u(all_episodes, filename="trtcocuk.m3u"):
    print("M3U dosyası oluşturuluyor...")
    with open(filename, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for ep in all_episodes:
            # tvg-logo ve group-title eklenerek IPTV uygulamasında kategorili görünmesi sağlanıyor
            f.write(f'#EXTINF:-1 tvg-logo="{ep["logo"]}" group-title="{ep["group"]}", {ep["title"]}\n')
            f.write(f'{ep["video"]}\n')

if __name__ == "__main__":
    shows = get_all_shows()
    all_eps = []
    
    for url in shows:
        print(f"Bölümler çekiliyor: {url}")
        eps = get_episodes(url)
        all_eps.extend(eps)
        
    if all_eps:
        generate_m3u(all_eps, "trtcocuk.m3u")
        print(f"İşlem başarıyla tamamlandı! {len(all_eps)} adet video trtcocuk.m3u dosyasına kaydedildi.")
    else:
        print("Hiç video bulunamadı. Sitenin yapısı değişmiş olabilir.")
