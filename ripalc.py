import base64
import requests
import json
import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# --- SECURITY: Load from GitHub Secrets ---
BASE_URL = os.environ.get("BASE_URL")

# Key Rotation Logic: Pehle Key 1 try karega, fail hone par Key 2
KEYS_LIST = [
    {
        "key": os.environ.get("KEY_HEX"),      # Key 1
        "iv": os.environ.get("IV_HEX")         # IV 1
    },
    {
        "key": os.environ.get("KEY_HEX_2"),    # Key 2 (Backup)
        "iv": os.environ.get("IV_HEX_2")       # IV 2 (Backup)
    }
]

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def try_decrypt(encrypted_text, key_hex, iv_hex):
    try:
        if not key_hex or not iv_hex: return None
        key = bytes.fromhex(key_hex)
        iv = bytes.fromhex(iv_hex)
        clean_b64 = encrypted_text.strip().replace("\n", "").replace("\r", "").replace(" ", "").replace("\t", "")
        ciphertext = base64.b64decode(clean_b64)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(ciphertext), AES.block_size)
        return decrypted.decode('utf-8')
    except:
        return None

def decrypt_data(encrypted_text):
    # Loop through all available keys
    for creds in KEYS_LIST:
        k = creds["key"]
        i = creds["iv"]
        if k and i:
            result = try_decrypt(encrypted_text, k, i)
            if result: return result
    return None

def get_match_links(slug, match_title, logo):
    links_found = []
    try:
        ch_url = f"{BASE_URL}/channels/{slug}.txt"
        ch_res = requests.get(ch_url, headers=HEADERS, timeout=10)
        
        if ch_res.status_code == 200:
            dec_links = decrypt_data(ch_res.text)
            if dec_links:
                streams = json.loads(dec_links).get('streamUrls', [])
                for s in streams:
                    stream_title = s.get('title', 'Source')
                    raw_link = s.get('link', '')
                    
                    if '|' in raw_link:
                        final_url = raw_link.split('|')[0]
                        pipe_headers = raw_link.split('|')[1]
                    else:
                        final_url = raw_link
                        pipe_headers = ""

                    json_headers = s.get('headers')
                    header_list = []
                    
                    if "User-Agent" not in str(pipe_headers) and "User-Agent" not in str(json_headers):
                        header_list.append(f"User-Agent={HEADERS['User-Agent']}")
                    
                    if pipe_headers: header_list.append(pipe_headers)
                    if json_headers:
                        clean_json = str(json_headers).replace(";", "&").replace(" ", "")
                        header_list.append(clean_json)

                    final_header_string = "&".join(header_list)
                    
                    entry = ""
                    drm_key = s.get('api') 
                    
                    if drm_key:
                        entry += '#KODIPROP:inputstream.adaptive.license_type=clearkey\n'
                        entry += f'#KODIPROP:inputstream.adaptive.license_key={drm_key}\n'
                    
                    entry += f'#EXTINF:-1 tvg-logo="{logo}" group-title="{match_title}", {stream_title}\n'
                    
                    if final_header_string:
                        entry += f'{final_url}|{final_header_string}\n'
                    else:
                        entry += f'{final_url}\n'
                        
                    links_found.append(entry)
    except Exception as e:
        print(f"Error in {slug}: {e}")
    return links_found

def main():
    if not BASE_URL:
        print("❌ Error: Secrets not loaded!")
        return

    print("🚀 Connecting to Server (Secure Mode)...")
    all_entries = []
    
    try:
        response = requests.get(f"{BASE_URL}/categories/live-events.txt", headers=HEADERS, timeout=30)
        decrypted_list = decrypt_data(response.text)
        
        if not decrypted_list:
            print("❌ Decryption failed with all keys.")
            return
        
        events = json.loads(decrypted_list)
        print(f"✅ Found {len(events)} events.")

        for event in events:
            cat = event.get('eventInfo', {}).get('eventCat', '')
            if cat and cat.lower() == "cricket":
                title = event.get('title', 'Cricket Match')
                slug = event.get('slug')
                logo = event.get('eventInfo', {}).get('eventLogo', '')
                
                print(f"🏏 Fetching: {title}")
                all_entries.extend(get_match_links(slug, title, logo))

        with open("playlist.m3u", "w", encoding='utf-8') as f:
            f.write("#EXTM3U\n")
            for entry in all_entries:
                f.write(entry)
        
        print(f"🎉 Success! Playlist updated.")
        
    except Exception as e:
        print(f"❌ Critical Error: {e}")

if __name__ == "__main__":
    main()
