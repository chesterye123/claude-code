"""
CPB La Crème — Blender/Cycles product studio (patched).

Same studio as the original handoff, with three changes so it renders the real
multi-material jar on any machine:

  1. Device auto-detect. The original hard-wired Apple METAL and disabled every
     other device, which silently falls back to nothing on a Linux/NVIDIA box.
     This tries OPTIX > CUDA > METAL > HIP > ONEAPI and lands on CPU if there's
     no GPU. Override with --device CPU|CUDA|OPTIX|METAL|HIP|ONEAPI.
  2. Denoise is guarded so a build without OpenImageDenoise doesn't error out.
  3. Material by slot name. The crystal shader is applied to slots whose name
     contains CRYSTAL/GLASS; GOLD/IVORY/CREAM slots get their own shaders. A
     single-material or material-less mesh (the old stand-in) gets crystal on
     everything, exactly as before.

    blender -b --factory-startup --python cpb_studio.py -- --mesh jar.glb --out hero.png --samples 512
    blender -b --factory-startup --python cpb_studio.py -- --mesh jar.obj --alpha --out plate.png
    blender -b --factory-startup --python cpb_studio.py -- --mesh jar.glb --frames 96 --rot 90 --out //turn/
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
PRODUCT_MESH = arg("--mesh", "")
ALPHA    = "--alpha" in argv
FRAMES   = int(arg("--frames", "1"))
ROT_DEG  = float(arg("--rot", "90"))
DEVICE   = arg("--device", "AUTO").upper()   # AUTO|CPU|CUDA|OPTIX|METAL|HIP|ONEAPI

# Real product dimensions, 50ml jar
JAR_H = 0.083
JAR_W = JAR_H * 0.90

# ---------------------------------------------------------------- scene reset
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'

# --- device auto-detect ---------------------------------------------------
def setup_device():
    prefs = bpy.context.preferences.addons['cycles'].preferences
    order = [DEVICE] if DEVICE not in ('AUTO', '') else ['OPTIX', 'CUDA', 'METAL', 'HIP', 'ONEAPI']
    if DEVICE == 'CPU':
        scene.cycles.device = 'CPU'
        print("[studio] device = CPU (forced)")
        return
    for backend in order:
        try:
            prefs.compute_device_type = backend
        except (TypeError, ValueError):
            continue
        prefs.refresh_devices()
        gpus = [d for d in prefs.devices if d.type == backend]
        if gpus:
            for d in prefs.devices:
                d.use = (d.type == backend) or (d.type == 'CPU' and False)
            scene.cycles.device = 'GPU'
            print(f"[studio] device = GPU / {backend} ({len(gpus)} device(s))")
            return
    scene.cycles.device = 'CPU'
    print("[studio] device = CPU (no GPU backend available)")

setup_device()

scene.cycles.samples = SAMPLES
try:
    scene.cycles.use_denoising = True
except Exception:
    pass
scene.cycles.max_bounces = 32
scene.cycles.transmission_bounces = 24
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
try:
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Base Contrast'
except Exception:
    scene.view_settings.view_transform = 'Filmic'


# ---------------------------------------------------------------- shaders
def _principled(m):
    m.use_nodes = True
    return m.node_tree.nodes.get("Principled BSDF") or m.node_tree.nodes["Principled BSDF"]

def crystal_shader(m):
    for n in list(m.node_tree.nodes):
        m.node_tree.nodes.remove(n)
    nt = m.node_tree
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled'); bsdf.location = (-300, 0)
    def setv(name, val):
        if name in bsdf.inputs: bsdf.inputs[name].default_value = val
    setv('Base Color', (1.0, 0.955, 0.86, 1.0))
    setv('Metallic', 0.0)
    setv('Roughness', 0.015)
    setv('IOR', 1.62)
    setv('Transmission Weight', 1.0); setv('Transmission', 1.0)
    setv('Alpha', 1.0)
    for k in ('Dispersion', 'Transmission Dispersion'):
        setv(k, 0.035)
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

def gold_shader(m):
    b = _principled(m)
    def setv(k, v):
        if k in b.inputs: b.inputs[k].default_value = v
    setv('Base Color', (1.0, 0.82, 0.42, 1.0)); setv('Metallic', 1.0); setv('Roughness', 0.12)
    return m

def ivory_shader(m):
    b = _principled(m)
    def setv(k, v):
        if k in b.inputs: b.inputs[k].default_value = v
    setv('Base Color', (0.96, 0.92, 0.82, 1.0)); setv('Metallic', 0.0); setv('Roughness', 0.5)
    return m

def cream_shader(m):
    b = _principled(m)
    def setv(k, v):
        if k in b.inputs: b.inputs[k].default_value = v
    setv('Base Color', (0.98, 0.95, 0.88, 1.0)); setv('Metallic', 0.0); setv('Roughness', 0.35)
    return m

def apply_materials(ob):
    """Assign shaders by slot name. Fall back to all-crystal for a bare mesh."""
    mats = ob.data.materials
    if len(mats) == 0:
        m = bpy.data.materials.new("CPB_CRYSTAL"); crystal_shader(m)
        mats.append(m)
        return
    for slot in mats:
        if slot is None:
            continue
        name = slot.name.upper()
        if any(k in name for k in ('GOLD', 'METAL', 'BRASS')):
            gold_shader(slot)
        elif any(k in name for k in ('IVORY', 'WELL')):
            ivory_shader(slot)
        elif 'CREAM' in name:
            cream_shader(slot)
        else:
            crystal_shader(slot)   # CRYSTAL / GLASS / anything else


# ---------------------------------------------------------------- product
def build_standin():
    profile = [
        (1.000, 0.000), (0.985, 0.150), (0.955, 0.340), (0.900, 0.430),
        (0.850, 0.455), (0.780, 0.487), (0.700, 0.492), (0.620, 0.494),
        (0.560, 0.496), (0.520, 0.470),
        (0.480, 0.496), (0.400, 0.494), (0.320, 0.488),
        (0.240, 0.474), (0.160, 0.418), (0.090, 0.310),
        (0.045, 0.265), (0.010, 0.250), (0.000, 0.235),
    ]
    bm = bmesh.new()
    verts = [bm.verts.new((r * JAR_W, 0.0, h * JAR_H)) for h, r in profile]
    for a, b in zip(verts, verts[1:]):
        bm.edges.new((a, b))
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
        try: bpy.ops.wm.obj_import(filepath=path)
        except AttributeError: bpy.ops.import_scene.obj(filepath=path)
    elif ext == '.fbx':
        bpy.ops.import_scene.fbx(filepath=path)
    elif ext in ('.glb', '.gltf'):
        bpy.ops.import_scene.gltf(filepath=path)
    elif ext in ('.stl',):
        try: bpy.ops.wm.stl_import(filepath=path)
        except AttributeError: bpy.ops.import_mesh.stl(filepath=path)
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
        bpy.ops.object.join()          # keeps per-face material slots
    ob = bpy.context.view_layer.objects.active
    dims = ob.dimensions
    ob.scale *= JAR_H / max(dims.z, 1e-6)
    bpy.ops.object.transform_apply(scale=True)
    ob.location.z -= min(v.co.z for v in ob.data.vertices) * ob.scale.z
    return ob


jar = import_client_mesh(PRODUCT_MESH) if PRODUCT_MESH else build_standin()
apply_materials(jar)
jar.is_shadow_catcher = False
try:
    jar.is_caustics_caster = True
except AttributeError:
    pass


# ---------------------------------------------------------------- stone floor
bpy.ops.mesh.primitive_plane_add(size=3.0, location=(0, 0, 0))
floor = bpy.context.object
floor.name = "STONE"
try:
    floor.is_caustics_receiver = True
except AttributeError:
    pass

fm = bpy.data.materials.new("STONE_MAT"); fm.use_nodes = True
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


# ---------------------------------------------------------------- fixtures
def softbox(name, loc, rot, w, h, strength, color=(1.0, 0.94, 0.86)):
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=loc, rotation=rot)
    ob = bpy.context.object; ob.name = name; ob.scale = (w, h, 1.0)
    m = bpy.data.materials.new(name + "_EMIT"); m.use_nodes = True
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

softbox("SOFTBOX_L", (-0.34,  0.10, 0.16), (0, math.radians(90), math.radians(14)), 0.16, 0.42, 26.0)
softbox("SOFTBOX_R", ( 0.36, -0.06, 0.17), (0, math.radians(-90), math.radians(-12)), 0.12, 0.40, 16.0)

bpy.ops.object.light_add(type='SPOT', location=(-0.30, 0.26, 0.52))
key = bpy.context.object; key.name = "FRESNEL_KEY"
key.data.energy = 190.0
key.data.spot_size = math.radians(44)
key.data.spot_blend = 0.18
key.data.shadow_soft_size = 0.006
key.data.color = (1.0, 0.90, 0.78)
try:
    key.data.use_shadow_caustics = True
except AttributeError:
    pass
key.rotation_euler = (math.radians(52), 0, math.radians(-136))

softbox("BOUNCE", (0.30, 0.30, 0.14), (0, math.radians(-70), math.radians(-40)), 0.30, 0.26, 2.2,
        color=(1.0, 0.97, 0.94))

world = bpy.data.worlds.new("W"); scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs['Color'].default_value = (0.14, 0.085, 0.052, 1.0)
bg.inputs['Strength'].default_value = 1.1


# ---------------------------------------------------------------- camera
bpy.ops.object.camera_add(location=(0.0, -0.46, 0.055))
cam = bpy.context.object; scene.camera = cam
cam.data.lens = 85.0
cam.data.sensor_width = 36.0
cam.data.dof.use_dof = True
cam.data.dof.focus_object = jar
cam.data.dof.aperture_fstop = 5.6

target = bpy.data.objects.new("AIM", None)
bpy.context.collection.objects.link(target)
target.location = (0.0, 0.0, JAR_H * 0.58)
c = cam.constraints.new('TRACK_TO')
c.target = target
c.track_axis = 'TRACK_NEGATIVE_Z'
c.up_axis = 'UP_Y'


# ---------------------------------------------------------------- render
def render(animation):
    """Render, and if the build has no OpenImageDenoise, retry without it."""
    try:
        bpy.ops.render.render(animation=animation, write_still=not animation)
    except RuntimeError as e:
        if 'OpenImageDenois' in str(e) or 'denois' in str(e).lower():
            print("[studio] no denoiser in this build; rendering without denoising")
            scene.cycles.use_denoising = False
            bpy.ops.render.render(animation=animation, write_still=not animation)
        else:
            raise

if FRAMES > 1:
    jar.rotation_mode = 'XYZ'
    jar.rotation_euler.z = 0.0
    jar.keyframe_insert('rotation_euler', frame=1)
    jar.rotation_euler.z = math.radians(ROT_DEG)
    jar.keyframe_insert('rotation_euler', frame=FRAMES)
    for fc in jar.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'BEZIER'; kp.easing = 'EASE_IN_OUT'
    scene.frame_start, scene.frame_end = 1, FRAMES
    scene.render.filepath = OUT
    render(animation=True)
else:
    scene.render.filepath = OUT
    render(animation=False)

print("RENDERED ->", OUT)
