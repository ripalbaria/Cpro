import base64
import requests
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# --- CONFIGURATION ---
BASE_URL = "https://cfyhgdgnkkuvn92.top"
KEY_HEX = "3368487a78594167534749382f68616d"
IV_HEX = "557143766b766a656345497a38343256"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def decrypt_data(encrypted_text):
    try:
        key = bytes.fromhex(KEY_HEX)
        iv = bytes.fromhex(IV_HEX)
        clean_b64 = encrypted_text.strip().replace("\n", "").replace("\r", "").replace(" ", "").replace("\t", "")
        ciphertext = base64.b64decode(clean_b64)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(ciphertext), AES.block_size)
        return decrypted.decode('utf-8')
    except:
        return None

def main():
    print(f"🚀 Connecting to: {BASE_URL}")
    master_list = [] # Ye list final JSON banegi
    
    try:
        # 1. Fetch Main List
        list_url = f"{BASE_URL}/categories/live-events.txt"
        response = requests.get(list_url, headers=HEADERS, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Server Error: {response.status_code}")
            return

        decrypted_list = decrypt_data(response.text)
        if not decrypted_list:
            print("❌ Decryption Failed")
            return
        
        events = json.loads(decrypted_list)
        print(f"✅ Found {len(events)} events. Filtering Cricket...")

        # 2. Filter Cricket Matches
        for event in events:
            cat = event.get('eventInfo', {}).get('eventCat', '')
            
            if cat and cat.lower() == "cricket":
                title = event.get('title', 'Cricket Match')
                slug = event.get('slug')
                print(f"🏏 Processing: {title}")
                
                match_data = {
                    "match_name": title,
                    "slug": slug,
                    "event_logo": event.get('eventInfo', {}).get('eventLogo', ''),
                    "streams": []
                }

                # 3. Fetch Channel Links
                ch_url = f"{BASE_URL}/channels/{slug}.txt"
                try:
                    ch_res = requests.get(ch_url, headers=HEADERS, timeout=10)
                    if ch_res.status_code == 200:
                        dec_links = decrypt_data(ch_res.text)
                        if dec_links:
                            streams = json.loads(dec_links).get('streamUrls', [])
                            for s in streams:
                                # Data safai aur DRM Key capture
                                stream_info = {
                                    "server": s.get('title'),       # Group Wise Name (e.g. Willow HD)
                                    "url": s.get('link', '').split('|')[0],
                                    "headers": s.get('link', '').split('|')[1] if '|' in s.get('link', '') else None,
                                    "drm_api": s.get('api'),        # Yahan DRM KEY hogi (kid:key)
                                    "type": s.get('type')           # Type 7 = DRM/DASH
                                }
                                match_data["streams"].append(stream_info)
                except Exception as e:
                    print(f"⚠️ Error fetching channel: {e}")
                
                # Sirf tab add karein agar streams mili hon
                if match_data["streams"]:
                    master_list.append(match_data)

        # 4. Save as JSON
        with open("playlist.json", "w", encoding='utf-8') as f:
            json.dump(master_list, f, indent=4) # Indent 4 se file readable banegi
        print("🎉 Success: playlist.json created with full DRM details!")
        
    except Exception as e:
        print(f"❌ Critical Error: {e}")

if __name__ == "__main__":
    main()
