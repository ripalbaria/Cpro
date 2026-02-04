import base64
import requests
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# UPDATE: Reqable wala working URL use karein
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
    m3u_output = "#EXTM3U\n"
    print(f"🚀 Fetching from: {BASE_URL}")
    
    try:
        # Step 1: Get Cricket Matches
        response = requests.get(f"{BASE_URL}/categories/live-events.txt", headers=HEADERS, timeout=15)
        decrypted_list = decrypt_data(response.text)
        if not decrypted_list: return
        
        events = json.loads(decrypted_list)
        for event in events:
            if event.get('eventInfo', {}).get('eventCat', '').lower() == "cricket":
                title = event.get('title', 'Cricket Match')
                slug = event.get('slug')
                logo = event.get('eventInfo', {}).get('eventLogo', '')
                
                # Step 2: Get Match Links
                ch_res = requests.get(f"{BASE_URL}/channels/{slug}.txt", headers=HEADERS, timeout=15)
                dec_links = decrypt_data(ch_res.text)
                if dec_links:
                    streams = json.loads(dec_links).get('streamUrls', [])
                    for s in streams:
                        link = s.get('link', '').split('|')[0]
                        m3u_output += f'#EXTINF:-1 tvg-logo="{logo}", {title} ({s.get("title")})\n{link}\n'
        
        # Step 3: Save File
        with open("playlist.m3u", "w", encoding='utf-8') as f:
            f.write(m3u_output)
        print("✅ Success: playlist.m3u created!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
