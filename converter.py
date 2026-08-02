import os
import json
import requests
import re

# Sana ait olan JSON verisi (Eğer bu veri bir dosyadaysa json.load() ile de okutabilirsin)
plugin_data = [
    # Buraya senin verdiğin JSON listesinin tamamını koymalısın.
    # Örnek olarak birkaç tanesini ekliyorum, sen tam listeyi buraya yapıştır.
    {
        "url": "https://raw.githubusercontent.com/Kraptor123/cs-kraptor/builds/AnimeciX.cs3",
        "name": "AnimeciX"
    },
    {
        "url": "https://raw.githubusercontent.com/Kraptor123/cs-kraptor/builds/Animeler.cs3",
        "name": "Animeler"
    }
    # ... DİĞER TÜM JSON VERİLERİ ...
]

# Çıktıların kaydedileceği klasörü oluştur
OUTPUT_DIR = "kotlin_src"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def cs3_to_kotlin(cs3_code, plugin_name):
    """
    C# / CS3 sözdizimini temel düzeyde Kotlin sözdizimine dönüştürür.
    """
    kt_code = cs3_code
    
    # 1. Temel Sınıf ve Değişken Tanımları
    kt_code = kt_code.replace("public class", "class")
    kt_code = kt_code.replace("public override", "override")
    kt_code = kt_code.replace("public virtual", "open")
    
    # 2. Veri Tipleri Dönüşümü (C# -> Kotlin)
    kt_code = re.sub(r'\bstring\b', 'String', kt_code)
    kt_code = re.sub(r'\bbool\b', 'Boolean', kt_code)
    kt_code = re.sub(r'\bint\b', 'Int', kt_code)
    kt_code = re.sub(r'\bvoid\b', 'Unit', kt_code)
    
    # 3. Metot (Fonksiyon) Dönüşümleri
    # Örnek: public string GetName() -> fun GetName(): String
    kt_code = re.sub(r'public\s+([A-Z][a-zA-Z0-9_]*)\s+([a-zA-Z0-9_]+)\s*\(', r'fun \2(): \1 { // TODO: Parametreleri kontrol et\n', kt_code)
    
    # 4. Liste ve Dizi Dönüşümleri
    kt_code = kt_code.replace("List<", "MutableList<")
    kt_code = kt_code.replace("new List", "mutableListOf")
    
    # 5. Nullable operatörler ve diğer ufak syntax değişiklikleri
    kt_code = kt_code.replace("null", "null") # Aynı ama case-sensitive kontrol
    kt_code = kt_code.replace("==", "==")
    
    # Yorum satırı olarak eklentinin adını en başa yazalım
    header = f"// Otomatik dönüştürüldü: {plugin_name}.cs3 -> {plugin_name}.kt\npackage com.kraptor.plugins\n\n"
    
    return header + kt_code

def main():
    print("Dönüştürme işlemi başlıyor...")
    
    for item in plugin_data: # Tam listeyi kullanacaksan 'plugin_data' değişkenini döngüye sok
        url = item.get("url")
        name = item.get("name")
        
        if not url or not name:
            continue
            
        print(f"İndiriliyor: {name} ({url})")
        
        try:
            # CS3 dosyasını indir
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                cs3_content = response.text
                
                # Kodu Kotlin'e çevir
                kt_content = cs3_to_kotlin(cs3_content, name)
                
                # Dosyayı kaydet
                file_path = os.path.join(OUTPUT_DIR, f"{name}.kt")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(kt_content)
                    
                print(f"Başarılı: {name}.kt oluşturuldu.")
            else:
                print(f"Hata: {name} indirilemedi. HTTP Kodu: {response.status_code}")
                
        except Exception as e:
            print(f"Hata oluştu ({name}): {e}")

if __name__ == "__main__":
    main()
