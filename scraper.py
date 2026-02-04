import requests
from bs4 import BeautifulSoup
import re
import json
import base64
import time

# --- P.A.C.K.E.R. Çözücü Fonksiyonu ---
def unpack(p, a, c, k, e=None, d=None):
    """
    Dean Edwards Packer algoritmasını çözer (eval(function(p,a,c,k,e,d)...).
    Javascript'in bu sıkıştırma yöntemini Python'a simüle eder.
    """
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
        self.base_url = "https://www.hdfilmcehennemi.nl"
        self.category_url = "https://www.hdfilmcehennemi.nl/category/film-izle-2/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
            "Referer": "https://www.hdfilmcehennemi.nl/",
            "Origin": "https://www.hdfilmcehennemi.nl"
        }
        self.movies = []

    def get_movies_from_category(self):
        print(f"Kategori taranıyor: {self.category_url}")
        try:
            response = requests.get(self.category_url, headers=self.headers)
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Film kartlarını bul
            posters = soup.select(".poster")
            
            for poster in posters:
                movie_data = {}
                movie_data["title"] = poster.get("title")
                movie_data["link"] = poster.get("href")
                movie_data["year"] = poster.find("span", text=re.compile(r"\d{4}")).text.strip() if poster.find("span", text=re.compile(r"\d{4}")) else "N/A"
                
                # Resim kaynağını al (lazyload veya src)
                img_tag = poster.find("img")
                if img_tag:
                    movie_data["poster"] = img_tag.get("data-src") or img_tag.get("src")
                
                print(f"Film Bulundu: {movie_data['title']}")
                
                # Detaylara git ve player verisini çek
                details = self.get_movie_details(movie_data["link"])
                movie_data.update(details)
                
                self.movies.append(movie_data)
                time.sleep(1) # Siteyi yormamak için bekleme
                
        except Exception as e:
            print(f"Kategori hatası: {e}")

    def get_movie_details(self, movie_url):
        data = {"description": "", "imdb": "", "stream_url": "", "iframe_url": ""}
        try:
            response = requests.get(movie_url, headers=self.headers)
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Açıklama ve IMDb
            desc_tag = soup.select_one("article.post-info-content p")
            if desc_tag:
                data["description"] = desc_tag.text.strip()
                
            imdb_tag = soup.select_one(".post-info-imdb-rating span")
            if imdb_tag:
                data["imdb"] = imdb_tag.text.strip()

            # Iframe URL'sini bul (Rapidrame)
            iframe = soup.select_one("iframe[data-src]")
            if iframe:
                iframe_url = iframe.get("data-src")
                if iframe_url.startswith("//"):
                    iframe_url = "https:" + iframe_url
                data["iframe_url"] = iframe_url
                
                # Player'daki asıl video linkini çöz
                data["stream_url"] = self.resolve_player(iframe_url)
            
        except Exception as e:
            print(f"Detay hatası ({movie_url}): {e}")
        
        return data

    def resolve_player(self, iframe_url):
        """
        Iframe kaynağına gider, Packer şifresini çözer ve .m3u8 linkini bulur.
        """
        print(f"Player Çözümleniyor: {iframe_url}")
        try:
            # Iframe için özel header (Referer önemli)
            player_headers = self.headers.copy()
            player_headers["Referer"] = self.base_url
            
            response = requests.get(iframe_url, headers=player_headers)
            content = response.text

            # 1. Adım: Packer kodunu bul (eval(function(p,a,c,k,e,d)...)
            packer_regex = re.search(r"eval\(function\(p,a,c,k,e,d\).*?\.split\('\|'\)\)\)", content)
            
            if packer_regex:
                packed_code = packer_regex.group(0)
                # Packer parametrelerini ayrıştır
                args = re.search(r"}\('(.*)',(\d+),(\d+),'(.*)'.split\('\|'\)", packed_code)
                if args:
                    p = args.group(1)
                    a = int(args.group(2))
                    c = int(args.group(3))
                    k = args.group(4).split('|')
                    
                    # Kodu unpack et (JavaScript'i açık hale getir)
                    unpacked_js = unpack(p, a, c, k)
                    
                    # 2. Adım: Unpacked kod içinde .m3u8 veya .mp4 ara
                    # Genellikle "file":"https://..." formatındadır
                    video_match = re.search(r'file\s*:\s*["\'](https?://[^"\']+\.m3u8[^"\']*)["\']', unpacked_js)
                    
                    if video_match:
                        return video_match.group(1)
                    
                    # Eğer regex bulamazsa, base64 encode edilmiş bir string olabilir (s_TKrBf7wd9pR gibi)
                    # Bu durumda genellikle kodun içinde atob() fonksiyonu aranır, ancak
                    # HDFilmCehennemi genelde unpack sonrası açık link verir.
                    # Alternatif basit regex:
                    url_match = re.search(r'(https?://[a-zA-Z0-9\-\.]+\.[a-z]{2,}/[^\s"\'\)]+)', unpacked_js)
                    if url_match:
                        return url_match.group(1)

            return "Stream URL Bulunamadı (Korumalı veya Yapı Değişti)"

        except Exception as e:
            return f"Player Hatası: {e}"

    def save_json(self):
        with open("hdfilm_data.json", "w", encoding="utf-8") as f:
            json.dump(self.movies, f, ensure_ascii=False, indent=4)
        print("Veriler hdfilm_data.json dosyasına kaydedildi.")

if __name__ == "__main__":
    scraper = HDFilmScraper()
    scraper.get_movies_from_category()
    scraper.save_json()
