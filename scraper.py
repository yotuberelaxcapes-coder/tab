import asyncio
from playwright.async_api import async_playwright

async def main():
    # Hedef URL (örnek olarak senin HTML'ine ait bölümü ekledim)
    url = "https://sezonlukdizi.cc/fate-strange-fake/1-sezon-8-bolum.html"

    async with async_playwright() as p:
        # Chromium tarayıcıyı arkaplanda başlat
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print(f"Sayfaya gidiliyor: {url}")
        await page.goto(url, wait_until="networkidle")

        # Alternatiflerin yüklenmesi için kısa bir bekleme
        await page.wait_for_selector('#alternatif .menu', timeout=10000)
        
        # Alternatif menüsündeki tüm seçenekleri bul
        alternatifler = await page.query_selector_all('#alternatif .menu .item')
        print(f"Toplam {len(alternatifler)} alternatif bulundu.\n")

        for alt in alternatifler:
            isim = await alt.inner_text()
            
            # Alternatife tıkla ve video embed'inin yüklenmesini bekle
            await alt.click()
            await page.wait_for_timeout(2000) # AJAX isteği için kısa bir tolerans
            
            # Oynatıcının içindeki iframe'i bul
            iframe = await page.query_selector('#embed iframe')
            if iframe:
                src = await iframe.get_attribute('src')
                # Okru, Vidmoly, Sibnet gibi kelimeleri kontrol edebilirsin
                print(f"Kaynak: {isim.strip()} -> Link: {src}")
            else:
                print(f"Kaynak: {isim.strip()} -> Link bulunamadı veya henüz yüklenmedi.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
