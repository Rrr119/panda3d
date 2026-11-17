# Parallax Occlusion Mapping

Panda3D's shader generator supports parallax occlusion mapping (POM) for
surfaces that have both a normal map and a height map.  POM marches the view
ray through the height field in tangent space and looks up the visible surface
point.  This is more accurate than simple parallax offsetting: tall parts of
the surface can correctly occlude the texture behind them, and the effect does
not swim as the camera moves.

The implementation is enabled automatically when a height map is present and
`parallax-mapping-samples` is greater than zero.  Existing models and shaders
continue to work unchanged; setting the sample count to zero restores ordinary
normal mapping.

## Texture modes

There are two texture stage modes for height maps:

- `TextureStage.M_height` - the height is stored in the RGB channels of a
  separate grayscale texture.
- `TextureStage.M_normal_height` - the normal is stored in RGB and the height
  is stored in alpha.  This packed representation is recommended because it
  needs only one texture lookup per sample.

In an EGG file the equivalent texture environment types are `height` and
`normal_height`:

```
<Texture> brick {
  brick-normal-height.png
  <Scalar> envtype { normal_height }
  <Scalar> format { rgba }
}
```

To set up the packed form in Python:

```python
stage = TextureStage("detail-normal-height")
stage.set_mode(TextureStage.M_normal_height)
model.set_texture(stage, normal_height_texture)
model.set_shader_auto()
```

The height convention is shared by both modes:

- 0 is the base surface.
- 1 is the highest point.

The value is treated as a scalar.  For `M_height`, the red channel is used.
For `M_normal_height`, the alpha channel is used.

Only the first height map on a polygon is used.  Using one height map per
polygon also keeps the generated shader small.

## Tangent space

POM needs a tangent-space view direction, so the mesh must contain a normal,
tangent and binormal for the texture coordinate set used by the height map.
Panda3D exporters can generate them, for example:

```bash
egg-trans -tbn "*" -o model-with-tangents.egg model.egg
```

The EGG representation is a pair of vectors on each texture coordinate:

```
<UV> {
  0.0 0.0
  <Tangent> { 1 0 0 }
  <Binormal> { 0 1 0 }
}
```

The tangent should point along increasing U and the binormal along increasing
V.  The normal map and the height map should use the same texture coordinate
set; otherwise the shader generator can only use one tangent basis for both.

Custom shaders can use the same inputs.  The generated shader receives the
interpolated `p3d_Tangent` and `p3d_Binormal` vertex attributes and transforms
the model-space view direction into the tangent basis before marching.

## Configuration

The effect is controlled by two PRC variables:

```
parallax-mapping-samples 16
parallax-mapping-scale 0.12
```

`parallax-mapping-samples` is the number of layers used by the ray march.  More
layers reduce stair-stepping at the cost of additional height map lookups.  A
value of 0 disables parallax mapping.  The default is 8; 16 is a good choice
for close-up demonstrations.

`parallax-mapping-scale` is the height of the displacement in texture
coordinate units, not in world units.  For a tiled texture, the apparent depth
therefore depends on the tiling rate.  Values between 0.02 and 0.2 work well
for most materials.  Grazing view angles are clamped internally so that the
maximum offset does not grow without bound.

To change these settings at runtime, update the variables and then clear the
shader generator's cache so that the shader is regenerated:

```python
from panda3d.core import ConfigVariableInt

ConfigVariableInt("parallax-mapping-samples").set_value(24)
base.win.get_gsg().get_shader_generator().clear_generated_shaders()
```

## How the generated shader works

For each fragment, the shader:

1. Normalizes the tangent-space view direction.
2. Projects the view direction onto the UV plane, using the configured height
   scale.
3. Marches from the surface into the height field, sampling the height at each
   layer.
4. Detects the first layer that crosses the height field and linearly
   interpolates the UV coordinate between the previous and current layer.
5. Uses that corrected UV for the color, normal and height map lookups.

The step count is constant for a given material, so the shader is unrolled at
generation time to avoid depending on dynamic branching support.

## Example

The `samples/parallax-mapping` sample generates its textures procedurally and
creates a quad with explicit tangent and binormal columns.  It starts with POM
enabled and lets you press `Space` to compare the result with normal mapping
only.

The older `samples/bump-mapping` sample also uses POM for the rock pillar; its
height map is packed into the alpha channel of the rock normal map.
