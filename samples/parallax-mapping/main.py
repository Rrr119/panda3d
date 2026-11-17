#!/usr/bin/env python

"""
Parallax occlusion mapping (POM) example.

The wall is built from a normal map with the height map packed into its alpha
channel, which is the most efficient representation for the shader generator.
The plane carries explicit tangent and binormal columns, since POM marches the
view ray in tangent space.  Press space to compare POM against normal mapping
only.
"""

import math

from direct.gui.OnscreenText import OnscreenText
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import (
    AmbientLight, Geom, GeomNode, GeomTriangles, GeomVertexArrayFormat,
    GeomVertexData, GeomVertexFormat, GeomVertexWriter, InternalName,
    LVector3, NodePath, PNMImage, PointLight, Texture, TextureStage, TextNode,
    loadPrcFileData,
)


TEXTURE_SIZE = 256


def add_text(pos, text):
    return OnscreenText(
        text=text, style=1, fg=(1, 1, 1, 1), shadow=(0, 0, 0, 1),
        parent=base.a2dTopLeft, align=TextNode.ALeft,
        pos=(0.06, -pos - 0.04), scale=0.05)


def brick_height(u, v):
    """Returns a tileable height value in the range 0 to 1."""
    rows = 6
    cols = 3
    row = int(v * rows)
    offset = 0.5 if (row & 1) else 0.0
    bu = (u * cols + offset) % 1.0
    bv = (v * rows) % 1.0

    edge_u = min(bu, 1.0 - bu)
    edge_v = min(bv, 1.0 - bv)
    if edge_u < 0.035 or edge_v < 0.055:
        return 0.04

    bevel = min((edge_u - 0.035) / 0.06, (edge_v - 0.055) / 0.06, 1.0)
    bevel = bevel * bevel * (3.0 - 2.0 * bevel)
    noise = (0.025 * math.sin(2.0 * math.pi * (u * 9.0 + v * 5.0)) +
             0.015 * math.sin(2.0 * math.pi * (u * 23.0 - v * 13.0)))
    return max(0.0, min(1.0, 0.50 + 0.42 * bevel + noise))


def make_textures():
    heights = [
        [0.0] * TEXTURE_SIZE for _ in range(TEXTURE_SIZE)
    ]
    for y in range(TEXTURE_SIZE):
        for x in range(TEXTURE_SIZE):
            heights[y][x] = brick_height(x / TEXTURE_SIZE, y / TEXTURE_SIZE)

    color_image = PNMImage(TEXTURE_SIZE, TEXTURE_SIZE, 3)
    normal_image = PNMImage(TEXTURE_SIZE, TEXTURE_SIZE, 4)
    normal_strength = 7.0

    for y in range(TEXTURE_SIZE):
        for x in range(TEXTURE_SIZE):
            height = heights[y][x]
            height_right = heights[y][(x + 1) % TEXTURE_SIZE]
            height_left = heights[y][(x - 1) % TEXTURE_SIZE]
            height_up = heights[(y + 1) % TEXTURE_SIZE][x]
            height_down = heights[(y - 1) % TEXTURE_SIZE][x]

            normal = LVector3(
                -(height_right - height_left) * normal_strength,
                -(height_up - height_down) * normal_strength,
                1.0)
            normal.normalize()
            normal_image.set_xel_a(
                x, y, normal.x * 0.5 + 0.5, normal.y * 0.5 + 0.5,
                normal.z * 0.5 + 0.5, height)

            if height < 0.1:
                color = (0.30, 0.30, 0.32)
            else:
                row = int((y / TEXTURE_SIZE) * 6)
                tint = 0.85 + 0.15 * ((row * 37) % 5) / 4.0
                color = (0.62 * tint, 0.25 * tint, 0.13 * tint)
            color_image.set_xel(x, y, *color)

    color_tex = Texture("pom-brick-color")
    color_tex.load(color_image)
    color_tex.set_wrap_u(Texture.WM_repeat)
    color_tex.set_wrap_v(Texture.WM_repeat)
    color_tex.set_minfilter(Texture.FT_linear_mipmap_linear)
    color_tex.set_magfilter(Texture.FT_linear)
    color_tex.set_anisotropic_degree(8)

    normal_tex = Texture("pom-brick-normal-height")
    normal_tex.load(normal_image)
    normal_tex.set_wrap_u(Texture.WM_repeat)
    normal_tex.set_wrap_v(Texture.WM_repeat)
    normal_tex.set_minfilter(Texture.FT_linear_mipmap_linear)
    normal_tex.set_magfilter(Texture.FT_linear)
    normal_tex.set_anisotropic_degree(8)
    return color_tex, normal_tex


def make_wall():
    """Creates a quad with vertex, normal, UV, tangent and binormal data."""
    vertex_format = GeomVertexFormat(GeomVertexFormat.get_v3n3t2())
    tangent_format = GeomVertexArrayFormat()
    tangent_format.add_column(
        InternalName.get_tangent(), 3, Geom.NT_float32, Geom.C_other)
    tangent_format.add_column(
        InternalName.get_binormal(), 3, Geom.NT_float32, Geom.C_other)
    vertex_format.add_array(tangent_format)
    vertex_format = GeomVertexFormat.register_format(vertex_format)

    data = GeomVertexData("POMWall", vertex_format, Geom.UH_static)
    data.set_num_rows(4)
    vertex = GeomVertexWriter(data, InternalName.get_vertex())
    normal = GeomVertexWriter(data, InternalName.get_normal())
    texcoord = GeomVertexWriter(data, InternalName.get_texcoord())
    tangent = GeomVertexWriter(data, InternalName.get_tangent())
    binormal = GeomVertexWriter(data, InternalName.get_binormal())

    positions = (
        (-2.0, 0.0, -2.0, 0.0, 0.0),
        (2.0, 0.0, -2.0, 1.0, 0.0),
        (2.0, 0.0, 2.0, 1.0, 1.0),
        (-2.0, 0.0, 2.0, 0.0, 1.0),
    )
    for x, y, z, u, v in positions:
        vertex.add_data3(x, y, z)
        normal.add_data3(0.0, -1.0, 0.0)
        texcoord.add_data2(u, v)
        tangent.add_data3(1.0, 0.0, 0.0)
        binormal.add_data3(0.0, 0.0, 1.0)

    triangles = GeomTriangles(Geom.UH_static)
    triangles.add_vertices(0, 1, 2)
    triangles.add_vertices(0, 2, 3)
    geom = Geom(data)
    geom.add_primitive(triangles)
    node = GeomNode("POMWall")
    node.add_geom(geom)
    return NodePath(node)


class ParallaxDemo(ShowBase):
    def __init__(self):
        loadPrcFileData(
            "", "parallax-mapping-samples 16\n"
                "parallax-mapping-scale 0.12")
        ShowBase.__init__(self)

        self.setBackgroundColor(0.04, 0.05, 0.07, 1.0)
        self.disableMouse()

        self.wall = make_wall()
        self.wall.reparent_to(render)

        color_tex, normal_tex = make_textures()
        color_stage = TextureStage("color")
        color_stage.set_sort(0)
        self.wall.set_texture(color_stage, color_tex)

        self.height_stage = TextureStage("normal-height")
        self.height_stage.set_sort(1)
        self.height_stage.set_mode(TextureStage.M_normal_height)
        self.wall.set_texture(self.height_stage, normal_tex)
        self.wall.set_shader_auto()

        ambient = AmbientLight("ambient")
        ambient.set_color((0.20, 0.22, 0.28, 1.0))
        render.set_light(render.attach_new_node(ambient))

        point = PointLight("point")
        point.set_color((1.0, 0.92, 0.82, 1.0))
        point.set_attenuation(LVector3(1.0, 0.0, 0.0))
        self.light = render.attach_new_node(point)
        self.light.set_pos(2.5, -3.0, 3.0)
        render.set_light(self.light)

        add_text(0.0, "Panda3D: Parallax Occlusion Mapping")
        add_text(0.07, "Space: toggle POM / normal mapping")
        add_text(0.13, "16 ray-march layers, tangent-space height map")
        self.status = add_text(0.19, "POM enabled")

        self.use_pom = True
        self.accept("space", self.toggle_pom)
        self.task_mgr.add(self.orbit_camera, "orbit-camera")
        self.task_mgr.add(self.move_light, "move-light")

    def toggle_pom(self):
        self.use_pom = not self.use_pom
        if self.use_pom:
            self.height_stage.set_mode(TextureStage.M_normal_height)
            self.status.set_text("POM enabled")
        else:
            self.height_stage.set_mode(TextureStage.M_normal)
            self.status.set_text("POM disabled (normal mapping only)")
        # TextureStage is mutable, so toggle the shader attrib as well to make
        # sure the generated shader is re-evaluated.
        self.wall.set_shader_auto(False)
        self.wall.set_shader_auto()

    def orbit_camera(self, task):
        angle = math.sin(task.time * 0.25) * 0.9
        self.camera.set_pos(
            math.sin(angle) * 6.5, -math.cos(angle) * 6.5, 1.4)
        self.camera.look_at(0.0, 0.0, 0.0)
        return Task.cont

    def move_light(self, task):
        angle = task.time * 0.7
        self.light.set_pos(
            math.sin(angle) * 3.0, -3.2, 2.5 + math.cos(angle) * 1.0)
        return Task.cont


demo = ParallaxDemo()
demo.run()
