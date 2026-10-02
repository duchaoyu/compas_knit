# Pipeline overview

<!-- TODO: diagram of the whole pipeline -->
<!-- ![](../.gitbook/assets/pipeline.png) -->

| Step | Input | Output | Code |
|---|---|---|---|
| 1. Directional field | mesh | `<name>_vertex_directional_field.txt` | <!-- TODO --> |
| 2. Trajectories | mesh, field, stitch height | `<name>_tri_path.txt` | [`generate_stripes`](../api/stripes.md#generate_stripes) |
| 3. Ordering | trajectories | `<name>_neighbours.txt` | `stripes`, [`read_neighbours`](../api/stripes.md#read_neighbours) |
| 4. Sequence, bitmap | stitches, neighbours | `<name>_bitmap.bmp`, `<name>_pixel_data_dict.pkl` | [`knitting_pattern`](../api/pattern.md) |
| 5. Pixel post-processing | <!-- TODO --> | <!-- TODO --> | `3_pixel_data_postprocess.py` |
| 6. Splitting | <!-- TODO --> | <!-- TODO --> | `4_bitmap_split.py` |
| 7. Channels | <!-- TODO --> | <!-- TODO --> | `5_add_channel.py` |

## 1. Directional field

<!-- TODO: what the field means (wale direction?), how it is designed -->

## 2. Trajectories

The trajectories are the isolines of a stripe pattern aligned with the field, see
[Stripe patterns and singularities](stripe-patterns.md). They run across the field, and adjacent
trajectories are placed `2 * stitch_height / stretch_wale` apart, and divided into stitches `stitch_width / stretch_course`
apart, as each is knitted out and back as two courses.

## 3. – 7.

<!-- TODO -->
