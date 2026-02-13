import requests
import base64
import json
import os
import urllib.parse
from datetime import datetime, timedelta
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# --- CONFIGURATION ---
BASE_URL = os.environ.get("BASE_URL", "https://cfyhsgskskb96.top")

# Decryption Keys
KEYS_LIST = [
    { "key": "3368487a78594167534749382f68616d", "iv": "557143766b766a656345497a38343256" },
    { "key": "4d7165594743543441594b6f484b7254", "iv": "6f484b725451755078387a6c386f4a2b" }
]

# Headers for FETCHING the list (Server se baat karne ke liye zaroori hai)
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
    """Filename Guesser"""
    guesses = []
    
    # 1. Event ID
    eid = str(event.get('id', ''))
    if eid:
        guesses.append(eid)
        guesses.append(f"match-{eid}")
    
    # 2. Slug
    slug = event.get('slug', '').strip()
    if slug:
        guesses.append(slug)
        guesses.append(urllib.parse.quote(slug))
        guesses.append(slug.replace(" ", "-").lower())
    
    # 3. Team Names
    team_a = event.get('eventInfo', {}).get('teamA', '').strip()
    team_b = event.get('eventInfo', {}).get('teamB', '').strip()
    
    if team_a and team_b:
        t_a = team_a.lower().replace(" ", "")
        t_b = team_b.lower().replace(" ", "")
        guesses.append(f"{t_a}-vs-{t_b}")
        guesses.append(f"{t_a}-v-{t_b}")
        guesses.append(f"{t_a}{t_b}")
        
    return guesses

def fetch_match_streams(event):
    entries = []
    
    title = event.get('title', 'Cricket Match')
    logo = event.get('eventInfo', {}).get('eventLogo', '')
    
    # Time Grouping
    ist_time = convert_utc_to_ist(event.get('startTime', ''))
    group_title = f"{title} [{ist_time}]" if ist_time else title

    print(f"   🏏 Processing: {group_title}")

    # Hunt for File
    valid_data = None
    filenames = get_smart_filename(event)
    
    for fname in filenames:
        try:
            for ext in [".txt", ""]:
                url = f"{BASE_URL}/channels/{fname}{ext}"
                res = requests.get(url, headers=HEADERS, timeout=3)
                if res.status_code == 200 and "google.com" not in res.text and len(res.text) > 50:
                    valid_data = decrypt_data(res.text)
                    if valid_data: break
            if valid_data: break
        except:
            continue

    if not valid_data:
        return []

    # Parse JSON
    try:
        data = json.loads(valid_data)
        streams = data.get('streamUrls', [])
        
        for s in streams:
            stream_name = s.get('title', 'Link')
            raw_link = s.get('link', '')
            
            # --- STRICT RAW MODE: Use Link As-Is ---
            # Hum kuch nahi jodenge. Agar JSON me headers hain to wo 'raw_link' me hi honge.
            # Agar nahi hain, to nahi honge.
            final_url = raw_link

            # --- M3U Construction ---
            # 1. EXTINF
            entry = f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group_title}", {title} ({stream_name})\n'
            
            # 2. KODIPROP (DRM Keys are necessary for player to know how to unlock)
            drm_key = s.get('api')
            if drm_key:
                entry += '#KODIPROP:inputstream.adaptive.license_type=clearkey\n'
                entry += f'#KODIPROP:inputstream.adaptive.license_key={drm_key}\n'
            
            # 3. URL (The Raw Link)
            entry += f'{final_url}\n'
            
            entries.append(entry)

    except Exception as e:
        print(f"      ⚠️ Error: {e}")

    return entries

def main():
    print("🚀 Starting Generator (Strict Raw Mode)...")
    all_entries = []
    
    try:
        res = requests.get(f"{BASE_URL}/categories/live-events.txt", headers=HEADERS, timeout=15)
        raw_data = decrypt_data(res.text)
        
        if not raw_data: return

        events = json.loads(raw_data)
        
        for event in events:
            # Filter
            cat = event.get('eventInfo', {}).get('eventCat', '').lower()
            title = event.get('title', '').lower()
            
            if 'cricket' in cat or 'cricket' in title or 'ind' in title or 'zim' in title or 'warm' in title:
                match_entries = fetch_match_streams(event)
                all_entries.extend(match_entries)

        # Save
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

