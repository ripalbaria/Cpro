import requests
import base64
import os
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# --- CONFIGURATION ---
TARGET_SLUG = "india-vs-south-africa"
BASE_URL = os.environ.get("BASE_URL")

# GitHub Secrets se Keys load karna
KEYS = []
if os.environ.get("KEY_HEX"): KEYS.append({"k": os.environ.get("KEY_HEX"), "i": os.environ.get("IV_HEX")})
if os.environ.get("KEY_HEX_2"): KEYS.append({"k": os.environ.get("KEY_HEX_2"), "i": os.environ.get("IV_HEX_2")})

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": f"{BASE_URL}/",
    "Origin": BASE_URL
}

def decrypt_text(encrypted_text):
    print(f"🔐 Raw Length: {len(encrypted_text)}")
    
    # --- EXACT KOTLIN LOGIC (Clean Base64) ---
    clean_b64 = encrypted_text.strip()
    clean_b64 = clean_b64.replace("\n", "")
    clean_b64 = clean_b64.replace("\r", "")
    clean_b64 = clean_b64.replace(" ", "")
    clean_b64 = clean_b64.replace("\t", "")
    
    print(f"ww Clean Length: {len(clean_b64)}")

    for idx, cred in enumerate(KEYS):
        try:
            k = bytes.fromhex(cred["k"])
            i = bytes.fromhex(cred["i"])
            
            ciphertext = base64.b64decode(clean_b64)
            cipher = AES.new(k, AES.MODE_CBC, i)
            decrypted = unpad(cipher.decrypt(ciphertext), AES.block_size).decode('utf-8')
            
            print(f"✅ Success with Key {idx+1}!")
            return decrypted
        except ValueError as ve:
            # Ye PKCS7 error hota hai usually
            print(f"❌ Key {idx+1} Padding Error: {ve}")
        except Exception as e:
            print(f"❌ Key {idx+1} Failed: {e}")
            
    return None

def test_match():
    if not BASE_URL:
        print("❌ Error: BASE_URL secret not set!")
        return

    full_url = f"{BASE_URL}/channels/{TARGET_SLUG}.txt"
    print(f"🚀 Testing URL: {full_url}")

    try:
        res = requests.get(full_url, headers=HEADERS, timeout=10)
        
        if res.status_code == 200 and "google.com" not in res.text:
            print("✅ Data received from server.")
            data = decrypt_text(res.text)
            
            if data:
                print("\n🎉 DECRYPTION SUCCESS!")
                print(data[:200] + "...")
            else:
                print("\n❌ ALL KEYS FAILED. We need new keys.")
        else:
            print(f"❌ Failed to fetch: Status {res.status_code}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_match()
