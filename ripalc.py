import base64
import requests
import json
import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# --- SECURITY ---
BASE_URL = os.environ.get("BASE_URL")
KEYS_LIST = []
if os.environ.get("KEY_HEX"): 
    KEYS_LIST.append({ "key": os.environ.get("KEY_HEX"), "iv": os.environ.get("IV_HEX") })
if os.environ.get("KEY_HEX_2"): 
    KEYS_LIST.append({ "key": os.environ.get("KEY_HEX_2"), "iv": os.environ.get("IV_HEX_2") })

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": f"{BASE_URL}/",
    "Origin": BASE_URL,
    "Accept": "*/*",
    "Connection": "keep-alive"
}

# --- TEAM MAPPER ---
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

def get_full_team_name(code):
    return TEAM_MAP.get(code.lower().strip(), code.lower().strip())

def get_match_links(event):
    links_found = []
    
    slug = event.get('slug', '').strip()
    match_title = event.get('title', 'Cricket Match')
    logo = event.get('eventInfo', {}).get('eventLogo', '')
    event_id = str(event.get('id', ''))
    
    team_a = get_full_team_name(event.get('eventInfo', {}).get('teamA', '').lower().replace(" ", ""))
    team_b = get_full_team_name(event.get('eventInfo', {}).get('teamB', '').lower().replace(" ", ""))
    
    possible_slugs = []
    if team_a and team_b:
        possible_slugs.append(f"{team_a}-vs-{team_b}")
        possible_slugs.append(f"{team_b}-vs-{team_a}")
    if event.get('eventInfo', {}).get('teamA', '') and event.get('eventInfo', {}).get('teamB', ''):
        possible_slugs.append(f"{event.get('eventInfo', {}).get('teamA', '').lower().replace(' ', '')}-vs-{event.get('eventInfo', {}).get('teamB', '').lower().replace(' ', '')}")
    if slug:
        possible_slugs.append(slug.lower().replace(" ", "-"))
        possible_slugs.append(slug.replace(" ", "%20"))
    if event_id:
        possible_slugs.append(event_id)

    print(f"🔎 Scanning {match_title}...")
    valid_response = None
    
    for s in possible_slugs:
        try:
            ch_url = f"{BASE_URL}/channels/{s}.txt"
            res = requests.get(ch_url, headers=HEADERS, timeout=4)
            if res.status_code == 200 and "google.com" not in res.text and len(res.text) > 50:
                valid_response = res
                print(f"✅ LINK FOUND: {s}")
                break
        except:
            continue

    if not valid_response: return []

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

                h_list = []
                if "User-Agent" not in headers: h_list.append(f"User-Agent={HEADERS['User-Agent']}")
                if headers: h_list.append(headers)
                final_headers = "&".join(h_list)

                # --- FIX: CORRECT ARRANGEMENT ORDER ---
                # 1. Start with EXTINF (Sabse Pehle)
                entry = f'#EXTINF:-1 tvg-logo="{logo}" group-title="{match_title}", {stream_title}\n'
                
                # 2. Add KODIPROP (Uske Baad)
                drm_key = s.get('api')
                if drm_key:
                    entry += f'#KODIPROP:inputstream.adaptive.license_type=clearkey\n'
                    entry += f'#KODIPROP:inputstream.adaptive.license_key={drm_key}\n'
                
                # 3. Add URL (Sabse Niche)
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
    print("🚀 Connecting (Ordered Mode)...")
    all_entries = []
    try:
        response = requests.get(f"{BASE_URL}/categories/live-events.txt", headers=HEADERS, timeout=30)
        decrypted_list = decrypt_data(response.text)
        if not decrypted_list: return
        
        events = json.loads(decrypted_list)
        for event in events:
            if "cricket" in event.get('eventInfo', {}).get('eventCat', '').lower():
                all_entries.extend(get_match_links(event))

        with open("playlist.m3u", "w", encoding='utf-8') as f:
            f.write("#EXTM3U\n")
            for entry in all_entries:
                f.write(entry)
        print(f"🎉 Playlist Updated with Correct Order: {len(all_entries)} streams.")
    except Exception as e:
        print(f"Critical Error: {e}")

if __name__ == "__main__":
    main()
