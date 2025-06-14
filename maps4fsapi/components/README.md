<a id="components.dtm"></a>

# components.dtm

DTM (Digital Terrain Model) API endpoints for Maps4FS.

<a id="components.dtm.dtm_list"></a>

#### dtm\_list

```python
@dtm_router.post("/list")
def dtm_list(payload: LatLonPayload)
```

Get a list of available DTM providers based on latitude and longitude.

**Arguments**:

- `payload` _LatLonPayload_ - The payload containing latitude and longitude.

**Returns**:

- `list` - A list of available DTM providers for the given coordinates.

<a id="components.dtm.dtm_info"></a>

#### dtm\_info

```python
@dtm_router.post("/info")
def dtm_info(payload: DTMCodePayload)
```

Get information about a DTM provider based on its code.
If the code is correct, returns the description of the DTM provider. If not, raises a 404 error.

**Arguments**:

- `payload` _DTMCodePayload_ - The payload containing the DTM code to check.

**Returns**:

- `dict` - A dictionary indicating whether the DTM code is valid and providing the
  description of the provider.

<a id="components.dtm.dtm_dem"></a>

#### dtm\_dem

```python
@dtm_router.post("/dem")
@public_limiter(DEFAULT_PUBLIC_LIMIT)
def dtm_dem(payload: DEMSettingsPayload,
            request: Request) -> dict[str, str | bool]
```

Generate a DEM (Digital Elevation Model) based on the provided settings.

**Arguments**:

- `payload` _DEMSettingsPayload_ - The settings payload containing parameters for DEM generation.
  

**Returns**:

- `dict` - A dictionary containing the success status, description, and task ID.

<a id="components.grle"></a>

# components.grle

Generate GRLE data for the given payload.

<a id="components.grle.grle_generation"></a>

#### grle\_generation

```python
@grle_router.post("/plants")
@grle_router.post("/farmlands")
@public_limiter(DEFAULT_PUBLIC_LIMIT)
def grle_generation(payload: GRLESettingsPayload,
                    request: Request) -> dict[str, str | bool]
```

Generate a GRLE (Georeferenced Raster Layer) based on the provided settings.

**Arguments**:

- `payload` _GRLESettingsPayload_ - The settings payload containing parameters for GRLE generation.
  

**Returns**:

- `dict` - A dictionary containing the success status, description, and task ID.

<a id="components.i3d"></a>

# components.i3d

Generate GRLE data for the given payload.

<a id="components.i3d.i3d_generation"></a>

#### i3d\_generation

```python
@i3d_router.post("/fields")
@i3d_router.post("/forests")
@i3d_router.post("/splines")
@public_limiter(DEFAULT_PUBLIC_LIMIT)
def i3d_generation(payload: I3DSettingsPayload,
                   request: Request) -> dict[str, str | bool]
```

Generate a I3D data based on the provided settings.

**Arguments**:

- `payload` _I3DSettingsPayload_ - The settings payload containing parameters for I3D generation.
  

**Returns**:

- `dict` - A dictionary containing the success status, description, and task ID.

<a id="components.map"></a>

# components.map

Generate GRLE data for the given payload.

<a id="components.map.map_generation"></a>

#### map\_generation

```python
@map_router.post("/generate")
@public_limiter(HIGH_DEMAND_PUBLIC_LIMIT)
def map_generation(payload: MapGenerationPayload,
                   request: Request) -> dict[str, str | bool]
```

Generate a complete map based on the provided settings.

**Arguments**:

- `payload` _MapGenerationPayload_ - The settings payload containing parameters for map generation.
  

**Returns**:

- `dict` - A dictionary containing the success status, description, and task ID.

<a id="components.mesh"></a>

# components.mesh

Generate mesh data for the given payload.

<a id="components.mesh.mesh_generation"></a>

#### mesh\_generation

```python
@mesh_router.post("/background")
@mesh_router.post("/water")
@public_limiter(DEFAULT_PUBLIC_LIMIT)
def mesh_generation(payload: BackgroundSettingsPayload,
                    request: Request) -> dict[str, str | bool]
```

Generate a mesh background based on the provided settings.

**Arguments**:

- `payload` _BackgroundSettingsPayload_ - The settings payload containing parameters for mesh generation.
  

**Returns**:

- `dict` - A dictionary containing the success status, description, and task ID.

<a id="components.models"></a>

# components.models

Maps4FS API Models used to validate and structure data for various endpoints.

<a id="components.models.LatLonPayload"></a>

## LatLonPayload Objects

```python
class LatLonPayload(BaseModel)
```

Payload model for latitude and longitude coordinates.

<a id="components.models.DTMCodePayload"></a>

## DTMCodePayload Objects

```python
class DTMCodePayload(BaseModel)
```

Payload model for DTM code.

<a id="components.models.TaskIdPayload"></a>

## TaskIdPayload Objects

```python
class TaskIdPayload(BaseModel)
```

Payload model for task ID.

<a id="components.models.MainSettingsPayload"></a>

## MainSettingsPayload Objects

```python
class MainSettingsPayload(BaseModel)
```

Main settings payload for generating maps with Maps4FS.

<a id="components.models.DEMSettingsPayload"></a>

## DEMSettingsPayload Objects

```python
class DEMSettingsPayload(MainSettingsPayload)
```

Payload model for DEM settings, extending MainSettingsPayload.

<a id="components.models.BackgroundSettingsPayload"></a>

## BackgroundSettingsPayload Objects

```python
class BackgroundSettingsPayload(DEMSettingsPayload)
```

Payload model for Background settings, extending DEMSettingsPayload.

<a id="components.models.GRLESettingsPayload"></a>

## GRLESettingsPayload Objects

```python
class GRLESettingsPayload(MainSettingsPayload)
```

Payload model for GRLE settings, extending MainSettingsPayload.

<a id="components.models.I3DSettingsPayload"></a>

## I3DSettingsPayload Objects

```python
class I3DSettingsPayload(BackgroundSettingsPayload)
```

Payload model for I3D settings, extending BackgroundSettingsPayload.

<a id="components.models.TextureSettingsPayload"></a>

## TextureSettingsPayload Objects

```python
class TextureSettingsPayload(MainSettingsPayload)
```

Payload model for Texture settings, extending MainSettingsPayload.

<a id="components.models.SatelliteSettingsPayload"></a>

## SatelliteSettingsPayload Objects

```python
class SatelliteSettingsPayload(MainSettingsPayload)
```

Payload model for Satellite settings, extending MainSettingsPayload.

<a id="components.models.MapGenerationPayload"></a>

## MapGenerationPayload Objects

```python
class MapGenerationPayload(MainSettingsPayload)
```

Payload model for Map generation settings, extending MainSettingsPayload.

<a id="components.satellite"></a>

# components.satellite

Generate GRLE data for the given payload.

<a id="components.satellite.satellite_generation"></a>

#### satellite\_generation

```python
@satellite_router.post("/overview")
@satellite_router.post("/background")
@public_limiter(DEFAULT_PUBLIC_LIMIT)
def satellite_generation(payload: SatelliteSettingsPayload,
                         request: Request) -> dict[str, str | bool]
```

Generate a satellite data based on the provided settings.

**Arguments**:

- `payload` _SatelliteSettingsPayload_ - The settings payload containing parameters for satellite generation.
  

**Returns**:

- `dict` - A dictionary containing the success status, description, and task ID.

<a id="components.task"></a>

# components.task

Task management for data retrieval in FastAPI application.

<a id="components.task.get_task"></a>

#### get\_task

```python
@task_router.post("/get")
def get_task(payload: TaskIdPayload, background_tasks: BackgroundTasks)
```

Retrieve a task result based on the provided task ID.

**Arguments**:

- `payload` _TaskIdPayload_ - The payload containing the task ID.
- `background_tasks` _BackgroundTasks_ - Background tasks to handle cleanup after response.
  

**Returns**:

- `FileResponse` - A response containing the DEM file if successful, or an error message.

<a id="components.texture"></a>

# components.texture

Generate GRLE data for the given payload.

<a id="components.texture.texture_generation"></a>

#### texture\_generation

```python
@texture_router.post("/images")
@public_limiter(DEFAULT_PUBLIC_LIMIT)
def texture_generation(payload: TextureSettingsPayload,
                       request: Request) -> dict[str, str | bool]
```

Generate a texture data based on the provided settings.

**Arguments**:

- `payload` _I3DSettingsPayload_ - The settings payload containing parameters for I3D generation.
  

**Returns**:

- `dict` - A dictionary containing the success status, description, and task ID.

