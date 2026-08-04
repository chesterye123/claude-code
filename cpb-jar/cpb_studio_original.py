"""
CPB La Creme — Blender/Cycles product studio.

Renders the jar as real cut crystal: physical refraction, real softbox geometry,
traced caustics on the stone. Swap PRODUCT_MESH to the client's file when it lands;
until then it lathes a stand-in from the proportions measured off the official packshot.

    blender -b --factory-startup --python cpb_studio.py -- --out hero.png --samples 512

Measured from cle-de-peau-packshot-front-official.jpg: width/height 0.90, crown
0.68 of max width, foot ring 0.53, widest through the middle 60%.
"""
import bpy, bmesh, sys, os, math
from mathutils import Vector

# ---------------------------------------------------------------- args
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(flag, default):
    return argv[argv.index(flag) + 1] if flag in argv else default

OUT      = arg("--out", "/tmp/cpb_hero.png")
SAMPLES  = int(arg("--samples", "256"))
RES_X    = int(arg("--resx", "1080"))
RES_Y    = int(arg("--resy", "1920"))
PRODUCT_MESH = arg("--mesh", "")          # client OBJ/FBX/GLB when available
ALPHA    = "--alpha" in argv               # product on transparent, for compositing
FRAMES   = int(arg("--frames", "1"))       # >1 renders a turntable
ROT_DEG  = float(arg("--rot", "90"))       # turntable sweep

# Real product dimensions, 50ml jar
JAR_H = 0.083    # metres
JAR_W = JAR_H * 0.90

# ---------------------------------------------------------------- scene reset
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'GPU'
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'METAL'
prefs.refresh_devices()
for d in prefs.devices:
    d.use = (d.type == 'METAL')

scene.cycles.samples = SAMPLES
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 32
scene.cycles.transmission_bounces = 24     # glass needs depth or it goes black
scene.cycles.transparent_max_bounces = 24
scene.cycles.glossy_bounces = 12
scene.cycles.blur_glossy = 0.5
scene.cycles.caustics_refractive = True
scene.cycles.caustics_reflective = True
try:
    scene.cycles.use_light_tree = True
except AttributeError:
    pass

scene.render.resolution_x = RES_X
scene.render.resolution_y = RES_Y
scene.render.film_transparent = ALPHA
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA' if ALPHA else 'RGB'
scene.render.image_settings.color_depth = '16'
# AgX rolls highlights off like film instead of clipping them
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Base Contrast'


# ---------------------------------------------------------------- product
def build_standin():
    """Lathe the measured profile, then facet it. Stand-in until the client mesh lands."""
    # (height fraction, radius fraction of max width) read off the packshot
    profile = [
        (1.000, 0.000), (0.985, 0.150), (0.955, 0.340), (0.900, 0.430),
        (0.850, 0.455), (0.780, 0.487), (0.700, 0.492), (0.620, 0.494),
        (0.560, 0.496), (0.520, 0.470),                 # seam pinch
        (0.480, 0.496), (0.400, 0.494), (0.320, 0.488),
        (0.240, 0.474), (0.160, 0.418), (0.090, 0.310),
        (0.045, 0.265), (0.010, 0.250), (0.000, 0.235),
    ]
    bm = bmesh.new()
    verts = [bm.verts.new((r * JAR_W, 0.0, h * JAR_H)) for h, r in profile]
    for a, b in zip(verts, verts[1:]):
        bm.edges.new((a, b))
    # 22 segments, flat shaded -> real facets rather than a smooth barrel
    bmesh.ops.spin(bm, geom=bm.verts[:] + bm.edges[:], axis=(0, 0, 1),
                   cent=(0, 0, 0), dvec=(0, 0, 0), angle=math.radians(360),
                   steps=22, use_merge=True)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    me = bpy.data.meshes.new("CPB_JAR")
    bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = False
    ob = bpy.data.objects.new("CPB_JAR", me)
    bpy.context.collection.objects.link(ob)
    return ob


def import_client_mesh(path):
    ext = os.path.splitext(path)[1].lower()
    before = set(bpy.data.objects)
    if ext == '.obj':
        bpy.ops.wm.obj_import(filepath=path)
    elif ext == '.fbx':
        bpy.ops.import_scene.fbx(filepath=path)
    elif ext in ('.glb', '.gltf'):
        bpy.ops.import_scene.gltf(filepath=path)
    elif ext in ('.stl',):
        bpy.ops.wm.stl_import(filepath=path)
    else:
        raise SystemExit(f"unsupported mesh format: {ext} (want obj/fbx/glb/stl)")
    new = [o for o in set(bpy.data.objects) - before if o.type == 'MESH']
    if not new:
        raise SystemExit("no mesh found in import")
    bpy.ops.object.select_all(action='DESELECT')
    for o in new:
        o.select_set(True)
    bpy.context.view_layer.objects.active = new[0]
    if len(new) > 1:
        bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    # normalise to the real 83mm height and sit it on the floor
    dims = ob.dimensions
    ob.scale *= JAR_H / max(dims.z, 1e-6)
    bpy.ops.object.transform_apply(scale=True)
    ob.location.z -= min(v.co.z for v in ob.data.vertices) * ob.scale.z
    return ob


jar = import_client_mesh(PRODUCT_MESH) if PRODUCT_MESH else build_standin()
jar.is_shadow_catcher = False
# MNEE shadow caustics: the jar casts, the stone receives
try:
    jar.is_caustics_caster = True
except AttributeError:
    pass


# ---------------------------------------------------------------- crystal shader
def crystal_material():
    m = bpy.data.materials.new("CPB_CRYSTAL")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (-300, 0)

    def setv(name, val):
        if name in bsdf.inputs:
            bsdf.inputs[name].default_value = val

    setv('Base Color', (1.0, 0.955, 0.86, 1.0))   # champagne tint in the glass
    setv('Metallic', 0.0)
    setv('Roughness', 0.015)
    setv('IOR', 1.62)                              # lead crystal
    setv('Transmission Weight', 1.0)
    setv('Alpha', 1.0)
    # dispersion is what puts real spectral edges on the facets
    for k in ('Dispersion', 'Transmission Dispersion'):
        setv(k, 0.035)

    # micro-imperfection: perfectly clean glass is the loudest CG tell
    noise = nt.nodes.new('ShaderNodeTexNoise'); noise.location = (-900, -200)
    noise.inputs['Scale'].default_value = 380.0
    noise.inputs['Detail'].default_value = 6.0
    ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.location = (-650, -200)
    ramp.color_ramp.elements[0].position = 0.42
    ramp.color_ramp.elements[1].position = 0.72
    ramp.color_ramp.elements[0].color = (0.008, 0.008, 0.008, 1)
    ramp.color_ramp.elements[1].color = (0.075, 0.075, 0.075, 1)
    nt.links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], bsdf.inputs['Roughness'])
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return m


jar.data.materials.append(crystal_material())


# ---------------------------------------------------------------- stone floor
bpy.ops.mesh.primitive_plane_add(size=3.0, location=(0, 0, 0))
floor = bpy.context.object
floor.name = "STONE"
try:
    floor.is_caustics_receiver = True
except AttributeError:
    pass

fm = bpy.data.materials.new("STONE_MAT")
fm.use_nodes = True
nt = fm.node_tree
bsdf = nt.nodes["Principled BSDF"]
bsdf.inputs['Base Color'].default_value = (0.055, 0.040, 0.030, 1.0)
bsdf.inputs['Roughness'].default_value = 0.62
noise = nt.nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 160.0
noise.inputs['Detail'].default_value = 8.0
bump = nt.nodes.new('ShaderNodeBump')
bump.inputs['Strength'].default_value = 0.28
nt.links.new(noise.outputs['Fac'], bump.inputs['Height'])
nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
rough = nt.nodes.new('ShaderNodeTexNoise')
rough.inputs['Scale'].default_value = 40.0
mix = nt.nodes.new('ShaderNodeMapRange')
mix.inputs['To Min'].default_value = 0.45
mix.inputs['To Max'].default_value = 0.72
nt.links.new(rough.outputs['Fac'], mix.inputs['Value'])
nt.links.new(mix.outputs['Result'], bsdf.inputs['Roughness'])
floor.data.materials.append(fm)


# ---------------------------------------------------------------- real fixtures
def softbox(name, loc, rot, w, h, strength, color=(1.0, 0.94, 0.86)):
    """An actual emissive rectangle, so the glass mirrors a real shape with real edges."""
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=loc, rotation=rot)
    ob = bpy.context.object
    ob.name = name
    ob.scale = (w, h, 1.0)
    m = bpy.data.materials.new(name + "_EMIT")
    m.use_nodes = True
    t = m.node_tree
    for n in list(t.nodes):
        t.nodes.remove(n)
    o = t.nodes.new('ShaderNodeOutputMaterial')
    e = t.nodes.new('ShaderNodeEmission')
    e.inputs['Color'].default_value = (*color, 1.0)
    e.inputs['Strength'].default_value = strength
    t.links.new(e.outputs['Emission'], o.inputs['Surface'])
    ob.data.materials.append(m)
    ob.visible_diffuse = True
    return ob

# two vertical strip softboxes, the classic glass-product key
softbox("SOFTBOX_L", (-0.34,  0.10, 0.16), (0, math.radians(90), math.radians(14)),
        0.16, 0.42, 26.0)
softbox("SOFTBOX_R", ( 0.36, -0.06, 0.17), (0, math.radians(-90), math.radians(-12)),
        0.12, 0.40, 16.0)

# hard fresnel high camera-left: this is what throws the caustic web
bpy.ops.object.light_add(type='SPOT', location=(-0.30, 0.26, 0.52))
key = bpy.context.object
key.name = "FRESNEL_KEY"
key.data.energy = 190.0
key.data.spot_size = math.radians(44)
key.data.spot_blend = 0.18
key.data.shadow_soft_size = 0.006   # small source = sharp caustics
key.data.color = (1.0, 0.90, 0.78)
try:
    key.data.use_shadow_caustics = True   # MNEE
except AttributeError:
    pass
key.rotation_euler = (math.radians(52), 0, math.radians(-136))

# white bounce card, fills the shadow side without adding a second key
softbox("BOUNCE", (0.30, 0.30, 0.14), (0, math.radians(-70), math.radians(-40)),
        0.30, 0.26, 2.2, color=(1.0, 0.97, 0.94))

# warm ambient so the background is luminous, not black
world = bpy.data.worlds.new("W"); scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs['Color'].default_value = (0.14, 0.085, 0.052, 1.0)
bg.inputs['Strength'].default_value = 1.1


# ---------------------------------------------------------------- camera
bpy.ops.object.camera_add(location=(0.0, -0.46, 0.055))
cam = bpy.context.object
scene.camera = cam
cam.data.lens = 85.0
cam.data.sensor_width = 36.0
cam.data.dof.use_dof = True
cam.data.dof.focus_object = jar
cam.data.dof.aperture_fstop = 5.6

# aim at the jar's upper third, the way a real product shot sits
target = bpy.data.objects.new("AIM", None)
bpy.context.collection.objects.link(target)
target.location = (0.0, 0.0, JAR_H * 0.58)
c = cam.constraints.new('TRACK_TO')
c.target = target
c.track_axis = 'TRACK_NEGATIVE_Z'
c.up_axis = 'UP_Y'


# ---------------------------------------------------------------- render
if FRAMES > 1:
    jar.rotation_mode = 'XYZ'
    jar.rotation_euler.z = 0.0
    jar.keyframe_insert('rotation_euler', frame=1)
    jar.rotation_euler.z = math.radians(ROT_DEG)
    jar.keyframe_insert('rotation_euler', frame=FRAMES)
    for fc in jar.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'BEZIER'
            kp.easing = 'EASE_IN_OUT'
    scene.frame_start, scene.frame_end = 1, FRAMES
    scene.render.filepath = OUT
    scene.render.image_settings.file_format = 'PNG'
    bpy.ops.render.render(animation=True)
else:
    scene.render.filepath = OUT
    bpy.ops.render.render(write_still=True)

print("RENDERED ->", OUT)
