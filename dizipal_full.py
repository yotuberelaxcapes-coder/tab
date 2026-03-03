import httpx
import asyncio
import re
from bs4 import BeautifulSoup

# --- AYARLAR ---
MAIN_URL = "https://dizipal.bar"
MAX_PAGE = 1 # Test için 1 sayfa. Tüm arşivi çekmek için bunu 5, 10 veya 50 yapabilirsin.

# Çekilecek Kategoriler (Orijinal koddaki gibi)
KATEGORILER = {
    "Aksiyon": f"{MAIN_URL}/kategori/aksiyon/page/",
    "Bilim Kurgu": f"{MAIN_URL}/kategori/bilim-kurgu/page/",
    "Komedi": f"{MAIN_URL}/kategori/komedi/page/"
    # İstersen diğer kategorileri buraya ekleyebilirsin
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": f"{MAIN_URL}/"
}

async def fetch_html(client, url):
    """URL'den sayfa kaynağını güvenli bir şekilde çeker."""
    try:
        resp = await client.get(url, headers=HEADERS, timeout=15.0)
        if resp.status_code == 200:
            return resp.text
    except Exception as e:
        print(f"[-] Hata ({url}): {e}")
    return None

async def extract_video_data(client, page_url):
    """Sayfadaki iframe'i bulup m3u8 ve altyazı linklerini kazar."""
    html = await fetch_html(client, page_url)
    if not html: return None

    soup = BeautifulSoup(html, "html.parser")
    iframe = soup.select_one("div.video-player-area iframe") or soup.select_one("div.responsive-player iframe")
    
    if not iframe or not iframe.get("src"):
        return None

    iframe_src = iframe.get("src")
    if iframe_src.startswith("//"):
        iframe_src = "https:" + iframe_src

    # İframe içine gir
    iframe_html = await fetch_html(client, iframe_src)
    if not iframe_html: return None

    # M3U8 ve Altyazı Regex (Orijinal kod mantığı)
    m3u_match = re.search(r'file\s*:\s*["\']([^"\']+)["\']', iframe_html)
    sub_match = re.search(r'"subtitle"\s*:\s*["\']([^"\']+)["\']', iframe_html)

    if m3u_match:
        data = {"m3u8": m3u_match.group(1), "subtitles": []}
        
        # Altyazıları ayıkla ([TR]url,[EN]url formatı)
        if sub_match:
            sub_text = sub_match.group(1)
            for sub in sub_text.split(","):
                lang = re.search(r'\[(.*?)\]', sub)
                lang_code = lang.group(1) if lang else "TR"
                sub_url = re.sub(r'\[.*?\]', '', sub).strip()
                data["subtitles"].append(f"{lang_code}: {sub_url}")
                
        return data
    return None

async def process_item(client, item_url, item_title):
    """İçeriğin film mi yoksa dizi mi olduğunu anlar ve tüm linkleri toplar."""
    results = []
    
    # Eğer bu bir DİZİ ise
    if "/dizi/" in item_url:
        print(f"  [DİZİ] Bölümler taranıyor: {item_title}")
        html = await fetch_html(client, item_url)
        if not html: return []
        
        soup = BeautifulSoup(html, "html.parser")
        episodes = soup.select("div.episode-item")
        
        for ep in episodes:
            a_tag = ep.select_one("a")
            if a_tag and a_tag.get("href"):
                ep_url = a_tag.get("href")
                ep_title = ep.select_one("h4").text.strip() if ep.select_one("h4") else "Bölüm"
                full_title = f"{item_title} - {ep_title}"
                
                print(f"    -> {full_title} çıkarılıyor...")
                video_data = await extract_video_data(client, ep_url)
                if video_data:
                    results.append({"title": full_title, "m3u8": video_data["m3u8"]})
                await asyncio.sleep(0.5) # Ban yememek için bekle
                
    # Eğer bu bir FİLM ise
    else:
        print(f"  [FİLM] Link çıkarılıyor: {item_title}")
        video_data = await extract_video_data(client, item_url)
        if video_data:
            results.append({"title": item_title, "m3u8": video_data["m3u8"]})
            
    return results

async def main():
    m3u_content = "#EXTM3U\n"
    total_links = 0
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        for cat_name, cat_url in KATEGORILER.items():
            print(f"\n=============================")
            print(f"[*] KATEGORİ: {cat_name}")
            print(f"=============================")
            
            for page in range(1, MAX_PAGE + 1):
                url = f"{cat_url}{page}/"
                print(f"\n[*] Sayfa {page} taranıyor: {url}")
                
                html = await fetch_html(client, url)
                if not html: continue
                
                soup = BeautifulSoup(html, "html.parser")
                items = soup.select("div.grid div.post-item")
                
                for item in items:
                    a_tag = item.select_one("a")
                    if a_tag and a_tag.get("href"):
                        title = a_tag.get("title", "İsimsiz")
                        href = a_tag.get("href")
                        
                        # Film veya Dizinin içine gir
                        videos = await process_item(client, href, title)
                        
                        for vid in videos:
                            m3u_content += f"#EXTINF:-1, {vid['title']}\n"
                            m3u_content += f"{vid['m3u8']}\n"
                            total_links += 1
                            
                        await asyncio.sleep(0.5)

    with open("dizipal_full.m3u", "w", encoding="utf-8") as f:
        f.write(m3u_content)
        
    print(f"\n[✓] İŞLEM BİTTİ! Toplam {total_links} adet video linki dizipal_full.m3u dosyasına kaydedildi.")

if __name__ == "__main__":
    asyncio.run(main())
