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
    m3u_output = "#EXTM3U\n"
    
    try:
        # 1. Main List Fetch
        list_url = f"{BASE_URL}/categories/live-events.txt"
        response = requests.get(list_url, headers=HEADERS, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Server Error: {response.status_code}")
            return

        decrypted_list = decrypt_data(response.text)
        if not decrypted_list:
            print("❌ Failed to decrypt main list")
            return
        
        events = json.loads(decrypted_list)
        print(f"✅ Found {len(events)} events. Filtering Cricket...")

        # 2. Loop through events
        for event in events:
            cat = event.get('eventInfo', {}).get('eventCat', '')
            
            if cat and cat.lower() == "cricket":
                # Is variable se Folder/Group ka naam banega
                match_title = event.get('title', 'Cricket Match')
                slug = event.get('slug')
                logo = event.get('eventInfo', {}).get('eventLogo', '')
                
                print(f"🏏 Processing Group: {match_title}")

                # 3. Fetch Channel Links
                ch_url = f"{BASE_URL}/channels/{slug}.txt"
                try:
                    ch_res = requests.get(ch_url, headers=HEADERS, timeout=10)
                    if ch_res.status_code == 200:
                        dec_links = decrypt_data(ch_res.text)
                        if dec_links:
                            streams = json.loads(dec_links).get('streamUrls', [])
                            for s in streams:
                                stream_title = s.get('title', 'Source')
                                raw_link = s.get('link', '')
                                
                                # --- Link Parsing ---
                                if '|' in raw_link:
                                    final_url = raw_link.split('|')[0]
                                    pipe_headers = raw_link.split('|')[1]
                                else:
                                    final_url = raw_link
                                    pipe_headers = ""

                                json_headers = s.get('headers')
                                header_list = []
                                
                                # Default User-Agent Check
                                if "User-Agent" not in str(pipe_headers) and "User-Agent" not in str(json_headers):
                                    header_list.append(f"User-Agent={HEADERS['User-Agent']}")
                                
                                if pipe_headers:
                                    header_list.append(pipe_headers)
                                
                                if json_headers:
                                    clean_json_headers = str(json_headers).replace(";", "&").replace(" ", "")
                                    header_list.append(clean_json_headers)

                                final_header_string = "&".join(header_list)
                                
                                # --- M3U Construction ---
                                drm_key = s.get('api') 
                                if drm_key:
                                    # ClearKey DRM Tags
                                    m3u_output += '#KODIPROP:inputstream.adaptive.license_type=clearkey\n'
                                    m3u_output += f'#KODIPROP:inputstream.adaptive.license_key={drm_key}\n'
                                
                                # YAHAN CHANGE KIYA HAI: Group Title ab Match Name hai
                                m3u_output += f'#EXTINF:-1 tvg-logo="{logo}" group-title="{match_title}", {stream_title}\n'
                                
                                if final_header_string:
                                    m3u_output += f'{final_url}|{final_header_string}\n'
                                else:
                                    m3u_output += f'{final_url}\n'

                except Exception as e:
                    print(f"⚠️ Error fetching channel: {e}")

        # 4. Save File
        with open("playlist.m3u", "w", encoding='utf-8') as f:
            f.write(m3u_output)
        print("🎉 Success: playlist.m3u grouped by Match Name!")
        
    except Exception as e:
        print(f"❌ Critical Error: {e}")

if __name__ == "__main__":
    main()
                                m3u_output += f'#EXTINF:-1 tvg-logo="{logo}" group-title="{match_title}", {stream_title}\n'
                                
                                if final_header_string:
                                    m3u_output += f'{final_url}|{final_header_string}\n'
                                else:
                                    m3u_output += f'{final_url}\n'

                except Exception as e:
                    print(f"⚠️ Error fetching channel: {e}")

        # 4. Save File
        with open("playlist.m3u", "w", encoding='utf-8') as f:
            f.write(m3u_output)
        print("🎉 Success: playlist.m3u grouped by Match Name!")
        
    except Exception as e:
        print(f"❌ Critical Error: {e}")

if __name__ == "__main__":
    main()
                                if final_header_string:
                                    m3u_output += f'{final_url}|{final_header_string}\n'
                                else:
                                    m3u_output += f'{final_url}\n'

                except Exception as e:
                    print(f"⚠️ Error fetching channel: {e}")

        # 4. Save File
        with open("playlist.m3u", "w", encoding='utf-8') as f:
            f.write(m3u_output)
        print("🎉 Success: playlist.m3u created!")
        
    except Exception as e:
        print(f"❌ Critical Error: {e}")

if __name__ == "__main__":
    main()
