| Section   | Endpoint  | Component | Required payload                                               | Output                                      | Heavy (require queue) |
|-----------|-----------|-----------|----------------------------------------------------------------|---------------------------------------------|-----------------------|
| DTM       | /get_list | DTM       | lat, lon                                                       | list of DTM codes                           | ❌                    |
| DTM       | /is_valid | DTM       | dtm_code                                                       | DTM description or error message            | ❌                    |
| DEM       | /get_dem  | Background| lat, lon, map_size, rotation, output_size, dem_code            | dem image                                   | ✅                    |
| Backround | /get_bg   | Background| lat, lon, map_size, rotation, output_size, dem_code            | background mesh                             | ✅                    |
| Backround | /get_water| Background| lat, lon, map_size, rotation, output_size, dem_code            | water mesh (elevated)                       | ✅                    |
| Backround | /get_water| Background| lat, lon, map_size, rotation, output_size, dem_code            | water mesh (plane)                          | ✅                    |



✅ GRLE:
- Farmlands (image) If no textures were created, create a new instance automatically
- Plants (image) If no textures were created, create a new instance automatically

✅ I3D:
- Fields (XML part that can be injected to the map I3D file)
- Trees (XML part that can be injected to the map I3D file)
- Splines (separate I3D file) If no textures were created, create a new instance automatically

✅ Texture:
- Images by provided texture schema or default one (zip archive with images)

Complete generation:
- Completely generated map (zip archive with all files) -> Disable on public API, only for private use
