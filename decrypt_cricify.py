import base64
import requests
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# The endpoint found in your Reqable capture
DATA_URL = "https://cfyhgdgnkkuvn92.top/categories/live-events.txt"

# Extracted Secrets from the Smali lambda methods
SECRETS = [
    "3368487a78594167534749382f68616d:557143766b766a656345497a38343256", # Secret 1
    "4d7165594743543441594b6f484b7254:6f484b725451755078387a6l386f4a2b"  # Secret 2
]

def decrypt_payload(encrypted_text, secret_string):
    """Implementation of the tryDecrypt logic from the Provider code"""
    try:
        # Split secret into Key and IV by colon
        parts = secret_string.split(":")
        key = bytes.fromhex(parts[0])
        iv = bytes.fromhex(parts[1])
        
        # Clean the base64 string exactly like Kotlin logic
        clean_b64 = encrypted_text.strip().replace("\n", "").replace("\r", "").replace(" ", "").replace("\t", "")
        ciphertext = base64.b64decode(clean_b64)
        
        cipher = AES.new(key, AES.MODE_CBC, iv)
        # unpad handles the PKCS5Padding
        decrypted = unpad(cipher.decrypt(ciphertext), AES.block_size)
        return decrypted.decode('utf-8')
    except Exception:
        return None

def main():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    print(f"Fetching data from {DATA_URL}...")
    response = requests.get(DATA_URL, headers=headers)
    
    if response.status_code != 200:
        print(f"Error: Server returned {response.status_code}")
        return

    encrypted_data = response.text
    decrypted_result = None

    # Loop through both keys just like the 'for ((keyName, keyInfo) in KEYS)' logic
    for i, secret in enumerate(SECRETS):
        print(f"Attempting decryption with Key {i+1}...")
        decrypted_result = decrypt_payload(encrypted_data, secret)
        if decrypted_result:
            print(f"Success! Data decrypted using Key {i+1}.")
            break
    
    if decrypted_result:
        # Save the raw JSON for your reference
        with open("playlist.json", "w", encoding='utf-8') as f:
            f.write(decrypted_result)
        print("File saved: playlist.json")
    else:
        print("Failed: Neither key was able to decrypt the data. The server may have changed keys.")

if __name__ == "__main__":
    main()

