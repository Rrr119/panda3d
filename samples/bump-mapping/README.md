# Bump Mapping

This older sample demonstrates normal mapping on several materials in the
`abstractroom` model.  The rock material stores a height map in the alpha
channel of its normal map and uses `M_normal_height`, so the pillar also
receives parallax occlusion mapping.

For a smaller, self-contained example that focuses specifically on tangent
space and the POM configuration variables, see
`samples/parallax-mapping`.
