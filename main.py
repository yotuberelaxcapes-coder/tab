import time
import json
import os
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

class DizipalScraper:
    def __init__(self, url):
        self.url = url
        self.driver = None
        self.data = []

    def start_browser(self):
        """GitHub Actions için özel tarayıcı ayarları."""
        print("🌐 Tarayıcı başlatılıyor (Headless Mod)...")
        options = uc.ChromeOptions()
        
        # GitHub Sunucuları için Kritik Ayarlar
        options.add_argument('--headless=new')  # Ekransız mod
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        self.driver = uc.Chrome(options=options, headless=True, use_subprocess=False)

    def scrape(self):
        if not self.driver:
            self.start_browser()

        try:
            print(f"🔗 {self.url} adresine gidiliyor...")
            self.driver.get(self.url)
            
            # Cloudflare kontrolü için bekleme süresini artırdık
            print("⏳ Güvenlik kontrolü bekleniyor (15sn)...")
            time.sleep(15)

            print("📂 Veriler taranıyor...")
            dizi_kartlari = self.driver.find_elements(By.CSS_SELECTOR, ".new-added-list a")

            if not dizi_kartlari:
                print("❌ Hiçbir dizi bulunamadı! Sayfa yüklenmemiş veya Cloudflare engeli olabilir.")
                # Hata ayıklama için ekran görüntüsü al
                self.driver.save_screenshot("hata_goruntusu.png")
                return

            print(f"✅ Toplam {len(dizi_kartlari)} içerik bulundu. İşleniyor...")

            for kart in dizi_kartlari:
                try:
                    isim = kart.find_element(By.TAG_NAME, "h2").text.strip()
                    link = kart.get_attribute("href")
                    
                    if isim and link:
                        self.data.append({
                            "isim": isim,
                            "link": link,
                            "tarih": time.strftime("%Y-%m-%d %H:%M:%S")
                        })
                except:
                    continue

        except Exception as e:
            print(f"❌ Genel Hata: {e}")
        
        finally:
            self.close_browser()

    def save_to_json(self, filename="diziler.json"):
        if not self.data:
            print("⚠️ Kaydedilecek veri yok.")
            return

        # Eski veriyi oku, yenileri ekle
        if os.path.exists(filename):
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    eski_veri = json.load(f)
                    # Sadece yeni olanları ekle (Basit bir kontrol)
                    mevcut_linkler = [d['link'] for d in eski_veri]
                    yeni_eklenenler = [d for d in self.data if d['link'] not in mevcut_linkler]
                    eski_veri.extend(yeni_eklenenler)
                    self.data = eski_veri
            except:
                pass

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)
        print(f"💾 Veriler '{filename}' dosyasına başarıyla kaydedildi.")

    def close_browser(self):
        if self.driver:
            self.driver.quit()
            print("🔒 Tarayıcı kapatıldı.")

if __name__ == "__main__":
    TARGET_URL = "https://dizipal1536.com/yabanci-dizi-izle"
    bot = DizipalScraper(TARGET_URL)
    bot.scrape()
    bot.save_to_json()
