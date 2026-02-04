import base64
import requests
import json
import os
import urllib.parse
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# --- CONFIGURATION ---
BASE_URL = os.environ.get("BASE_URL")
KEYS_LIST = []
if os.environ.get("KEY_HEX"): 
    KEYS_LIST.append({ "key": os.environ.get("KEY_HEX"), "iv": os.environ.get("IV_HEX") })
if os.environ.get("KEY_HEX_2"): 
    KEYS_LIST.append({ "key": os.environ.get("KEY_HEX_2"), "iv": os.environ.get("IV_HEX_2") })

# --- HEADERS ---
APP_UA = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
HEADERS = {
    "User-Agent": APP_UA,
    "Referer": f"{BASE_URL}/",
    "Origin": BASE_URL,
    "Connection": "keep-alive"
}

def decrypt_data(encrypted_text):
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

def get_match_links(event):
    links_found = []
    
    raw_slug = event.get('slug', '').strip()
    match_title = event.get('title', 'Cricket Match')
    logo = event.get('eventInfo', {}).get('eventLogo', '')
    
    if not raw_slug: return []

    # --- TRIALS: Server ke nakhre handle karne ke liye 3 tarike ---
    slug_variations = [
        urllib.parse.quote(raw_slug),         # 1. Standard: ICC%20T20...
        raw_slug,                             # 2. Raw: ICC T20... (Requests handle karega)
        raw_slug.replace(" ", "+"),           # 3. Plus: ICC+T20...
        raw_slug.lower().replace(" ", "-"),   # 4. Hyphen: icc-t20...
    ]

    print(f"🔎 Scanning: {match_title}")
    
    valid_response = None
    
    # Har variation try karo jab tak file na mile
    for s in slug_variations:
        try:
            url = f"{BASE_URL}/channels/{s}.txt"
            res = requests.get(url, headers=HEADERS, timeout=5)
            
            if res.status_code == 200 and "google.com" not in res.text and len(res.text) > 50:
                print(f"✅ FILE FOUND using: {s}.txt")
                valid_response = res
                break # Mil gaya! Loop roko.
        except:
            continue

    if not valid_response:
        print(f"❌ Failed to find file for: {raw_slug}")
        return []

    # --- PARSING ---
    try:
        dec_links = decrypt_data(valid_response.text)
        if dec_links:
            streams = json.loads(dec_links).get('streamUrls', [])
            for s in streams:
                stream_title = s.get('title', 'Source')
                raw_link = s.get('link', '')
                
                if '|' in raw_link:
                    url = raw_link.split('|')[0]
                else:
                    url = raw_link

                player_headers = f"User-Agent={APP_UA}&Referer={BASE_URL}/"

                # M3U Entry Construction
                entry = f'#EXTINF:-1 tvg-logo="{logo}" group-title="{match_title}", {stream_title}\n'
                
                drm_key = s.get('api')
                if drm_key:
                    entry += '#KODIPROP:inputstream.adaptive.license_type=clearkey\n'
                    entry += f'#KODIPROP:inputstream.adaptive.license_key={drm_key}\n'
                    entry += f'#EXTVLCOPT:http-user-agent={APP_UA}\n'
                
                entry += f'{url}|{player_headers}\n'
                links_found.append(entry)
                
    except Exception as e:
        print(f"Parsing Error: {e}")
        
    return links_found

def main():
    if not BASE_URL: return
    print("🚀 Connecting (Multi-Try Mode)...")
    all_entries = []
    
    try:
        response = requests.get(f"{BASE_URL}/categories/live-events.txt", headers=HEADERS, timeout=30)
        decrypted_list = decrypt_data(response.text)
        if not decrypted_list: return
        
        events = json.loads(decrypted_list)
        print(f"📋 Found {len(events)} events.")

        for event in events:
            cat = event.get('eventInfo', {}).get('eventCat', '').lower()
            title = event.get('title', '').lower()
            
            # Wahi filter jo pehle kaam kar raha tha
            if "cricket" in cat or "warm" in title or "ind" in title or "t20" in title:
                all_entries.extend(get_match_links(event))

        with open("playlist.m3u", "w", encoding='utf-8') as f:
            f.write("#EXTM3U\n")
            for entry in all_entries:
                f.write(entry)
        
        print(f"🎉 Playlist Updated: {len(all_entries)} streams added.")
        
    except Exception as e:
        print(f"Critical Error: {e}")

if __name__ == "__main__":
    main()
