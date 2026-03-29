import asyncio
import yaml
import json
import os
from ddizi_lib import DDiziScraper

def generate_m3u(data: dict, filepath: str):
    """Veriyi standart IPTV M3U formatında kaydeder."""
    lines = ["#EXTM3U\n"]
    series_title = data.get("title", "Bilinmeyen Dizi")
    poster = data.get("poster", "")
    
    for ep in data.get("episodes", []):
        for video_link in ep.get("video_links", []):
            ep_title = ep.get("title", f"S{ep.get('season', 1):02d}E{ep.get('episode', 1):02d}")
            # tvg-logo ve group-title etiketleri eklendi
            extinf = f'#EXTINF:-1 tvg-logo="{poster}" group-title="{series_title}", {series_title} - {ep_title}\n'
            lines.append(extinf)
            lines.append(f"{video_link}\n")
            
    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(lines)

def generate_json(data: dict, filepath: str):
    """Veriyi JSON formatında kaydeder."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

async def main():
    # 1. Config dosyasını oku
    with open("config.yml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    output_dir = config['settings'].get('output_dir', './outputs')
    os.makedirs(output_dir, exist_ok=True)

    scraper = DDiziScraper(config)

    # 2. Hedef dizileri tara
    for target_url in config['targets']:
        print(f"[*] Taranıyor: {target_url}")
        
        # Dizi bilgisini ve bölüm listesini al
        series_data = await scraper.load_item(target_url)
        
        # Her bölüm için video linklerini çöz
        for ep in series_data["episodes"]:
            print(f"  -> Linkler çözülüyor: {ep['title']}")
            ep["video_links"] = await scraper.load_links(ep["url"])

        # 3. Dosyaları kaydet
        safe_title = "".join([c for c in series_data['title'] if c.isalpha() or c.isdigit() or c==' ']).rstrip()
        json_path = os.path.join(output_dir, f"{safe_title}.json")
        m3u_path = os.path.join(output_dir, f"{safe_title}.m3u")

        generate_json(series_data, json_path)
        generate_m3u(series_data, m3u_path)
        
        print(f"[+] Başarılı! Çıktılar kaydedildi:\n - {json_path}\n - {m3u_path}\n")

    await scraper.close()

if __name__ == "__main__":
    asyncio.run(main())
