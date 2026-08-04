"""
CPB La Crème — procedural jar builder.

Constructs the Clé de Peau Beauté "La Crème" 50ml jar as a parametric cut-crystal
asset: a superellipse (rounded-square) plan swept along a measured height profile,
with broad flat crystal facets split by narrow deep V-grooves, a cushion-cut lid
table, a gold seam band, and an ivory inner well with a cream surface.

    blender -b --factory-startup --python cpb_jar_builder.py -- --out /tmp/cpb_jar.blend

Silhouette (v2, read off the close reference set): an ONION — widest at the seam
in the middle, the lid doming up to the gem table and the body tapering down to a
small rounded base. NOT a barrel.

Everything is parametric. Defaults are eyeballed off photos, NOT calipers:

    blender -b --factory-startup --python cpb_jar_builder.py -- \
        --height 0.083 --width-ratio 0.90 --facets 16 --panel-frac 0.74 \
        --groove-depth 0.13 --plan-exp 3.6 --out jar.blend --export-glb jar.glb

Drops straight into cpb_studio.py via --mesh.

Written against Blender 4.0 and guarded to also run on 4.2 / 4.4 / 5.x.
"""
import bpy, bmesh, sys, os, math
from mathutils import Vector, Matrix

# ---------------------------------------------------------------- args
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(flag, default):
    return argv[argv.index(flag) + 1] if flag in argv else default
def farg(flag, default): return float(arg(flag, default))
def iarg(flag, default): return int(arg(flag, default))

OUT_BLEND   = arg("--out", "/tmp/cpb_jar.blend")
EXPORT_GLB  = arg("--export-glb", "")
EXPORT_OBJ  = arg("--export-obj", "")
JOIN_ONE    = "--join" in argv

# --- master dimensions (metres). Measured: 70mm tall, 63mm wide (ratio 0.90). ---
JAR_H   = farg("--height", 0.070)       # measured overall height
W_RATIO = farg("--width-ratio", 0.90)   # 63mm / 70mm
HALF_W  = 0.5 * JAR_H * W_RATIO         # = 31.5mm, widest radius (dead centre)

# --- form parameters ---
PLAN_EXP    = farg("--plan-exp", 3.6)       # 2=circle, ~4=rounded square (superellipse)
FACETS      = iarg("--facets", iarg("--body-grooves", 18))   # vertical facets around
PANEL_FRAC  = farg("--panel-frac", 0.85)    # fraction of each sector that's flat panel
GROOVE_DEPTH= farg("--groove-depth", 0.12)  # V-groove depth (fraction of local radius)
TABLE_FRAC  = farg("--table-frac", 0.55)    # flat lid table radius as fraction of crown rim
RINGS       = iarg("--rings", 160)          # vertical resolution
SEAM_H      = farg("--seam-h", 0.500)       # seam at dead centre (widest point)
FOOT        = "--no-foot" not in argv       # draw a thin gold foot ring

# ---------------------------------------------------------------- profile
# (height fraction 0..1, radius as fraction of HALF_W). Onion: widest at the seam.
PROFILE = [
    (0.000, 0.440),   # underside centre
    (0.020, 0.560),   # base / foot contact
    (0.060, 0.660),
    (0.120, 0.780),
    (0.190, 0.880),
    (0.270, 0.950),
    (0.360, 0.990),
    (0.440, 1.000),
    (0.500, 1.000),   # -- SEAM, widest, dead centre
    (0.560, 1.000),
    (0.640, 0.990),   # cushion holds width through the middle third
    (0.720, 0.950),
    (0.790, 0.880),
    (0.850, 0.790),
    (0.905, 0.685),
    (0.950, 0.580),
    (0.982, 0.490),   # shoulder into the crown
    (1.000, 0.430),   # crown rim; flat table capped on above
]

# ---------------------------------------------------------------- helpers
def superellipse_r(theta, exp):
    c, s = abs(math.cos(theta)), abs(math.sin(theta))
    return (c ** exp + s ** exp) ** (-1.0 / exp)

def profile_r(h):
    if h <= PROFILE[0][0]: return PROFILE[0][1]
    if h >= PROFILE[-1][0]: return PROFILE[-1][1]
    for (h0, r0), (h1, r1) in zip(PROFILE, PROFILE[1:]):
        if h0 <= h <= h1:
            t = (h - h0) / (h1 - h0) if h1 > h0 else 0.0
            return r0 + t * (r1 - r0)
    return PROFILE[-1][1]

def facet_template(depth):
    """Angular samples for one ring: broad flat panels + narrow deep V-grooves.
    Returns [(angle, radius_multiplier)]; panel edges on the superellipse, groove
    valley dipped inward by `depth`."""
    pts = []
    sector = 2 * math.pi / FACETS
    w = sector * PANEL_FRAC
    for i in range(FACETS):
        c = (i + 0.5) * sector
        aL, aR = c - w / 2, c + w / 2
        b = (i + 1) * sector                      # boundary (groove valley)
        for ang, mult in ((aL, 1.0), (aR, 1.0), (b, 1.0 - depth)):
            pts.append((ang, superellipse_r(ang, PLAN_EXP) * mult))
    return pts

def depth_at(h):
    """Grooves shallow at the seam, deepen toward the crown and base so the
    facets pinch toward points (gem cut), not run as straight flutes."""
    return GROOVE_DEPTH * (0.55 + 1.6 * abs(2.0 * h - 1.0) ** 1.7)

M = len(facet_template(GROOVE_DEPTH))

# smooth (polished) ring for gold band / foot / inner well
SMOOTH_SEG = 120
def smooth_ring_pts():
    return [(2 * math.pi * i / SMOOTH_SEG,
             superellipse_r(2 * math.pi * i / SMOOTH_SEG, PLAN_EXP))
            for i in range(SMOOTH_SEG)]
SMOOTH = smooth_ring_pts()

def finish(bm, name, smooth=False):
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = smooth
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return ob

# ---------------------------------------------------------------- crystal (body + lid + crown)
def build_crystal():
    bm = bmesh.new()
    rings = []
    for k in range(RINGS + 1):
        h = k / RINGS
        pr = profile_r(h)
        tmpl = facet_template(depth_at(h))        # depth varies with height
        ring = [bm.verts.new((HALF_W * pr * mult * math.cos(a),
                              HALF_W * pr * mult * math.sin(a),
                              h * JAR_H)) for a, mult in tmpl]
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for i in range(M):
            j = (i + 1) % M
            bm.faces.new((a[i], a[j], b[j], b[i]))
    # crown: a ring of facets sloping up from the rim to a flat central table
    top = rings[-1]
    tz = top[0].co.z + 0.010 * JAR_H
    table = [bm.verts.new((v.co.x * TABLE_FRAC, v.co.y * TABLE_FRAC, tz)) for v in top]
    for i in range(M):
        j = (i + 1) % M
        bm.faces.new((top[i], top[j], table[j], table[i]))   # radiating crown facets
    bm.faces.new(list(reversed(table)))                       # flat table (monogram sits here)
    # bottom: fan the base ring to a recessed centre (rounded foot underside)
    base = rings[0]
    bctr = bm.verts.new((0, 0, -0.006 * JAR_H))
    for i in range(M):
        j = (i + 1) % M
        bm.faces.new((bctr, base[j], base[i]))
    bm.normal_update()
    return finish(bm, "CPB_Crystal", smooth=False)

# ---------------------------------------------------------------- gold seam band
def build_seam():
    bm = bmesh.new()
    h0, h1 = SEAM_H - 0.010, SEAM_H + 0.010
    lo, hi = [], []
    for a, r in SMOOTH:
        rr = HALF_W * 1.004 * r
        lo.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), h0 * JAR_H)))
        hi.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), h1 * JAR_H)))
    for i in range(SMOOTH_SEG):
        j = (i + 1) % SMOOTH_SEG
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    bm.normal_update()
    return finish(bm, "CPB_SeamBand", smooth=True)

# ---------------------------------------------------------------- gold foot ring
def build_foot():
    bm = bmesh.new()
    rr = 0.54
    top_z, bot_z = 0.030 * JAR_H, 0.004 * JAR_H
    top, bot = [], []
    for a, r in SMOOTH:
        R = HALF_W * rr * r
        top.append(bm.verts.new((R * math.cos(a), R * math.sin(a), top_z)))
        bot.append(bm.verts.new((R * math.cos(a), R * math.sin(a), bot_z)))
    for i in range(SMOOTH_SEG):
        j = (i + 1) % SMOOTH_SEG
        bm.faces.new((bot[i], bot[j], top[j], top[i]))
    bm.normal_update()
    return finish(bm, "CPB_Foot", smooth=True)

# ---------------------------------------------------------------- ivory inner well + cream
def build_inner():
    bm = bmesh.new()
    rr = 0.56
    h0, h1 = 0.10, 0.47
    lo, hi = [], []
    for a, r in SMOOTH:
        R = HALF_W * rr * r
        lo.append(bm.verts.new((R * math.cos(a), R * math.sin(a), h0 * JAR_H)))
        hi.append(bm.verts.new((R * math.cos(a), R * math.sin(a), h1 * JAR_H)))
    for i in range(SMOOTH_SEG):
        j = (i + 1) % SMOOTH_SEG
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    fl = bm.verts.new((0, 0, h0 * JAR_H))
    for i in range(SMOOTH_SEG):
        j = (i + 1) % SMOOTH_SEG
        bm.faces.new((fl, lo[i], lo[j]))
    bm.normal_update()
    well = finish(bm, "CPB_InnerWell", smooth=True)

    bm2 = bmesh.new()
    cz = 0.44 * JAR_H
    ctr = bm2.verts.new((0, 0, cz + 0.01 * JAR_H))
    ring = []
    for a, r in SMOOTH:
        R = HALF_W * rr * 0.9 * r
        ring.append(bm2.verts.new((R * math.cos(a), R * math.sin(a), cz)))
    for i in range(SMOOTH_SEG):
        j = (i + 1) % SMOOTH_SEG
        bm2.faces.new((ctr, ring[i], ring[j]))
    bm2.normal_update()
    cream = finish(bm2, "CPB_Cream", smooth=True)
    return well, cream

# ---------------------------------------------------------------- materials
def principled(name, **kw):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    def setv(sock, val):
        if sock in b.inputs: b.inputs[sock].default_value = val
    for k, v in kw.items():
        setv(k.replace("_", " ").title().replace("Ior", "IOR"), v)
    return m

def crystal_mat():
    m = principled("CPB_CRYSTAL", base_color=(1.0, 0.955, 0.86, 1.0),
                   metallic=0.0, roughness=0.02, ior=1.62)
    b = m.node_tree.nodes["Principled BSDF"]
    for s in ("Transmission Weight", "Transmission"):
        if s in b.inputs: b.inputs[s].default_value = 1.0
    for s in ("Dispersion", "Transmission Dispersion"):
        if s in b.inputs: b.inputs[s].default_value = 0.035
    return m

def gold_mat():  return principled("CPB_GOLD",  base_color=(1.0, 0.82, 0.42, 1.0), metallic=1.0, roughness=0.12)
def ivory_mat(): return principled("CPB_IVORY", base_color=(0.96, 0.92, 0.82, 1.0), metallic=0.0, roughness=0.5)
def cream_mat(): return principled("CPB_CREAM", base_color=(0.98, 0.95, 0.88, 1.0), metallic=0.0, roughness=0.35)

# ---------------------------------------------------------------- build
def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)

    crystal = build_crystal()
    seam    = build_seam()
    well, cream = build_inner()
    parts = [crystal, seam, well, cream]
    crystal.data.materials.append(crystal_mat())
    seam.data.materials.append(gold_mat())
    well.data.materials.append(ivory_mat())
    cream.data.materials.append(cream_mat())
    if FOOT:
        foot = build_foot(); foot.data.materials.append(gold_mat()); parts.append(foot)

    # normalise overall height to exactly JAR_H, base on z=0
    zmin = min(v.co.z for o in parts for v in o.data.vertices)
    zmax = max(v.co.z for o in parts for v in o.data.vertices)
    factor = JAR_H / max(zmax - zmin, 1e-9)
    Mx = Matrix.Translation((0, 0, -zmin * factor)) @ Matrix.Diagonal((factor, factor, factor, 1.0))
    for o in parts:
        o.data.transform(Mx)

    if JOIN_ONE:
        bpy.ops.object.select_all(action='DESELECT')
        for o in parts: o.select_set(True)
        bpy.context.view_layer.objects.active = crystal
        bpy.ops.object.join()
        parts = [crystal]; crystal.name = "CPB_LaCreme"

    allz = [v.co.z for o in parts for v in o.data.vertices]
    print(f"[cpb] built. height = {(max(allz) - min(allz)) * 1000:.1f} mm, "
          f"half-width = {HALF_W * 1000:.1f} mm, facets = {FACETS}, "
          f"panel-frac = {PANEL_FRAC}, groove-depth = {GROOVE_DEPTH}, plan-exp = {PLAN_EXP}")

    def export_obj(path):
        try: bpy.ops.wm.obj_export(filepath=path)
        except AttributeError: bpy.ops.export_scene.obj(filepath=path)
        print("[cpb] exported obj ->", path)

    if OUT_BLEND:
        bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
        print("[cpb] saved blend ->", OUT_BLEND)
    if EXPORT_GLB:
        try:
            bpy.ops.export_scene.gltf(filepath=EXPORT_GLB, export_format='GLB')
            print("[cpb] exported glb ->", EXPORT_GLB)
        except Exception as e:
            print(f"[cpb] glb export failed ({e}); falling back to obj")
            export_obj(os.path.splitext(EXPORT_GLB)[0] + ".obj")
    if EXPORT_OBJ:
        export_obj(EXPORT_OBJ)

main()
