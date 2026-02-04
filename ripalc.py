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

# --- HEADERS (Mobile App Simulation) ---
APP_UA = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
HEADERS = {
    "User-Agent": APP_UA,
    "Referer": f"{BASE_URL}/",
    "Origin": BASE_URL,
    "Connection": "keep-alive"
}

def decrypt_data(encrypted_text):
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
    return None

def get_match_links(event):
    links_found = []
    
    # 1. Server se aya hua EXACT naam uthao (spaces aur capitals ke sath)
    raw_slug = event.get('slug', '').strip()
    match_title = event.get('title', 'Cricket Match')
    logo = event.get('eventInfo', {}).get('eventLogo', '')
    
    # 2. Slug ko URL safe banao (Space ko %20 me badlo)
    # Example: "ICC T20 Warm-up 1" -> "ICC%20T20%20Warm-up%201"
    safe_slug = urllib.parse.quote(raw_slug)
    
    print(f"🔎 Scanning: {match_title}")
    print(f"   👉 Target File: {safe_slug}.txt")

    valid_response = None
    
    # Sirf wahi file mangenge jo list me likhi hai
    try:
        url = f"{BASE_URL}/channels/{safe_slug}.txt"
        res = requests.get(url, headers=HEADERS, timeout=6)
        
        if res.status_code == 200 and "google.com" not in res.text and len(res.text) > 50:
            valid_response = res
            print(f"✅ FILE FOUND!")
        else:
            print(f"❌ File missing or blocked.")
    except Exception as e:
        print(f"⚠️ Connection Error: {e}")

    if not valid_response: return []

    # --- PARSING & FORMATTING ---
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

                # Player Headers (Zaroori hai)
                player_headers = f"User-Agent={APP_UA}&Referer={BASE_URL}/"

                # 1. EXTINF (Sabse Pehle)
                entry = f'#EXTINF:-1 tvg-logo="{logo}" group-title="{match_title}", {stream_title}\n'
                
                # 2. DRM / License Info
                drm_key = s.get('api')
                if drm_key:
                    entry += '#KODIPROP:inputstream.adaptive.license_type=clearkey\n'
                    entry += f'#KODIPROP:inputstream.adaptive.license_key={drm_key}\n'
                    entry += f'#EXTVLCOPT:http-user-agent={APP_UA}\n'
                
                # 3. URL + Headers
                entry += f'{url}|{player_headers}\n'
                
                links_found.append(entry)
                
    except Exception as e:
        print(f"Parsing Error: {e}")
        
    return links_found

def main():
    if not BASE_URL: return
    print("🚀 Connecting (Smart Slug Mode)...")
    all_entries = []
    
    try:
        # Step 1: Main List Uthao
        response = requests.get(f"{BASE_URL}/categories/live-events.txt", headers=HEADERS, timeout=30)
        decrypted_list = decrypt_data(response.text)
        if not decrypted_list: return
        
        events = json.loads(decrypted_list)
        print(f"📋 Found {len(events)} events in total.")

        # Step 2: Sirf Cricket Filter Karo
        for event in events:
            cat = event.get('eventInfo', {}).get('eventCat', '').lower()
            title = event.get('title', '').lower()
            
            # Filter Logic: Cricket Category OR Cricket Title
            if "cricket" in cat or "warm" in title or "ind" in title or "t20" in title:
                all_entries.extend(get_match_links(event))

        # Step 3: Playlist Save
        with open("playlist.m3u", "w", encoding='utf-8') as f:
            f.write("#EXTM3U\n")
            for entry in all_entries:
                f.write(entry)
        
        print(f"🎉 Playlist Updated: {len(all_entries)} streams added.")
        
    except Exception as e:
        print(f"Critical Error: {e}")

if __name__ == "__main__":
    main()
