import requests
import json
import os
from datetime import datetime

# Klasör yoksa oluştur
if not os.path.exists('data'):
    os.makedirs('data')

# ESPN Gizli API Uç Noktaları (Şifresiz ve Ücretsiz)
LEAGUES = {
    "football": [
        {"name": "Süper Lig", "url": "https://site.api.espn.com/apis/site/v2/sports/football/soccer.tur.1/scoreboard"},
        {"name": "Premier League", "url": "https://site.api.espn.com/apis/site/v2/sports/football/soccer.eng.1/scoreboard"},
        {"name": "La Liga", "url": "https://site.api.espn.com/apis/site/v2/sports/football/soccer.esp.1/scoreboard"},
        {"name": "Serie A", "url": "https://site.api.espn.com/apis/site/v2/sports/football/soccer.ita.1/scoreboard"},
        {"name": "Bundesliga", "url": "https://site.api.espn.com/apis/site/v2/sports/football/soccer.ger.1/scoreboard"},
        {"name": "Şampiyonlar Ligi", "url": "https://site.api.espn.com/apis/site/v2/sports/football/soccer.uefa.champions/scoreboard"}
    ],
    "basketball": [
        {"name": "NBA", "url": "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"},
        {"name": "EuroLeague", "url": "https://site.api.espn.com/apis/site/v2/sports/basketball/euroleague/scoreboard"}
    ]
}

def fetch_matches_from_api(sport_type):
    all_matches = []
    league_names = []
    
    for league in LEAGUES[sport_type]:
        league_names.append(league["name"])
        print(f"{league['name']} verileri çekiliyor...")
        
        try:
            # İnternetten gerçek veriyi çek
            response = requests.get(league["url"], timeout=15)
            data = response.json()
            
            events = data.get('events', [])
            for event in events:
                try:
                    competition = event['competitions'][0]
                    competitors = competition['competitors']
                    
                    # Ev sahibi ve deplasman takımlarını ayır
                    team1 = competitors[0]
                    team2 = competitors[1]
                    
                    home_team = team1 if team1['homeAway'] == 'home' else team2
                    away_team = team2 if team2['homeAway'] == 'away' else team1
                    
                    home_name = home_team['team']['shortDisplayName']
                    away_name = away_team['team']['shortDisplayName']
                    
                    home_score = home_team.get('score', '-')
                    away_score = away_team.get('score', '-')
                    
                    # Maç Durumunu Çözümle
                    status_type = event['status']['type']
                    state = status_type['state'] # 'pre', 'in', 'post'
                    time_detail = status_type['shortDetail'] 
                    
                    if state == 'pre':
                        match_status = 'upcoming'
                    elif state == 'in':
                        match_status = 'live'
                    else:
                        match_status = 'finished'
                        time_detail = 'MS'
                    
                    # Tarih işlemleri
                    match_date_str = event['date'] # Format: 2024-05-22T19:00:00Z
                    is_today = "Bugün" in time_detail or state == 'in'
                    date_display = "Bugün" if is_today else match_date_str[:10]

                    all_matches.append({
                        "id": event['id'],
                        "league": league["name"],
                        "home": home_name,
                        "away": away_name,
                        "scoreH": home_score,
                        "scoreA": away_score,
                        "status": match_status,
                        "time": time_detail,
                        "date": date_display,
                        "isToday": is_today
                    })
                except Exception as e:
                    print(f"Bir maç islenirken hata olustu: {e}")
                    continue
                    
        except Exception as e:
            print(f"{league['name']} icin baglanti hatasi: {e}")
            
    return league_names, all_matches

def generate_global_db():
    print("Dünya çapında spor verileri toplanıyor. Lütfen bekleyin...")
    
    fb_leagues, fb_matches = fetch_matches_from_api("football")
    bb_leagues, bb_matches = fetch_matches_from_api("basketball")
    
    # Tüm sitenin besleneceği JSON
    db = {
        "football": {
            "leagues": fb_leagues,
            "standings": {
                "Süper Lig": [
                    {"rank": 1, "team": "Galatasaray", "p": 38, "w": 33, "d": 3, "l": 2, "pts": 102},
                    {"rank": 2, "team": "Fenerbahçe", "p": 38, "w": 31, "d": 6, "l": 1, "pts": 99},
                    {"rank": 3, "team": "Trabzonspor", "p": 38, "w": 21, "d": 4, "l": 13, "pts": 67},
                    {"rank": 4, "team": "Başakşehir", "p": 38, "w": 18, "d": 7, "l": 13, "pts": 61}
                ],
                "Premier League": [
                    {"rank": 1, "team": "Man City", "p": 38, "w": 28, "d": 7, "l": 3, "pts": 91},
                    {"rank": 2, "team": "Arsenal", "p": 38, "w": 28, "d": 5, "l": 5, "pts": 89}
                ]
            },
            "matches": fb_matches
        },
        "basketball": {
            "leagues": bb_leagues,
            "standings": {
                "EuroLeague": [
                    {"rank": 1, "team": "Real Madrid", "p": 34, "w": 27, "d": 0, "l": 7, "pts": 54},
                    {"rank": 2, "team": "Panathinaikos", "p": 34, "w": 23, "d": 0, "l": 11, "pts": 46}
                ]
            },
            "matches": bb_matches
        },
        "news": [
            {"id": 1, "tag": "SİSTEM MESAJI", "title": "Gerçek Zamanlı ESPN Veri Motoru Aktif", "summary": "Dünya çapındaki tüm maçlar Python botu tarafından otomatik çekiliyor.", "time": "Şimdi"},
            {"id": 2, "tag": "GÜNCELLEME", "title": "Veriler Senkronize Edildi", "summary": f"Son güncelleme saati: {datetime.now().strftime('%H:%M:%S')}", "time": "Yeni"}
        ],
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    with open('data/db.json', 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=4)
        
    print(f"Toplam {len(fb_matches) + len(bb_matches)} mac verisi basariyla kaydedildi.")

if __name__ == "__main__":
    generate_global_db()