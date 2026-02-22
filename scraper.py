import asyncio
from playwright.async_api import async_playwright

async def main():
    url = "https://sezonlukdizi.cc/fate-strange-fake/1-sezon-8-bolum.html"

    async with async_playwright() as p:
        # Headless modunu kapalı tutarak sanal ekranda çalıştırıyoruz
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--no-sandbox", 
                "--disable-setuid-sandbox", 
                "--disable-blink-features=AutomationControlled"
            ]
        )
        
        # Gerçek bir Windows makinesindeki Chrome gibi davran
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="tr-TR",
            timezone_id="Europe/Istanbul"
        )
        page = await context.new_page()
        
        # --- BOT GİZLEME (STEALTH) ENJEKSİYONLARI ---
        # Cloudflare'ın botları tespit etmek için kullandığı webdriver bayrağını ve diğer tarayıcı izlerini siliyoruz
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.navigator.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
            Object.defineProperty(navigator, 'languages', {get: () => ['tr-TR', 'tr', 'en-US', 'en']});
        """)
        
        print(f"Sayfaya gidiliyor: {url}")
        await page.goto(url, wait_until="domcontentloaded")
        
        print("Sayfa yükleniyor, Cloudflare vb. korumalar bekleniyor...")
        # Koruma ekranının geçmesi için bekleme süresi
        await page.wait_for_timeout(8000) 

        try:
            # Alternatifler menüsünün yüklenmesini bekle
            await page.wait_for_selector('#alternatif', timeout=15000)
            
            # Dropdown menüyü aç
            await page.click('#alternatif')
            await page.wait_for_timeout(1000)

            # Menü içindeki alternatif kaynak isimlerini bul
            alternatifler = await page.query_selector_all('#alternatif .menu .item')
            print(f"Toplam {len(alternatifler)} alternatif bulundu.\n")

            for alt in alternatifler:
                isim = await alt.inner_text()
                
                # İlgili alternatife tıkla ve iframe (oynatıcı) yüklenmesini bekle
                await alt.click()
                await page.wait_for_timeout(4000) 
                
                # Iframe'in içindeki src (kaynak) linkini al
                iframe = await page.query_selector('#embed iframe')
                if iframe:
                    src = await iframe.get_attribute('src')
                    print(f"Kaynak: {isim.strip()} -> Link: {src}")
                else:
                    print(f"Kaynak: {isim.strip()} -> Link bulunamadı.")
                    
                # Sonraki döngü için alternatifler menüsünü tekrar aç
                await page.click('#alternatif')
                await page.wait_for_timeout(1000)

        except Exception as e:
            print(f"Hata oluştu veya koruma aşılamadı: {e}")

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
