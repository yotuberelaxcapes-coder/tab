import cloudscraper
from bs4 import BeautifulSoup
import re
import json
import base64
import time
import sys

# --- P.A.C.K.E.R. Çözücü (JavaScript Deobfuscator) ---
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
        # Cloudscraper: Cloudflare korumasını aşmak için gerekli
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        self.base_url = "https://www.hdfilmcehennemi.nl"
        self.category_url = "https://www.hdfilmcehennemi.nl/category/film-izle-2/"
        self.movies = []

    def get_movies_from_category(self):
        print(f"1. Kategoriye Bağlanılıyor: {self.category_url}")
        try:
            response = self.scraper.get(self.category_url)
            
            if response.status_code != 200:
                print(f"HATA: Sayfaya girilemedi. Kod: {response.status_code}")
                return

            soup = BeautifulSoup(response.content, "html.parser")
            
            # Film kartlarını bul (HTML yapısına göre güncel seçici)
            posters = soup.select(".poster")
            
            if not posters:
                print("UYARI: Film bulunamadı! Site yapısı değişmiş veya Cloudflare hala engelliyor.")
                # Hata ayıklama için sayfanın başını yazdır
                print("Gelen Sayfa İçeriği (İlk 500 karakter):")
                print(soup.prettify()[:500])
                return

            print(f"Toplam {len(posters)} film bulundu. Veriler çekiliyor...")

            for poster in posters: # Test için sadece ilk 5 filme bakalım, hepsini istersen [:5] sil.
                movie_data = {}
                movie_data["title"] = poster.get("title")
                movie_data["link"] = poster.get("href")
                
                # Resim
                img_tag = poster.find("img")
                if img_tag:
                    movie_data["poster"] = img_tag.get("data-src") or img_tag.get("src")
                
                # Yıl
                year_span = poster.select_one(".poster-meta span:first-child")
                movie_data["year"] = year_span.text.strip() if year_span else "N/A"

                print(f"--> İşleniyor: {movie_data['title']}")
                
                # Detay sayfasına git
                if movie_data["link"]:
                    details = self.get_movie_details(movie_data["link"])
                    movie_data.update(details)
                
                self.movies.append(movie_data)
                # Cloudflare'in bizi banlamaması için biraz bekle
                time.sleep(2) 

        except Exception as e:
            print(f"Genel Hata: {e}")

    def get_movie_details(self, movie_url):
        data = {"description": "", "imdb": "", "stream_url": "", "iframe_url": ""}
        try:
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

            # Player Iframe Bulma (Rapidrame)
            # Genellikle data-src içinde saklıdır ve hidden olabilir
            iframe = soup.select_one("iframe[data-src*='rapidrame']") or soup.select_one("iframe[data-src*='video/embed']")
            
            if iframe:
                iframe_url = iframe.get("data-src")
                if iframe_url.startswith("//"):
                    iframe_url = "https:" + iframe_url
                
                data["iframe_url"] = iframe_url
                data["stream_url"] = self.resolve_player(iframe_url)
            else:
                data["iframe_url"] = "Player Bulunamadı"

        except Exception as e:
            print(f"    Detay hatası: {e}")
        
        return data

    def resolve_player(self, iframe_url):
        """
        Player içerisindeki şifreli JS kodunu çözer.
        """
        try:
            # Player için Referer header'ı çok önemlidir
            headers = {"Referer": self.base_url}
            response = self.scraper.get(iframe_url, headers=headers)
            content = response.text

            # 1. Packer kodunu regex ile yakala
            packer_pattern = r"eval\(function\(p,a,c,k,e,d\).*?\.split\('\|'\)\)\)"
            packed_data = re.search(packer_pattern, content)

            if packed_data:
                packed_js = packed_data.group(0)
                
                # Parametreleri ayıkla
                args = re.search(r"}\('(.*)',(\d+),(\d+),'(.*)'.split\('\|'\)", packed_js)
                if args:
                    p = args.group(1)
                    a = int(args.group(2))
                    c = int(args.group(3))
                    k = args.group(4).split('|')
                    
                    # Şifreyi çöz (Deobfuscate)
                    unpacked_code = unpack(p, a, c, k)
                    
                    # 2. Çözülen kod içinde .m3u8 veya .mp4 linkini ara
                    # Genellikle file:"..." veya sources:[{file:"..."}] içindedir
                    
                    # Yöntem A: Açık m3u8 linki
                    m3u8_match = re.search(r'file\s*:\s*["\'](https?://[^"\']+\.m3u8[^"\']*)["\']', unpacked_code)
                    if m3u8_match:
                        return m3u8_match.group(1)
                    
                    # Yöntem B: Base64 ile gizlenmiş link (atob)
                    # sources: [{file:atob(file_link)}] gibi yapılar için
                    base64_match = re.search(r'file\s*:\s*atob\([\'"]([A-Za-z0-9+/=]+)[\'"]\)', unpacked_code)
                    if base64_match:
                        decoded_link = base64.b64decode(base64_match.group(1)).decode('utf-8')
                        return decoded_link

                    # Yöntem C: Değişken adı (s_TKrBf7wd9pR gibi)
                    # Kodun başında bir değişken tanımlanmış olabilir.
                    var_match = re.search(r'var\s+([a-zA-Z0-9_]+)\s*=\s*["\'](https?://[^"\']+)["\']', unpacked_code)
                    if var_match:
                         return var_match.group(2)

            return "Stream Linki Çözülemedi (Koruma Güncellenmiş Olabilir)"

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
