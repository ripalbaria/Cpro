import base64
import requests
import json
import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# --- SECURITY: Load from GitHub Secrets ---
BASE_URL = os.environ.get("BASE_URL")

# Key Rotation Logic
KEYS_LIST = [
    { "key": os.environ.get("KEY_HEX"), "iv": os.environ.get("IV_HEX") },
    { "key": os.environ.get("KEY_HEX_2"), "iv": os.environ.get("IV_HEX_2") }
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
    for creds in KEYS_LIST:
        k = creds["key"]
        i = creds["iv"]
        if k and i:
            result = try_decrypt(encrypted_text, k, i)
            if result: return result
    return None

def get_match_links(slug, match_title, logo):
    links_found = []
    
    # --- SMART SEARCH LOGIC ---
    # Hum alag-alag possibilities ki list banayenge
    possible_slugs = []
    
    # 1. Standard (Lowercase + Dashes) -> icc-t20-warm-up-2 (Most likely)
    possible_slugs.append(slug.lower().replace(" ", "-"))
    
    # 2. Encoded Spaces -> ICC%20T20%20Warm-up%202
    possible_slugs.append(slug.replace(" ", "%20"))
    
    # 3. Compressed -> icct20warmup2
    possible_slugs.append(slug.lower().replace(" ", ""))
    
    # 4. Original (Just in case) -> ICC T20 Warm-up 2
    possible_slugs.append(slug)

    valid_response = None
    used_slug = ""

    print(f"🔎 Searching valid link for: {match_title}")
    
    for s in possible_slugs:
        try:
            ch_url = f"{BASE_URL}/channels/{s}.txt"
            res = requests.get(ch_url, headers=HEADERS, timeout=5)
            
            # Agar 'Redirect to Google' na ho aur status 200 ho
            if res.status_code == 200 and "google.com" not in res.text:
                # Check karein ki kya ye wakai encrypted data hai?
                if len(res.text) > 50: 
                    valid_response = res
                    used_slug = s
                    print(f"✅ FOUND at slug: {s}")
                    break
        except:
            continue

    if not valid_response:
        print(f"⚠️ Skipping '{match_title}' (File not found on server)")
        return []

    # --- DECRYPTION & PARSING ---
    try:
        dec_links = decrypt_data(valid_response.text)
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
        print(f"Error processing {used_slug}: {e}")
        
    return links_found

def main():
    if not BASE_URL:
        print("❌ Error: Secrets not loaded!")
        return

    print("🚀 Connecting to Server (Smart Search Mode)...")
    all_entries = []
    
    try:
        response = requests.get(f"{BASE_URL}/categories/live-events.txt", headers=HEADERS, timeout=30)
        decrypted_list = decrypt_data(response.text)
        
        if not decrypted_list:
            print("❌ Decryption failed.")
            return
        
        events = json.loads(decrypted_list)
        print(f"✅ Found {len(events)} events.")

        for event in events:
            cat = event.get('eventInfo', {}).get('eventCat', '')
            if cat and cat.lower() == "cricket":
                title = event.get('title', 'Cricket Match')
                slug = event.get('slug')
                logo = event.get('eventInfo', {}).get('eventLogo', '')
                
                # Function call karein jo khud sahi link dhoondhega
                links = get_match_links(slug, title, logo)
                all_entries.extend(links)

        with open("playlist.m3u", "w", encoding='utf-8') as f:
            f.write("#EXTM3U\n")
            for entry in all_entries:
                f.write(entry)
        
        print(f"🎉 Playlist updated with {len(all_entries)} streams.")
        
    except Exception as e:
        print(f"❌ Critical Error: {e}")

if __name__ == "__main__":
    main()
