import base64
import requests
import json
import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# --- SECURITY ---
BASE_URL = os.environ.get("BASE_URL")
# Load Keys from Secrets
KEYS_LIST = []
if os.environ.get("KEY_HEX"): 
    KEYS_LIST.append({ "key": os.environ.get("KEY_HEX"), "iv": os.environ.get("IV_HEX") })
if os.environ.get("KEY_HEX_2"): 
    KEYS_LIST.append({ "key": os.environ.get("KEY_HEX_2"), "iv": os.environ.get("IV_HEX_2") })

# Headers (Browser Mode)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": f"{BASE_URL}/",
    "Origin": BASE_URL,
    "Accept": "*/*",
    "Connection": "keep-alive"
}

# --- TEAM NAMES DICTIONARY ---
TEAM_MAP = {
    "ind": "india", "sa": "south-africa", "aus": "australia",
    "eng": "england", "nz": "new-zealand", "pak": "pakistan",
    "wi": "west-indies", "afg": "afghanistan", "sl": "sri-lanka",
    "ban": "bangladesh", "ire": "ireland", "zim": "zimbabwe",
    "ned": "netherlands", "nep": "nepal", "sco": "scotland",
    "nam": "namibia", "usa": "usa", "can": "canada",
    "png": "papua-new-guinea", "oma": "oman", "uga": "uganda"
}

def decrypt_data(encrypted_text):
    # 1. Clean the Data (Exactly like Debug Script)
    clean_b64 = encrypted_text.strip()
    clean_b64 = clean_b64.replace("\n", "").replace("\r", "").replace(" ", "").replace("\t", "")
    
    # 2. Try All Keys
    for creds in KEYS_LIST:
        try:
            k = bytes.fromhex(creds["key"])
            i = bytes.fromhex(creds["iv"])
            
            ciphertext = base64.b64decode(clean_b64)
            cipher = AES.new(k, AES.MODE_CBC, i)
            decrypted = unpad(cipher.decrypt(ciphertext), AES.block_size).decode('utf-8')
            return decrypted
        except:
            continue
    return None

def get_full_team_name(code):
    return TEAM_MAP.get(code.lower().strip(), code.lower().strip())

def get_match_links(event):
    links_found = []
    
    slug = event.get('slug', '').strip()
    match_title = event.get('title', 'Cricket Match')
    logo = event.get('eventInfo', {}).get('eventLogo', '')
    event_id = str(event.get('id', ''))
    
    # Team Logic
    team_a_code = event.get('eventInfo', {}).get('teamA', '').lower().replace(" ", "")
    team_b_code = event.get('eventInfo', {}).get('teamB', '').lower().replace(" ", "")
    
    team_a_full = get_full_team_name(team_a_code)
    team_b_full = get_full_team_name(team_b_code)
    
    possible_slugs = []

    # Priority 1: Full Names (e.g. india-vs-south-africa) - Sabse zaroori
    if team_a_full and team_b_full:
        possible_slugs.append(f"{team_a_full}-vs-{team_b_full}")
        possible_slugs.append(f"{team_b_full}-vs-{team_a_full}")

    # Priority 2: Short Names (e.g. ind-vs-sa)
    if team_a_code and team_b_code:
        possible_slugs.append(f"{team_a_code}-vs-{team_b_code}")
    
    # Priority 3: Original Slug
    if slug:
        possible_slugs.append(slug.lower().replace(" ", "-"))
        possible_slugs.append(slug.replace(" ", "%20"))

    # Priority 4: Event ID
    if event_id:
        possible_slugs.append(event_id)

    print(f"🔎 Scanning {match_title}...")

    valid_response = None
    
    for s in possible_slugs:
        try:
            ch_url = f"{BASE_URL}/channels/{s}.txt"
            res = requests.get(ch_url, headers=HEADERS, timeout=4)
            
            if res.status_code == 200 and "google.com" not in res.text:
                if len(res.text) > 50:
                    valid_response = res
                    print(f"✅ LINK FOUND: {s}")
                    break
        except:
            continue

    if not valid_response:
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

                # Headers merge
                h_list = []
                if "User-Agent" not in headers: h_list.append(f"User-Agent={HEADERS['User-Agent']}")
                if headers: h_list.append(headers)
                final_headers = "&".join(h_list)

                # License Logic
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
    print("🚀 Connecting (Final Production Mode)...")
    all_entries = []
    
    try:
        response = requests.get(f"{BASE_URL}/categories/live-events.txt", headers=HEADERS, timeout=30)
        decrypted_list = decrypt_data(response.text)
        if not decrypted_list: return
        
        events = json.loads(decrypted_list)
        print(f"✅ Found {len(events)} events.")

        for event in events:
            cat = event.get('eventInfo', {}).get('eventCat', '').lower()
            # Filter for Cricket
            if "cricket" in cat:
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
