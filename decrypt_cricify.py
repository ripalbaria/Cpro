import base64
import requests
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# --- COMPLETE CONFIGURATION ---
# Base URL ko pura path ke liye define kiya gaya hai
BASE_URL = "https://cfyhljddgbkkufh82.top"

# Extracted Secrets from your smali files
KEY_HEX = "3368487a78594167534749382f68616d"
IV_HEX = "557143766b766a656345497a38343256"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def decrypt_data(encrypted_text):
    """Plugin logic: AES/CBC/PKCS5Padding"""
    try:
        key = bytes.fromhex(KEY_HEX)
        iv = bytes.fromhex(IV_HEX)
        clean_b64 = encrypted_text.strip().replace("\n", "").replace("\r", "").replace(" ", "").replace("\t", "")
        ciphertext = base64.b64decode(clean_b64)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(ciphertext), AES.block_size)
        return decrypted.decode('utf-8')
    except Exception:
        return None

def main():
    # 1. Sabse pehle matches ki list fetch karein (Full URL)
    events_list_url = f"{BASE_URL}/categories/live-events.txt"
    print(f"📡 Fetching Cricket List from: {events_list_url}")
    
    response = requests.get(events_list_url, headers=HEADERS)
    if response.status_code != 200:
        print("❌ Error: List download nahi ho saki.")
        return

    decrypted_list = decrypt_data(response.text)
    if not decrypted_list:
        print("❌ Error: List decrypt nahi ho payi.")
        return

    events = json.loads(decrypted_list)
    
    # 2. Loop through events and filter only Cricket
    for event in events:
        category = event.get('eventInfo', {}).get('eventCat', '')
        
        if category.lower() == "cricket":
            title = event.get('title', 'Unknown Match')
            slug = event.get('slug')
            
            print(f"\n🏏 MATCH: {title}")
            
            # 3. Dynamic Match URL (Pura Path .txt ke saath)
            match_links_url = f"{BASE_URL}/channels/{slug}.txt"
            
            match_res = requests.get(match_links_url, headers=HEADERS)
            if match_res.status_code == 200:
                decrypted_links = decrypt_data(match_res.text)
                if decrypted_links:
                    stream_json = json.loads(decrypted_links)
                    streams = stream_json.get('streamUrls', [])
                    for s in streams:
                        # URL se extra headers hatana (| ke baad wala part)
                        clean_url = s.get('link', '').split('|')[0]
                        print(f"   ✅ {s.get('title')}: {clean_url}")
                else:
                    print(f"   ⚠️ Could not decrypt links for {slug}")
            else:
                print(f"   ⚠️ Match URL not found: {match_links_url}")

if __name__ == "__main__":
    main()
