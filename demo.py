from time import sleep

import requests

# region Constants
SLEEP_TIMER = 5
API_URL = "https://api.maps4fs.xyz"

# The API token is required only on the public API (https://api.maps4fs.xyz).
# If you're using local version (https://localhost:8000), you don't need it.
BEARER_TOKEN = "YOUR_API_TOKEN_HERE"
# The API token can be obtained from the Maps4FS bot in the Discord server.
# Open the api-keys channel and type /apikey to get your token.
lat, lon = 45.285541402763336, 20.237452197282817
map_size = 512
game_code = "fs25"
# endregion


# region Utility Functions


def wait(seconds: int) -> None:
    """Wait for a specified number of seconds.

    Arguments:
        seconds (int): Number of seconds to wait.
    """
    for i in range(seconds, 0, -1):
        print(f"Waiting for {i} seconds...")
        sleep(1)


# endregion

# region Case 1️⃣: Download DEM for a specific location using the Maps4FS API.

# ℹ️ Get version of the maps4fs API.
version_info = requests.get(f"{API_URL}/info/version").json()
print(f"API Version: {version_info['version']}")

# 1️⃣ Get available DTM Providers for the given coordinates.
dtm_providers = requests.post(
    f"{API_URL}/dtm/list",
    json={"lat": lat, "lon": lon},
    headers={"Authorization": f"Bearer {BEARER_TOKEN}"},  # Example of using the API token.
).json()
print(f"Available DTM Providers: {dtm_providers}")

# 2️⃣ Vaidate the DTM Provider code.
dtm_info = requests.post(f"{API_URL}/dtm/info", json={"code": "srtm30"}).json()
print(f"DTM Info: {dtm_info}")

# 3️⃣ Request generation of the DEM file.
dem_task_response = requests.post(
    f"{API_URL}/dtm/dem",
    json={"lat": lat, "lon": lon, "size": map_size, "dtm_code": "srtm30", "game_code": game_code},
).json()
print(f"DEM Task Response: {dem_task_response}")

# 4️⃣ Get the task ID for the DEM generation.
task_id = dem_task_response["task_id"]
print(f"Task ID: {task_id}")

# 5️⃣ Wait for the DEM generation to complete.
wait(SLEEP_TIMER)

response = requests.post(f"{API_URL}/task/get", json={"task_id": task_id})
response.raise_for_status()
if response.status_code == 200:
    dem_image_data = response.content
    print("DEM image data received successfully.")
else:
    raise Exception(f"Failed to retrieve DEM image: {response.status_code} - {response.text}")

# 5️⃣ Save the DEM image to a file.
with open("dem_image.png", "wb") as file:
    file.write(dem_image_data)
print("DEM image saved as 'dem_image.png'.")

# endregion
