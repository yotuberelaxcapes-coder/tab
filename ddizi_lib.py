import httpx
import json
import os
from selectolax.parser import HTMLParser
from contextlib import suppress

class DDiziScraper:
    def __init__(self, config: dict):
        self.name = config['plugin']['name']
        self.main_url = config['plugin']['main_url']
        self.timeout = config['settings'].get('timeout', 15)
        
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": f"{self.main_url}/"
            }
        )

    def fix_url(self, url: str) -> str:
        if not url: return ""
        if url.startswith("http"): return url
        if url.startswith("//"): return f"https:{url}"
        return f"{self.main_url}{url}"

    def extract_season_episode(self, text: str):
        # Basit S/E ayrıştırıcı (Geliştirilebilir)
        import re
        s = re.search(r'(\d+)\.\s*Sezon', text, re.IGNORECASE)
        e = re.search(r'(\d+)\.\s*Bölüm', text, re.IGNORECASE)
        season = int(s.group(1)) if s else 1
        episode = int(e.group(1)) if e else 1
        return season, episode

    async def load_item(self, url: str) -> dict:
        """Dizi detaylarını ve bölüm listesini çeker."""
        response = await self.client.get(url)
        tree = HTMLParser(response.text)

        title_node = tree.css_first("h1, h2, div.dizi-boxpost-cat a")
        title = title_node.text(strip=True) if title_node else "Bilinmeyen Dizi"

        poster_node = tree.css_first("div.afis img, img.afis, img.img-back")
        poster = self.fix_url(poster_node.attributes.get("src", "")) if poster_node else ""

        episodes = []
        current_page = 1
        has_next = True

        while has_next:
            page_url = f"{url}/sayfa-{current_page}" if current_page > 1 else url
            if current_page > 1:
                response = await self.client.get(page_url)
                tree = HTMLParser(response.text)

            page_eps = tree.css("div.bolumler a, div.sezonlar a, div.dizi-arsiv a")
            if not page_eps:
                break

            for ep in page_eps:
                ep_name = ep.text(strip=True)
                ep_href = ep.attributes.get("href")
                
                if ep_name and ep_href:
                    s, e = self.extract_season_episode(ep_name)
                    episodes.append({
                        "season": s,
                        "episode": e,
                        "title": ep_name.replace("Final", "").strip(),
                        "url": self.fix_url(ep_href)
                    })

            # Sayfalama kontrolü
            pagination = tree.css(".pagination a")
            has_next = any("Sonraki" in a.text(strip=True) for a in pagination)
            current_page += 1
            if current_page > 10: break # Sonsuz döngü kilidi

        return {
            "title": title,
            "poster": poster,
            "url": url,
            "episodes": episodes
        }

    async def load_links(self, url: str) -> list:
        """Bölüm URL'sinden doğrudan oynatılabilir medya linklerini çıkarır."""
        response = await self.client.get(url)
        tree = HTMLParser(response.text)
        results = []

        # 1. og:video kontrolü
        og_video = tree.css_first("meta[property='og:video']")
        target_url = self.fix_url(og_video.attributes.get("content")) if og_video else None

        # 2. Iframe kontrolü
        if not target_url:
            iframe = tree.css_first("iframe[src^='/player/oynat/']")
            target_url = self.fix_url(iframe.attributes.get("src")) if iframe else None

        if target_url:
            with suppress(Exception):
                player_resp = await self.client.get(target_url, headers={"Referer": url})
                
                # file: "..." mantığını bul
                import re
                sources = re.findall(r'file:\s*["\']([^"\']+)["\']', player_resp.text)
                
                for src in sources:
                    src = self.fix_url(src)
                    if any(x in src.lower() for x in [".m3u8", ".mp4"]):
                        results.append(src)
                
                if not results and any(x in target_url.lower() for x in [".m3u8", ".mp4"]):
                    results.append(target_url)

        return results

    async def close(self):
        await self.client.aclose()
