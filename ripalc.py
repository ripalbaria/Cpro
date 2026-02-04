import base64
import requests
import json
import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# --- SECURITY ---
BASE_URL = os.environ.get("BASE_URL")
KEYS_LIST = [
    { "key": os.environ.get("KEY_HEX"), "iv": os.environ.get("IV_HEX") },
    { "key": os.environ.get("KEY_HEX_2"), "iv": os.environ.get("IV_HEX_2") }
]

# --- IMPROVED HEADERS (To bypass Google Redirect) ---
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Referer": f"{BASE_URL}/",
    "Origin": BASE_URL,
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive"
}

def decrypt_data(encrypted_text):
    for creds in KEYS_LIST:
        try:
            k = bytes.fromhex(creds["key"])
            i = bytes.fromhex(creds["iv"])
            clean_b64 = encrypted_text.strip().replace("\n", "").replace("\r", "").replace(" ", "")
            ciphertext = base64.b64decode(clean_b64)
            cipher = AES.new(k, AES.MODE_CBC, i)
            return unpad(cipher.decrypt(ciphertext), AES.block_size).decode('utf-8')
        except:
            continue
    return None

def get_match_links(event):
    links_found = []
    
    slug = event.get('slug', '').strip()
    match_title = event.get('title', 'Cricket Match')
    logo = event.get('eventInfo', {}).get('eventLogo', '')
    
    # Teams Info (Example: AFG vs WI)
    team_a = event.get('eventInfo', {}).get('teamA', '').lower().replace(" ", "")
    team_b = event.get('eventInfo', {}).get('teamB', '').lower().replace(" ", "")
    
    possible_slugs = []

    # 1. JSON Slug (Priority) -> icc-t20-warm-up-2
    if slug:
        possible_slugs.append(slug.lower().replace(" ", "-")) 
        possible_slugs.append(slug.replace(" ", "%20"))
    
    # 2. Team Based (CloudStream Style) -> afg-vs-wi
    if team_a and team_b:
        possible_slugs.append(f"{team_a}-vs-{team_b}")
        possible_slugs.append(f"{team_b}-vs-{team_a}")
    
    # 3. Fallback -> icc-t20-warm-up-2 (Standard format)
    possible_slugs.append("icc-t20-warm-up-2") 

    print(f"🔎 Checking {match_title}...")

    valid_response = None
    used_slug = ""
    
    for s in possible_slugs:
        try:
            ch_url = f"{BASE_URL}/channels/{s}.txt"
            res = requests.get(ch_url, headers=HEADERS, timeout=5)
            
            # Google Redirect aur Empty responses ko filter karo
            if res.status_code == 200 and "google.com" not in res.text:
                if len(res.text) > 50: # Valid encrypted text
                    valid_response = res
                    used_slug = s
                    print(f"✅ LINK FOUND: {s}")
                    break
        except:
            continue

    if not valid_response:
        print(f"⚠️ Skipped: No valid file found for {match_title}")
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
                    url, headers = raw_link.split('|')
                else:
                    url, headers = raw_link, ""

                # Headers merge logic
                h_list = []
                if "User-Agent" not in headers: h_list.append(f"User-Agent={HEADERS['User-Agent']}")
                if headers: h_list.append(headers)
                final_headers = "&".join(h_list)

                # License logic
                entry = f'#EXTINF:-1 tvg-logo="{logo}" group-title="{match_title}", {stream_title}\n'
                drm_key = s.get('api')
                if drm_key:
                    entry = f'#KODIPROP:inputstream.adaptive.license_type=clearkey\n#KODIPROP:inputstream.adaptive.license_key={drm_key}\n' + entry
                
                if final_headers:
                    entry += f'{url}|{final_headers}\n'
                else:
                    entry += f'{url}\n'
                    
                links_found.append(entry)
    except Exception as e:
        print(f"Parsing Error: {e}")
        
    return links_found

def main():
    if not BASE_URL: return
    print("🚀 Connecting with CloudStream Headers...")
    all_entries = []
    
    try:
        response = requests.get(f"{BASE_URL}/categories/live-events.txt", headers=HEADERS, timeout=30)
        
        # Check if Main List is also redirecting
        if "google.com" in response.text:
            print("❌ Error: Main list redirected to Google. Server blocked IP/UA.")
            return

        decrypted_list = decrypt_data(response.text)
        if not decrypted_list: return
        
        events = json.loads(decrypted_list)
        print(f"✅ Found {len(events)} events.")

        for event in events:
            # Filter for Cricket
            cat = event.get('eventInfo', {}).get('eventCat', '').lower()
            if "cricket" in cat:
                all_entries.extend(get_match_links(event))

        with open("playlist.m3u", "w", encoding='utf-8') as f:
            f.write("#EXTM3U\n")
            for entry in all_entries:
                f.write(entry)
        
        print(f"🎉 Updated: {len(all_entries)} streams found.")
        
    except Exception as e:
        print(f"Critical Error: {e}")

if __name__ == "__main__":
    main()

