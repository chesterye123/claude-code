"""
Fast clay preview of the jar geometry — matte override, low samples, a few angles.
Purpose is to read silhouette / facet count / facet depth, not final look.

    blender -b --factory-startup --python cpb_preview.py -- --blend /tmp/cpb_jar.blend --out /tmp/prev
"""
import bpy, sys, math
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(f, d): return argv[argv.index(f) + 1] if f in argv else d
BLEND = arg("--blend", "/tmp/cpb_jar.blend")
OUT   = arg("--out", "/tmp/prev")
SAMPLES = int(arg("--samples", "24"))
RES = int(arg("--res", "560"))

bpy.ops.wm.open_mainfile(filepath=BLEND)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles.samples = SAMPLES
try:
    sc.cycles.use_denoising = True
except Exception:
    pass
if "--no-denoise" in argv:
    sc.cycles.use_denoising = False
sc.render.resolution_x = RES
sc.render.resolution_y = RES
sc.render.film_transparent = False
try:
    sc.view_settings.view_transform = 'AgX'
except Exception:
    sc.view_settings.view_transform = 'Filmic'

# clay override so we see form, not glass
clay = bpy.data.materials.new("CLAY"); clay.use_nodes = True
b = clay.node_tree.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.62, 0.62, 0.64, 1.0)
b.inputs["Roughness"].default_value = 0.55
sc.view_layers[0].material_override = clay

# bounds / centre
objs = [o for o in sc.objects if o.type == 'MESH']
zs = [(o.matrix_world @ Vector(c)).z for o in objs for c in o.bound_box]
xs = [(o.matrix_world @ Vector(c)).x for o in objs for c in o.bound_box]
zc = (min(zs) + max(zs)) / 2
H = max(zs) - min(zs)
R = max(abs(min(xs)), abs(max(xs)))

# world light
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.25
# suns: distance-independent, easy to expose
bpy.ops.object.light_add(type='SUN', location=(R*4, -R*4, zc + H))
k = bpy.context.object; k.data.energy = 3.0; k.data.angle = math.radians(3)
k.rotation_euler = (math.radians(55), 0, math.radians(35))
bpy.ops.object.light_add(type='SUN', location=(-R*4, -R*2, zc + H))
f = bpy.context.object; f.data.energy = 1.2; f.data.angle = math.radians(6)
f.rotation_euler = (math.radians(60), 0, math.radians(-40))

target = bpy.data.objects.new("AIM", None); sc.collection.objects.link(target)
target.location = (0, 0, zc)

bpy.ops.object.camera_add()
cam = bpy.context.object; sc.camera = cam
cam.data.lens = 85; cam.data.sensor_width = 36
c = cam.constraints.new('TRACK_TO'); c.target = target
c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'

dist = R * 6.5
views = {
    "front": (0.0, -dist, zc),
    "tq":    (-dist*0.7, -dist*0.7, zc + H*0.12),
    "side":  (-dist, 0.0, zc),
    "top":   (0.0, -0.001, zc + dist),
}
for name, loc in views.items():
    cam.location = loc
    sc.render.filepath = f"{OUT}_{name}.png"
    bpy.ops.render.render(write_still=True)
    print("[prev] wrote", sc.render.filepath)
