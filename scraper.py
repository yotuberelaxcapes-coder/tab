from curl_cffi import requests
from bs4 import BeautifulSoup
import json

def dizi_verilerini_cek(dizi_url):
    print(f"[*] Dizi sayfası taranıyor: {dizi_url}")
    
    # curl_cffi ile gerçek bir Chrome 110 tarayıcısını taklit ediyoruz
    response = requests.get(dizi_url, impersonate="chrome110")
    print(f"[*] Yanıt Kodu: {response.status_code}")
    
    if response.status_code != 200:
        print("[!] Siteye erişilemedi. Cloudflare, GitHub Actions IP'sini tamamen engelliyor olabilir.")
        
    soup = BeautifulSoup(response.text, 'html.parser')
    
    dizi_data = {
        "url": dizi_url,
        "isim": "",
        "orijinal_isim": "",
        "yil": "",
        "tur": [],
        "imdb": "",
        "gorsel": "",
        "aciklama": "",
        "oyuncular": [],
        "bolumler": []
    }
    
    bolum_linkleri = []
    
    # 1. JSON-LD içindeki hazır yapısal verileri çekme
    json_ld_tag = soup.find('script', type='application/ld+json')
    if json_ld_tag:
        try:
            ld_data = json.loads(json_ld_tag.text, strict=False)
            dizi_data['isim'] = ld_data.get('name', '')
            dizi_data['gorsel'] = ld_data.get('image', '')
            dizi_data['aciklama'] = ld_data.get('description', '')
            
            if 'aggregateRating' in ld_data:
                dizi_data['imdb'] = ld_data['aggregateRating'].get('ratingValue', '')
            
            if 'actor' in ld_data:
                dizi_data['oyuncular'] = [actor.get('name') for actor in ld_data['actor']]
                
            if 'containsSeason' in ld_data:
                for season in ld_data['containsSeason']:
                    if 'episode' in season:
                        for ep in season['episode']:
                            ep_name = ep.get('name', '')
                            ep_url = ep.get('url', '')
                            if ep_url:
                                bolum_linkleri.append({
                                    "isim": ep_name,
                                    "url": ep_url
                                })
            print(f"[+] Künye verileri ve {len(bolum_linkleri)} bölüm linki başarıyla çekildi.")
            
        except Exception as e:
            print(f"[!] JSON-LD ayrıştırma hatası: {e}")
    else:
        print("[!] JSON verisi (application/ld+json) sayfada bulunamadı.")

    # 2. HTML İçerisinden Tür ve Yıl Bilgilerini Ayıklama
    try:
        yil_tag = soup.select_one('.page-title .light-title')
        if yil_tag:
            dizi_data['yil'] = yil_tag.text.strip('()')
            
        tur_etiketleri = soup.select('.ui.list .item a[href*="/tur/"]')
        dizi_data['tur'] = [tur.text for tur in tur_etiketleri]
    except Exception:
        pass

    # 3. Bölüm Sayfalarına Gidip Okru ve Vidmoly Kaynaklarını Bulma
    for bolum in bolum_linkleri:
        bolum_adi = bolum['isim']
        bolum_url = bolum['url']
        
        kaynaklar = {
            "vidmoly": None,
            "okru": None,
            "sifreli_hashler": []
        }
        
        try:
            print(f"  -> Bölüm taranıyor: {bolum_adi}")
            # Bölüm sayfalarına girerken de taklit yapıyoruz
            b_res = requests.get(bolum_url, impersonate="chrome110")
            b_soup = BeautifulSoup(b_res.text, 'html.parser')
            
            vidmoly_link = b_soup.select_one('.menu a[href*="vidmoly"]')
            if vidmoly_link:
                kaynaklar['vidmoly'] = vidmoly_link.get('href', '')
                
            iframes = b_soup.find_all('iframe')
            for iframe in iframes:
                src = iframe.get('src', '')
                if 'ok.ru' in src or 'okru' in src:
                    kaynaklar['okru'] = src
                if 'vidmoly' in src and not kaynaklar['vidmoly']:
                    kaynaklar['vidmoly'] = src
            
            alt_items = b_soup.select('.alternatives-for-this .item')
            for item in alt_items:
                kaynak_ismi = item.text.strip().lower()
                hash_degeri = item.get('data-link')
                if hash_degeri:
                    kaynaklar['sifreli_hashler'].append({"kaynak": kaynak_ismi, "hash": hash_degeri})
                    
        except Exception as e:
            print(f"  [!] {bolum_adi} taraması başarısız: {e}")
            
        dizi_data['bolumler'].append({
            "bolum_ismi": bolum_adi,
            "bölüm_linki": bolum_url,
            "izleme_kaynaklari": kaynaklar
        })

    return dizi_data

if __name__ == "__main__":
    baslangic_url = "https://yabancidizi.so/dizi/1-happy-family-usa-izle-6"
    sonuc = dizi_verilerini_cek(baslangic_url)
    
    dosya_adi = "dizi_verileri.json"
    with open(dosya_adi, "w", encoding="utf-8") as f:
        json.dump(sonuc, f, ensure_ascii=False, indent=4)
        
    print(f"\n[+] İşlem tamamlandı! Veriler {dosya_adi} dosyasına kaydedildi.")
