import requests
import base64
import json
import os
import urllib.parse
from datetime import datetime, timedelta
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# ==========================================
# 🌟 FIREBASE AUTO-URL ENGINE (Added Active Check)
# ==========================================
def get_firebase_base_url():
    print("🔵 [Auto] Fetching Dynamic URL from Firebase...")
    url = "https://firebaseremoteconfig.googleapis.com/v1/projects/963020218535/namespaces/firebase:fetch"
    
    headers = {
        "accept": "application/json",
        "x-android-package": "com.cricfy.tv",
        "x-goog-api-key": "AIzaSyAh9jkEU0E_UYxH0m_BKAt-uUSTiTPqhb8",
        "content-type": "application/json; charset=utf-8",
        "user-agent": "okhttp/5.0.0-alpha.12"
    }
    
    payload = {
        "appInstanceId": "e368b85dbdd148bdb73f1c5fecfdd3e2",
        "appInstanceIdToken": "",
        "appId": "1:963020218535:android:47ec53252c64fb3c9c7b82",
        "countryCode": "US",
        "languageCode": "en-US",
        "platformVersion": "30",
        "timeZone": "UTC",
        "appVersion": "5.0",
        "appBuild": "50",
        "packageName": "com.cricfy.tv",
        "sdkVersion": "22.1.0",
        "analyticsUserProperties": {}
    }
    
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        if res.status_code == 200:
            data = res.json()
            entries = data.get("entries", {})
            
            # Dono URLs nikal liye
            url1 = entries.get("cric_api1")
            url2 = entries.get("cric_api2")
            
            # Active Link Checker (Jo zinda hoga wahi return karega)
            for api_url in [url1, url2]:
                if api_url:
                    clean_url = api_url.rstrip("/")
                    print(f"   🔄 Checking URL: {clean_url} ...")
                    try:
                        # 3 second timeout ke sath check karega ki site chal rahi hai ya nahi
                        requests.get(clean_url, timeout=3)
                        print(f"   🎉 SUCCESS! Active Auto-URL Detected: {clean_url}")
                        return clean_url
                    except requests.exceptions.RequestException:
                        print(f"   ⚠️ URL {clean_url} is dead/blocked. Trying next...")
                        continue # Pehla fail hua to loop dusre par jayega
                        
    except Exception as e:
        print(f"   ❌ Firebase Error: {e}")
        
    print("   ⚠️ Fetch failed or all URLs dead. Using fallback URL.")
    # Fallback ko abhi working wale pe set kar diya hai just in case
    return "https://cfykskgdjk100.top"

# --- CONFIGURATION ---
# Base URL ab Github secrets ki jagah seedha Firebase se aayega
BASE_URL = get_firebase_base_url()
KEYS_LIST = []

k1 = os.getenv("CRIC_KEY_1")
i1 = os.getenv("CRIC_IV_1")
if k1 and i1: KEYS_LIST.append({ "key": k1, "iv": i1 })

k2 = os.getenv("CRIC_KEY_2")
i2 = os.getenv("CRIC_IV_2")
if k2 and i2: KEYS_LIST.append({ "key": k2, "iv": i2 })

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Referer": f"{BASE_URL}/",
    "Origin": BASE_URL,
    "Connection": "keep-alive"
}

# --- HELPER FUNCTIONS ---

def decrypt_data(encrypted_text):
    if not encrypted_text: return None
    try:
        clean_b64 = encrypted_text.strip().replace("\n", "").replace("\r", "").replace(" ", "").replace("\t", "")
        for creds in KEYS_LIST:
            try:
                k = bytes.fromhex(creds["key"])
                i = bytes.fromhex(creds["iv"])
                ciphertext = base64.b64decode(clean_b64)
                cipher = AES.new(k, AES.MODE_CBC, i)
                return unpad(cipher.decrypt(ciphertext), AES.block_size).decode('utf-8')
            except:
                continue
    except:
        pass
    return None

def convert_utc_to_ist(utc_time_str):
    try:
        if not utc_time_str: return ""
        clean_time = utc_time_str.split(" +")[0]
        utc_dt = datetime.strptime(clean_time, "%Y/%m/%d %H:%M:%S")
        ist_dt = utc_dt + timedelta(hours=5, minutes=30)
        return ist_dt.strftime("%I:%M %p")
    except:
        return ""

def get_smart_filename(event):
    guesses = []
    
    # 1. Event ID
    eid = str(event.get('id', ''))
    if eid:
        guesses.append(eid)
        guesses.append(f"match-{eid}")
    
    # 2. Slug & Title (FORCE LOWERCASE FIX HERE)
    # Humne .lower() laga diya hai taaki 'ICC' ban jaye 'icc'
    slug = event.get('slug', '').strip().lower()
    
    if slug:
        # A. Normal Slug
        guesses.append(slug) 
        guesses.append(urllib.parse.quote(slug)) 
        guesses.append(slug.replace(" ", "-")) 
        
        # B. Numbered Variations (1 to 6)
        for i in range(1, 7):
            # Try: "icc t20 world cup 1" -> "icc%20t20...%201.txt"
            guesses.append(urllib.parse.quote(f"{slug} {i}"))
            
            # Try: "icc-t20-world-cup-1.txt"
            guesses.append(f"{slug.replace(' ', '-')}-{i}")
    
    # 3. Team Names (Also Lowercase)
    team_a = event.get('eventInfo', {}).get('teamA', '').strip().lower()
    team_b = event.get('eventInfo', {}).get('teamB', '').strip().lower()
    
    if team_a and team_b:
        t_a = team_a.replace(" ", "")
        t_b = team_b.replace(" ", "")
        base_vs = f"{t_a}-vs-{t_b}"
        guesses.append(base_vs)
        
        for i in range(1, 4):
            guesses.append(f"{base_vs}-{i}")
        
    return guesses

def fetch_match_streams(event):
    entries = []
    title = event.get('title', 'Cricket Match')
    logo = event.get('eventInfo', {}).get('eventLogo', '')
    ist_time = convert_utc_to_ist(event.get('startTime', ''))
    group_title = f"{title} [{ist_time}]" if ist_time else title

    print(f"   🏏 Processing: {group_title}")

    valid_data = None
    filenames = get_smart_filename(event)
    
    for fname in filenames:
        try:
            for ext in [".txt", ""]:
                url = f"{BASE_URL}/channels/{fname}{ext}"
                res = requests.get(url, headers=HEADERS, timeout=3)
                if res.status_code == 200 and "google.com" not in res.text and len(res.text) > 50:
                    valid_data = decrypt_data(res.text)
                    if valid_data: 
                        print(f"      ✅ FOUND: {fname}{ext}")
                        break
            if valid_data: break
        except:
            continue

    if not valid_data:
        print("      ❌ No stream file found.")
        return []

    try:
        data = json.loads(valid_data)
        streams = data.get('streamUrls', [])
        
        for s in streams:
            stream_name = s.get('title', 'Link')
            raw_link = s.get('link', '')
            final_url = raw_link

            entry = f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group_title}", {title} ({stream_name})\n'
            drm_key = s.get('api')
            if drm_key:
                entry += '#KODIPROP:inputstream.adaptive.license_type=clearkey\n'
                entry += f'#KODIPROP:inputstream.adaptive.license_key={drm_key}\n'
            entry += f'{final_url}\n'
            entries.append(entry)

    except Exception as e:
        print(f"      ⚠️ JSON Error: {e}")

    return entries

def main():
    print("🚀 Starting Generator (Lowercase Fix + Smart Numbering)...")
    all_entries = []
    
    try:
        if not BASE_URL or not KEYS_LIST:
            print("❌ Error: CRIC Secrets missing! Check GitHub Settings.")
            return

        res = requests.get(f"{BASE_URL}/categories/live-events.txt", headers=HEADERS, timeout=15)
        if res.status_code != 200:
            print(f"❌ Failed to fetch categories: {res.status_code}")
            return
            
        raw_data = decrypt_data(res.text)
        if not raw_data: 
            print("❌ Category Decryption Failed")
            return

        events = json.loads(raw_data)
        
        for event in events:
            cat = event.get('eventInfo', {}).get('eventCat', '').lower()
            title = event.get('title', '').lower()
            
            if 'cricket' in cat or 'cricket' in title or 'ind' in title or 'zim' in title or 'warm' in title:
                match_entries = fetch_match_streams(event)
                all_entries.extend(match_entries)

        timestamp = (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime('%Y-%m-%d %I:%M %p IST')
        
        with open("playlist.m3u", "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            f.write(f"# UPDATED: {timestamp}\n\n")
            for entry in all_entries:
                f.write(entry)
        
        print(f"🎉 Playlist Updated! {len(all_entries)} streams.")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()

