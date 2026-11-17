# Parallax Occlusion Mapping

This sample shows how to use the shader generator's parallax occlusion mapping
(POM) support with a tangent-space normal map and an embedded height map.

The brick wall is generated procedurally, so no external assets are required.
The normal map stores the normal in RGB and the height in alpha.  The wall
geometry contains explicit tangent and binormal columns, which the shader
generator uses to transform the view direction into tangent space.

Run the sample with:

```bash
python main.py
```

Press `Space` to switch between:

- `M_normal_height` - POM enabled.
- `M_normal` - normal mapping only, with the height channel ignored.

The relevant PRC settings are:

```
parallax-mapping-samples 16
parallax-mapping-scale 0.12
```

`parallax-mapping-samples` controls the number of ray-march layers.
`parallax-mapping-scale` controls the height of the displacement in texture
coordinate units.  Set the sample count to 0 to disable parallax mapping
entirely.

See `doc/parallax-mapping.md` in the Panda3D source tree for a more detailed
explanation and for the requirements on exported models.
