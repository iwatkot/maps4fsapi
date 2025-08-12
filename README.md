<p align="center">
<a href="https://github.com/iwatkot/maps4fs">maps4fs</a> •
<a href="https://github.com/iwatkot/maps4fsui">maps4fs UI</a> •
<a href="https://github.com/iwatkot/maps4fsdata">maps4fs Data</a> •
<a href="https://github.com/iwatkot/maps4fsapi">maps4fs API</a> •
<a href="https://github.com/iwatkot/maps4fsstats">maps4fs Stats</a> •
<a href="https://github.com/iwatkot/maps4fsbot">maps4fs Bot</a><br>
<a href="https://github.com/iwatkot/pygmdl">pygmdl</a> •
<a href="https://github.com/iwatkot/pydtmdl">pydtmdl</a>
</p>

<div align="center" markdown>

<img src="https://github.com/iwatkot/maps4fsapi/releases/download/0.0.1/maps4fs-poster_dev4.png">

<p align="center">
    <a href="#maps4fs">Maps4FS</a> •
    <a href="#overview">Overview</a> •
    <a href="#public-and-private-apis">Public and Private APIs</a> •
    <a href="#queuing">Queuing</a> •
    <a href="#maps4fs-api">Maps4FS API</a><br>
    <a href="#map-endpoints">Map Endpoints</a> •
    <a href="#task-endpoints">Task Endpoints</a> •
    <a href="#dtm-endpoints">DTM Endpoints</a> •
    <a href="#grle-endpoints">GRLE Endpoints</a><br>
    <a href="#i3d-endpoints">I3d Endpoints</a> •
    <a href="#mesh-endpoints">Mesh Endpoints</a> •
    <a href="#texture-endpoints">Texture Endpoints</a> •
    <a href="#satellite-endpoints">Satellite Endpoints</a>
</p>

[![Join Discord](https://img.shields.io/badge/join-discord-blue)](https://discord.gg/Sj5QKKyE42)
[![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/iwatkot/maps4fsapi)](https://github.com/iwatkot/maps4fs/releases)
[![GitHub issues](https://img.shields.io/github/issues/iwatkot/maps4fsapi)](https://github.com/iwatkot/maps4fsapi/issues)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![Build Status](https://github.com/iwatkot/maps4fsapi/actions/workflows/checks.yml/badge.svg)](https://github.com/iwatkot/maps4fsapi/actions)
[![GitHub Repo stars](https://img.shields.io/github/stars/iwatkot/maps4fsapi)](https://github.com/iwatkot/maps4fsapi/stargazers)

</div>

# Maps4FS

Maps4FS is a tool for automatic generation maps for Farming Simulator games using the real world data. More information can be found in the [main repository](https://github.com/iwatkot/maps4fs).  

This repository contains the source code for the Maps4FS API, based on the `fastapi` framework.

# Overview

This repository is a part of the Maps4FS project, which consists of several components: the main maps4fs Python library, the maps4fs UI, the maps4fs API, the maps4fs stats, and the maps4fs bot.

Please, refer to the main repository for all the relevant information about the Maps4FS project, including the documentation.

➡️ The example of using the Maps4FS API from the Python code can be found in the [demo.py](demo.py) file in the root directory of this repository.

# Public and private APIs
The public API is available at [https://api.maps4fs.xyz](https://api.maps4fs.xyz) and provides access to the Maps4FS functionality. It requires authentication via an API key, which can be obtained in the Maps4FS Discord server by asking the bot for an API key. The API key is required for all requests to the public API.  
The public version of the API also has a rate limit, which can be changed at any time but for the moment is set to 10 requests per hour for the same API key.  
<br>
The private API will be automatically deployed in the Docker version of the Maps4FS and by default will be available at `http://localhost:8000`. It does not require an API key and does not have a rate limit.

## Public API Authentication
To authenticate with the public API, you need to include your API key as a bearer token in the `Authorization` header of your request.  
Request example:
```bash
curl -X POST "http://localhost:8000/dtm/list" \
  -H "Authorization: Bearer YOUR_API_KEY_HERE" \
  -H "Content-Type: application/json" \
  -d '{"lat": 10.0, "lon": 25.0}'
```

**NOTE:** The private API (which deployed locally) does not require an API key, so you can omit the `Authorization` header in your requests.

# Queuing
Some endpoints of the Maps4FS API will take a long time to process the request, in this case the API will validate the initial request and return a `task_id` that can be used later to retrieve the result of the request.
The endpoints that support queuing are marked with a ✅ in the table below. You can use the `/tasks/get` endpoint to check the status of the task and retrieve the result when it is ready.

Response example:
```json
{
    "success": true,
    "description": "Task has been added to the queue. Use the task ID to retrieve the result.",
    "task_id": "1234567890abcdef1234567890abcdef"
}
```

# Maps4FS API
The Maps4FS API is a RESTful API that provides access to the Maps4FS functionality. It allows you to generate maps, retrieve information about the specific components of the maps, and perform other operations related to the Maps4FS project.  
Source documentation for the Maps4FS API is available [here](maps4fsapi/components/).  
Pydantic models from the main `maps4fs` library can be found [here](https://github.com/iwatkot/maps4fs/blob/main/maps4fs/generator/settings.py).

## Map Endpoints
The Map component of the Maps4FS API is responsible for generating a complete map, not a single component of it. You can provide all the settings in one place and receive a `zip` archive containing all the generated files.

| Method | Endpoint | Payload Model | Queuing |
|--------|----------|---------------|--------|
| POST   | `/map/generate` | [MapGenerationPayload](maps4fsapi/components/models.py) | ✅ |

`/map/generate`: Generates a complete map based on the provided settings. The response will be a `zip` archive containing all the generated files, including DTM, GRLE, I3D, Mesh, Texture, and Satellite data.

## Task Endpoints
Those endpoints are used to obtain the data about the task previously created by any endpoint which uses queuing. You can use the `task_id` to check the status of the task and retrieve the result when it is ready.

| Method | Endpoint | Payload Model | Queuing |
|--------|----------|---------------|--------|
| GET    | `/task/get` | [TaskIdPayload](maps4fsapi/components/models.py) | ❌ |

`/task/get`: If the task completed successfully, it will return the requested data, otherwise it will return the error message with details about the error.

If the response will have OK status, in most of the cases it will return a file object.

## DTM Endpoints
The DTM (Digital Terrain Model) component of the Maps4FS API is responsible for generating and managing the terrain data for the maps. It provides endpoints to obtain information about available DTM providers and to generate the DEM (Digital Elevation Model) for a specific area.

| Method | Endpoint | Payload Model | Queuing |
|--------|----------|---------------|--------|
| POST   | `/dtm/list` | [LatLonPayload](maps4fsapi/components/models.py) | ❌ |
| POST   | `/dtm/info` | [DTMCodePayload](maps4fsapi/components/models.py) | ❌ |
| POST   | `/dtm/dem` | [DEMSettingsPayload](maps4fsapi/components/models.py) | ✅ |

`/dtm/list`: Returns a list of available DTM providers for provide latitude and longitude.  

Response example:

```json
{"srtm30": "🌎 Global [30.0 m/px] SRTM 30 m"}
```
In this example the `srtm30` key is a DTM provider code, that can be used in other endpoints, and the value is a human-readable description of the DTM provider.

`/dtm/info`: Returns information about a specific DTM provider by provided DTM Provider code.  

Response example:

```json
{"valid": true, "provider": "🌎 Global [30.0 m/px] SRTM 30 m"}
```
If the provided DTM code was correct, the `valid` field will be `true`, otherwise it will be `false`. The `provider` field contains a human-readable description of the DTM provider.

`/dtm/dem`: Generates a DEM for a specific area defined by the provided payload.  

## GRLE Endpoints
The GRLE component of the Maps4FS API is responsible for generating and managing the ground layer data for the maps, for example plants and farmlands.

| Method | Endpoint | Payload Model | Queuing |
|--------|----------|---------------|--------|
| POST   | `/grle/plants` | [GRLESettingsPayload](maps4fsapi/components/models.py) | ✅ |
| POST   | `/grle/farmlands` | [GRLESettingsPayload](maps4fsapi/components/models.py) | ✅ |

`/grle/plants`: Generates a PNG file for the plants layer based on the provided settings.  
`/grle/farmlands`: Generates a PNG file for the farmlands layer based on the provided settings.  

## I3d Endpoints
The I3d component of the Maps4FS API is responsible for generating and managing the entities related to the I3d files, which contain trees, fields and splines.

| Method | Endpoint | Payload Model | Queuing |
|--------|----------|---------------|--------|
| POST   | `/i3d/forests` | [I3DSettingsPayload](maps4fsapi/components/models.py) | ✅ |
| POST   | `/i3d/fields` | [I3DSettingsPayload](maps4fsapi/components/models.py) | ✅ |
| POST   | `/i3d/splines` | [I3DSettingsPayload](maps4fsapi/components/models.py) | ✅ |

`/i3d/forests`: Returns map i3d file which contains tree data. 
`/i3d/fields`: Returns map i3d file which contains field data.
`/i3d/splines`: Returns map i3d file which contains splines.

## Mesh Endpoints
The Mesh component of the Maps4FS API is responsible for generating and managing the mesh data for the background terrain and the water resources. The returned files are in the `.obj` format, which can be used in various 3D applications (e.g., Blender).

| Method | Endpoint | Payload Model | Queuing |
|--------|----------|---------------|--------|
| POST   | `/mesh/background` | [BackgroundSettingsPayload](maps4fsapi/components/models.py) | ✅ |
| POST   | `/mesh/water` | [WaterSettingsPayload](maps4fsapi/components/models.py) | ✅ |

`/mesh/background`: Returns the background mesh in the `.obj` format based on the provided settings.  
`/mesh/water`: Returns the water mesh in the `.obj` format based on the provided settings.

## Texture Endpoints
The Texture component of the Maps4FS API is responsible for generating weight files for different in-game textures. The returned files are in the `.png` format.

| Method | Endpoint | Payload Model | Queuing |
|--------|----------|---------------|--------|
| POST   | `/texture/images` | [TextureSettingsPayload](maps4fsapi/components/models.py) | ✅ |

`/texture/images`: Based on the provided list of `layer_names` which correspond to the `texture-schema.json` file, this endpoint can return a single `.png` file or a `zip` archive containing multiple `.png` files.

## Satellite Endpoints
The Satellite component of the Maps4FS API is responsible for generating satellite images for the specified area. The returned files are in the `.png` format.

| Method | Endpoint | Payload Model | Queuing |
|--------|----------|---------------|--------|
| POST   | `/satellite/overview` | [SatelliteSettingsPayload](maps4fsapi/components/models.py) | ✅ |
| POST   | `/satellite/background` | [SatelliteSettingsPayload](maps4fsapi/components/models.py) | ✅ |

`/satellite/overview`: Returns an overview satellite image for the specified area. The overview image covers twice the area of the provided map size to create an in-game overview map.
`/satellite/background`: Returns a background satellite image for the specified area. This image can be used as a texture for the beackground terrain mesh obtained from the `/mesh/background` endpoint.
