import requests
import base64
import os
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# --- CONFIGURATION ---
# Hum seedha URL try karenge jo aapke Termux me chala tha
TARGET_SLUG = "india-vs-south-africa"
BASE_URL = os.environ.get("BASE_URL")

# Keys Load karo
KEYS = []
if os.environ.get("KEY_HEX"): KEYS.append({"k": os.environ.get("KEY_HEX"), "i": os.environ.get("IV_HEX")})
if os.environ.get("KEY_HEX_2"): KEYS.append({"k": os.environ.get("KEY_HEX_2"), "i": os.environ.get("IV_HEX_2")})

# Headers wahi rakhte hain jo Cloudstream/Browser use karte hain
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": f"{BASE_URL}/",
    "Origin": BASE_URL
}

def decrypt_text(encrypted_text):
    print(f"🔐 Decrypting {len(encrypted_text)} chars...")
    for idx, cred in enumerate(KEYS):
        try:
            k = bytes.fromhex(cred["k"])
            i = bytes.fromhex(cred["i"])
            clean_b64 = encrypted_text.strip().replace("\n", "").replace(" ", "")
            ciphertext = base64.b64decode(clean_b64)
            cipher = AES.new(k, AES.MODE_CBC, i)
            decrypted = unpad(cipher.decrypt(ciphertext), AES.block_size).decode('utf-8')
            print(f"✅ Success with Key {idx+1}!")
            return decrypted
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
        # Request bhejo
        res = requests.get(full_url, headers=HEADERS, timeout=10)
        
        print(f"📡 Status Code: {res.status_code}")
        
        if "google.com" in res.text:
            print("❌ BLOCKED: Server redirected to Google (Anti-Bot detected).")
            return

        if res.status_code != 200:
            print("❌ FAILED: File not found or server error.")
            return

        print("✅ Connection Successful! Data received.")
        print(f"📄 Data Preview: {res.text[:100]}...") # Shuru ke 100 akshar dikhao

        # Decryption Check
        data = decrypt_text(res.text)
        
        if data:
            print("\n🎉 FINAL RESULT: Decryption 100% Working!")
            print(json.dumps(json.loads(data), indent=2))
        else:
            print("\n❌ FINAL RESULT: Decryption Failed (Wrong Keys?)")

    except Exception as e:
        print(f"💥 Critical Error: {e}")

if __name__ == "__main__":
    test_match()

