import time
import json
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class DizipalScraper:
    def __init__(self, url):
        self.url = url
        self.driver = None
        self.data = []

    def start_browser(self):
        """Tarayıcıyı başlatır ve ayarları yapar."""
        print("🌐 Tarayıcı başlatılıyor...")
        options = uc.ChromeOptions()
        # options.add_argument('--headless')  # Arka planda çalıştırmak istersen yorumu kaldır
        self.driver = uc.Chrome(options=options)

    def scrape(self):
        """Siteye gider ve verileri çeker."""
        if not self.driver:
            self.start_browser()

        try:
            print(f"🔗 {self.url} adresine gidiliyor...")
            self.driver.get(self.url)
            
            print("⏳ Güvenlik kontrolü bekleniyor (10sn)...")
            time.sleep(10)  # Cloudflare geçişi için bekleme süresi

            print("📂 Veriler taranıyor...")
            # HTML yapısına göre 'new-added-list' içindeki 'a' etiketlerini bulur
            dizi_kartlari = self.driver.find_elements(By.CSS_SELECTOR, ".new-added-list a")

            if not dizi_kartlari:
                print("❌ Hiçbir dizi bulunamadı! CSS seçicileri kontrol et.")
                return

            print(f"✅ Toplam {len(dizi_kartlari)} içerik bulundu. İşleniyor...")

            for kart in dizi_kartlari:
                try:
                    isim = kart.find_element(By.TAG_NAME, "h2").text.strip()
                    link = kart.get_attribute("href")
                    
                    if isim and link:
                        self.data.append({
                            "isim": isim,
                            "link": link
                        })
                except Exception as e:
                    print(f"⚠️ Bir kart işlenirken hata oluştu: {e}")
                    continue

        except Exception as e:
            print(f"❌ Genel Hata: {e}")
        
        finally:
            self.close_browser()

    def save_to_json(self, filename="diziler.json"):
        """Verileri JSON dosyasına kaydeder."""
        if not self.data:
            print("⚠️ Kaydedilecek veri yok.")
            return

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)
        print(f"💾 Veriler '{filename}' dosyasına başarıyla kaydedildi.")

    def close_browser(self):
        """Tarayıcıyı kapatır."""
        if self.driver:
            self.driver.quit()
            print("🔒 Tarayıcı kapatıldı.")

if __name__ == "__main__":
    # Güncel URL buraya girilecek
    TARGET_URL = "https://dizipal1536.com/yabanci-dizi-izle"
    
    bot = DizipalScraper(TARGET_URL)
    bot.scrape()
    bot.save_to_json()
