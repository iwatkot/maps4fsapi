| Section   | Endpoint  | Component | Required payload                                               | Output                                      | Heavy (require queue) |
|-----------|-----------|-----------|----------------------------------------------------------------|---------------------------------------------|-----------------------|
| DTM       | /get_list | DTM       | lat, lon                                                       | list of DTM codes                           | ❌                    |
| DTM       | /is_valid | DTM       | dtm_code                                                       | DTM description or error message            | ❌                    |
| DEM       | /get_dem  | Background| lat, lon, map_size, rotation, output_size, dem_code            | dem image                                   | ✅                    |
| Backround | /get_bg   | Background| lat, lon, map_size, rotation, output_size, dem_code            | background mesh                             | ✅                    |
| Backround | /get_water| Background| lat, lon, map_size, rotation, output_size, dem_code            | water mesh (elevated)                       | ✅                    |
| Backround | /get_water| Background| lat, lon, map_size, rotation, output_size, dem_code            | water mesh (plane)                          | ✅                    |



GRLE:
- Farmlands (image) If no textures were created, create a new instance automatically
- Plants (image) If no textures were created, create a new instance automatically

I3D:
- Fields (XML part that can be injected to the map I3D file)
- Trees (XML part that can be injected to the map I3D file)
- Splines (separate I3D file) If no textures were created, create a new instance automatically

Texture:
- Images by provided texture schema or default one (zip archive with images)

Complete generation:
- Completely generated map (zip archive with all files) -> Disable on public API, only for private use



```python
import base64
import hashlib

SECRET_SALT = "your_secret_salt"

def encode_user_id(user_id: int) -> str:
    return base64.urlsafe_b64encode(str(user_id).encode()).decode().rstrip("=")

def decode_user_id(encoded: str) -> int:
    padded = encoded + "=" * (-len(encoded) % 4)
    return int(base64.urlsafe_b64decode(padded.encode()).decode())

def generate_api_key(user_id: int) -> str:
    encoded_id = encode_user_id(user_id)
    raw = f"{user_id}:{SECRET_SALT}"
    hashed = hashlib.sha256(raw.encode()).hexdigest()[:32]
    return f"{encoded_id}.{hashed}"

def validate_api_key(api_key: str) -> bool:
    try:
        encoded_id, key_hash = api_key.split(".")
        user_id = decode_user_id(encoded_id)
        expected_hash = hashlib.sha256(f"{user_id}:{SECRET_SALT}".encode()).hexdigest()[:32]
        return key_hash == expected_hash
    except Exception:
        return False

# Example usage:
api_key = generate_api_key(1234500)
print(api_key)  # Looks like: MTIzNDUwMA.96fb3933295bb3cd45f9f2b4aca4f33b
print(validate_api_key(api_key))  # True

broken_api_key = api_key[:-1]
print(validate_api_key(broken_api_key))
```