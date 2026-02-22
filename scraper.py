import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

async def main():
    url = "https://sezonlukdizi.cc/fate-strange-fake/1-sezon-8-bolum.html"

    async with async_playwright() as p:
        # Headless modunu kapattık, argümanlarla bot algılayıcıları yanıltıyoruz
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--no-sandbox", 
                "--disable-setuid-sandbox", 
                "--disable-blink-features=AutomationControlled"
            ]
        )
        
        # Gerçek bir kullanıcı gibi görünmek için User-Agent ekliyoruz
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        # Stealth (Gizlilik) eklentisini sayfaya uygula
        await stealth_async(page)
        
        print(f"Sayfaya gidiliyor: {url}")
        await page.goto(url, wait_until="domcontentloaded")
        
        print("Bot koruması (Cloudflare vb.) kontrol ediliyor, bekleniyor...")
        # Korumanın geçilmesi için 8 saniye bekliyoruz
        await page.wait_for_timeout(8000) 

        try:
            # Alternatif menüsünün yüklenmesini bekle
            await page.wait_for_selector('#alternatif', timeout=15000)
            
            # Dropdown menüyü açmak için 'Alternatifler' yazısına tıkla
            await page.click('#alternatif')
            await page.wait_for_timeout(1000)

            # Menü içindeki alternatifleri bul
            alternatifler = await page.query_selector_all('#alternatif .menu .item')
            print(f"Toplam {len(alternatifler)} alternatif bulundu.\n")

            for alt in alternatifler:
                isim = await alt.inner_text()
                
                # Alternatife tıkla ve iframe'in gelmesini bekle
                await alt.click()
                await page.wait_for_timeout(3000) 
                
                iframe = await page.query_selector('#embed iframe')
                if iframe:
                    src = await iframe.get_attribute('src')
                    print(f"Kaynak: {isim.strip()} -> Link: {src}")
                else:
                    print(f"Kaynak: {isim.strip()} -> Link bulunamadı.")
                    
                # Sonraki alternatif için menüyü tekrar aç
                await page.click('#alternatif')
                await page.wait_for_timeout(1000)

        except Exception as e:
            print(f"Bir hata oluştu veya koruma aşılamadı: {e}")

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
