import cloudscraper
from bs4 import BeautifulSoup
import re
import json
import base64
import time
import sys

# --- P.A.C.K.E.R. Çözücü ---
def unpack(p, a, c, k, e=None, d=None):
    def e_func(c):
        return ('' if c < a else e_func(int(c / a))) + \
               (chr(c % a + 29) if c % a > 35 else str(base64.b36encode(bytes([c % a]))[2:].decode('utf-8')))
    while c:
        c -= 1
        if k[c]:
            p = re.sub(r'\b' + e_func(c) + r'\b', k[c], p)
    return p

class HDFilmScraper:
    def __init__(self):
        # Cloudscraper ayarları
        self.scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
        )
        
        # GÜNCEL ADRES KONTROLÜ: Site yasaklandıkça uzantı değişir.
        # Tarayıcınızdan siteye girip yönlendiği son adresi buraya yazın.
        # Örnek: .nl, .co, .net, .com vb.
        self.base_url = "https://www.hdfilmcehennemi.nl" 
        self.category_url = f"{self.base_url}/category/film-izle-2/"
        self.movies = []

        # Proxy ayarları (VPN yoksa ve 451 hatası alıyorsanız burayı doldurun)
        # Format: "http://kullanici:sifre@ip:port" veya "http://ip:port"
        self.proxies = {
            # "http": "http://IP_ADRESI:PORT",
            # "https": "http://IP_ADRESI:PORT",
        }

    def get_movies_from_category(self):
        print(f"1. Kategoriye Bağlanılıyor: {self.category_url}")
        try:
            # Proxy varsa kullan, yoksa direkt bağlan
            if self.proxies:
                response = self.scraper.get(self.category_url, proxies=self.proxies)
            else:
                response = self.scraper.get(self.category_url)
            
            if response.status_code == 451:
                print("KRİTİK HATA (451): Erişim engeli var (VPN kullanın veya GitHub Actions'da çalıştırın).")
                return
            elif response.status_code != 200:
                print(f"HATA: Sayfaya girilemedi. Kod: {response.status_code}")
                return

            soup = BeautifulSoup(response.content, "html.parser")
            posters = soup.select(".poster")
            
            if not posters:
                print("UYARI: Film bulunamadı! Site yapısı değişmiş olabilir.")
                return

            print(f"Toplam {len(posters)} film bulundu. Veriler çekiliyor...")

            for poster in posters[:10]: # Test için ilk 10 film
                movie_data = {}
                movie_data["title"] = poster.get("title")
                
                # Link bazen tam bazen göreceli olabilir
                href = poster.get("href")
                if href.startswith("http"):
                    movie_data["link"] = href
                else:
                    movie_data["link"] = self.base_url + href
                
                img_tag = poster.find("img")
                if img_tag:
                    movie_data["poster"] = img_tag.get("data-src") or img_tag.get("src")
                
                year_span = poster.select_one(".poster-meta span:first-child")
                movie_data["year"] = year_span.text.strip() if year_span else "N/A"

                print(f"--> İşleniyor: {movie_data['title']}")
                
                if movie_data["link"]:
                    details = self.get_movie_details(movie_data["link"])
                    movie_data.update(details)
                
                self.movies.append(movie_data)
                time.sleep(1) # Banlanmamak için bekle

        except Exception as e:
            print(f"Genel Hata: {e}")

    def get_movie_details(self, movie_url):
        data = {"description": "", "imdb": "", "stream_url": "", "iframe_url": ""}
        try:
            # Proxy kontrolü
            if self.proxies:
                response = self.scraper.get(movie_url, proxies=self.proxies)
            else:
                response = self.scraper.get(movie_url)

            soup = BeautifulSoup(response.content, "html.parser")
            
            # Açıklama
            desc_tag = soup.select_one("article.post-info-content p")
            if desc_tag:
                data["description"] = desc_tag.text.strip()
            
            # IMDb
            imdb_tag = soup.select_one(".post-info-imdb-rating span")
            if imdb_tag:
                data["imdb"] = imdb_tag.text.strip()

            # Rapidrame veya diğer playerları bul
            iframe = soup.select_one("iframe[data-src*='rapidrame']") or soup.select_one("iframe[data-src*='video/embed']") or soup.select_one("iframe[src*='rapidrame']")
            
            if iframe:
                iframe_url = iframe.get("data-src") or iframe.get("src")
                if iframe_url.startswith("//"):
                    iframe_url = "https:" + iframe_url
                
                data["iframe_url"] = iframe_url
                data["stream_url"] = self.resolve_player(iframe_url)
            else:
                # Bazen player JS içinde saklıdır, basit bir kontrol:
                data["iframe_url"] = "Iframe bulunamadı (JS ile gömülü olabilir)"

        except Exception as e:
            print(f"    Detay hatası: {e}")
        
        return data

    def resolve_player(self, iframe_url):
        try:
            headers = {"Referer": self.base_url}
            if self.proxies:
                response = self.scraper.get(iframe_url, headers=headers, proxies=self.proxies)
            else:
                response = self.scraper.get(iframe_url, headers=headers)
                
            content = response.text

            # Packer şifresini bul
            packer_pattern = r"eval\(function\(p,a,c,k,e,d\).*?\.split\('\|'\)\)\)"
            packed_data = re.search(packer_pattern, content)

            if packed_data:
                packed_js = packed_data.group(0)
                args = re.search(r"}\('(.*)',(\d+),(\d+),'(.*)'.split\('\|'\)", packed_js)
                if args:
                    p, a, c, k = args.group(1), int(args.group(2)), int(args.group(3)), args.group(4).split('|')
                    unpacked_code = unpack(p, a, c, k)
                    
                    # Linki yakala
                    m3u8_match = re.search(r'file\s*:\s*["\'](https?://[^"\']+\.m3u8[^"\']*)["\']', unpacked_code)
                    if m3u8_match: return m3u8_match.group(1)
                    
                    # Alternatif link yakalama
                    var_match = re.search(r'var\s+([a-zA-Z0-9_]+)\s*=\s*["\'](https?://[^"\']+)["\']', unpacked_code)
                    if var_match: return var_match.group(2)

            return "Stream Linki Çözülemedi"

        except Exception as e:
            return f"Player Hatası: {e}"

    def save_json(self):
        if not self.movies:
            print("Kaydedilecek veri yok.")
            return
        with open("hdfilm_data.json", "w", encoding="utf-8") as f:
            json.dump(self.movies, f, ensure_ascii=False, indent=4)
        print(f"\nBaşarılı! {len(self.movies)} film 'hdfilm_data.json' dosyasına kaydedildi.")

if __name__ == "__main__":
    scraper = HDFilmScraper()
    scraper.get_movies_from_category()
    scraper.save_json()
