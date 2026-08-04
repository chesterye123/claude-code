"""
CPB La Crème — procedural jar builder.

Constructs the Clé de Peau Beauté "La Crème" 50ml jar as a parametric cut-crystal
asset: a superellipse (rounded-square) plan swept along a measured height profile,
with sharp vertical V-cuts faceted directly into the cross-section, a gem-cut lid
table, a gold seam band and foot ring, and an ivory inner well with a cream surface.

    blender -b --factory-startup --python cpb_jar_builder.py -- --out /tmp/cpb_jar.blend

Everything is parametric. The defaults are read off the five reference photos, NOT
off calipers — measure the real jar and pass the real numbers:

    blender -b --factory-startup --python cpb_jar_builder.py -- \
        --height 0.083 --width-ratio 0.90 --body-grooves 20 --groove-depth 0.10 \
        --plan-exp 3.2 --table-facets 16 --out jar.blend --export-glb jar.glb

The mesh it writes is meant to drop straight into cpb_studio.py:

    blender -b --factory-startup --python cpb_studio.py -- --mesh jar.glb --out hero.png

Written against the Blender 4.0 API and guarded to also run on 4.2 / 4.4 / 5.x:
socket names and operators that moved between versions are wrapped.
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
JOIN_ONE    = "--join" in argv          # join everything into one multi-slot object

# --- master dimensions (metres). VERIFY THESE AGAINST THE REAL JAR. ---
JAR_H   = farg("--height", 0.083)       # overall height
W_RATIO = farg("--width-ratio", 0.90)   # width / height
HALF_W  = 0.5 * JAR_H * W_RATIO         # max half-width (radius at widest)

# --- form parameters (read off the photos, tune to taste) ---
PLAN_EXP     = farg("--plan-exp", 3.4)      # superellipse exponent: 2=circle, ~4=rounded square
BODY_GROOVES = iarg("--body-grooves", 20)   # count of vertical V-cuts around the body
GROOVE_DEPTH = farg("--groove-depth", 0.16) # V-cut depth as a fraction of local radius
TABLE_FACETS = iarg("--table-facets", 16)   # radiating triangles on the lid crown
RINGS        = iarg("--rings", 200)         # vertical resolution of the swept body
SEAM_H       = farg("--seam-h", 0.455)      # height fraction of the gold seam band centre

# ---------------------------------------------------------------- profile
# (height fraction 0..1, radius as fraction of HALF_W). Read off the front elevation.
# Widest and held flat through the middle 60%; domed faceted crown up top; foot below.
PROFILE = [
    (0.000, 0.000),   # base centre (starburst apex, underside)
    (0.010, 0.360),
    (0.020, 0.530),   # gold foot ring contact
    (0.045, 0.520),
    (0.075, 0.470),   # pinch above the foot
    (0.120, 0.680),
    (0.175, 0.860),
    (0.220, 0.960),
    (0.300, 1.000),   # -- widest, start of the flat middle
    (0.455, 1.000),   # -- seam band sits here
    (0.560, 1.000),
    (0.640, 0.995),   # -- end of the flat middle, dome begins
    (0.720, 0.975),
    (0.800, 0.930),
    (0.870, 0.860),
    (0.930, 0.770),
    (0.975, 0.700),
    (1.000, 0.680),   # crown table edge
]

# ---------------------------------------------------------------- helpers
def superellipse_r(theta, exp):
    """Unit-halfwidth superellipse radius at angle theta. exp=2 circle, larger = squarer."""
    c, s = abs(math.cos(theta)), abs(math.sin(theta))
    return (c ** exp + s ** exp) ** (-1.0 / exp)

def profile_r(h):
    """Linear-interpolated radius fraction at height fraction h in [0,1]."""
    if h <= PROFILE[0][0]:
        return PROFILE[0][1]
    if h >= PROFILE[-1][0]:
        return PROFILE[-1][1]
    for (h0, r0), (h1, r1) in zip(PROFILE, PROFILE[1:]):
        if h0 <= h <= h1:
            t = (h - h0) / (h1 - h0) if h1 > h0 else 0.0
            return r0 + t * (r1 - r0)
    return PROFILE[-1][1]

def groove_scale(theta):
    """V-cut multiplier: 1.0 on a ridge, (1-depth) in a valley. Sharp triangle wave."""
    if BODY_GROOVES <= 0 or GROOVE_DEPTH <= 0:
        return 1.0
    ph = (theta * BODY_GROOVES) / (2 * math.pi)
    ph -= math.floor(ph)                     # 0..1 within one groove
    tri = abs(2.0 * ph - 1.0)                # 1 at ridge (edges), 0 at valley (centre)
    return 1.0 - GROOVE_DEPTH * (1.0 - tri)

def new_bmesh_obj(name):
    return bmesh.new(), name

def finish(bm, name, smooth=False):
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = smooth
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return ob

# angular sampling: ridge + valley per groove => 2 samples/groove, plus corner density
SEG = max(BODY_GROOVES * 2, 48)
def angles():
    return [2 * math.pi * i / SEG for i in range(SEG)]

# ---------------------------------------------------------------- crystal body
def build_body():
    bm = bmesh.new()
    ths = angles()
    # sample heights: dense, but skip the very top (h=1) — the crown cap closes it
    hs = [i / RINGS for i in range(RINGS + 1)]
    rings = []
    for h in hs:
        pr = profile_r(h)
        ring = []
        for th in ths:
            r = HALF_W * pr * superellipse_r(th, PLAN_EXP) * groove_scale(th)
            ring.append(bm.verts.new((r * math.cos(th), r * math.sin(th), h * JAR_H)))
        rings.append(ring)
    # side quads
    for a, b in zip(rings, rings[1:]):
        for i in range(SEG):
            j = (i + 1) % SEG
            bm.faces.new((a[i], a[j], b[j], b[i]))
    # bottom cap (fan to a centre vertex sitting slightly under the base ring)
    base_ring = rings[0]
    cz = -0.004 * JAR_H
    cbot = bm.verts.new((0, 0, cz))
    for i in range(SEG):
        j = (i + 1) % SEG
        bm.faces.new((cbot, base_ring[j], base_ring[i]))
    bm.normal_update()
    ob = finish(bm, "CPB_Crystal", smooth=False)
    return ob, rings[-1]   # return the top rim ring verts (as coords) for the crown

def top_rim_coords():
    """Recompute the top rim ring positions (crystal top, h=1) for the crown cap."""
    ths = angles()
    pr = profile_r(1.0)
    return [
        Vector((
            HALF_W * pr * superellipse_r(th, PLAN_EXP) * groove_scale(th) * math.cos(th),
            HALF_W * pr * superellipse_r(th, PLAN_EXP) * groove_scale(th) * math.sin(th),
            JAR_H,
        ))
        for th in ths
    ]

# ---------------------------------------------------------------- gem-cut lid crown
def build_crown():
    """Radiating triangular gem facets from the rim ring up to a small central table."""
    bm = bmesh.new()
    rim = top_rim_coords()
    rim_v = [bm.verts.new(c) for c in rim]
    crown_h = JAR_H * 0.055                    # how far the crown rises above the rim
    table_r = HALF_W * 0.30                    # central table radius
    table_z = JAR_H + crown_h
    # a ring at the table edge, with TABLE_FACETS points, faceted
    tf = TABLE_FACETS
    table_ring = []
    for i in range(tf):
        th = 2 * math.pi * i / tf
        r = table_r * superellipse_r(th, PLAN_EXP)
        table_ring.append(bm.verts.new((r * math.cos(th), r * math.sin(th), table_z)))
    # skirt: connect each rim vertex to the nearest table vertex, radial triangles
    for i, rv in enumerate(rim_v):
        th = 2 * math.pi * i / len(rim_v)
        ti = int(round(th / (2 * math.pi) * tf)) % tf
        ti2 = (ti + 1) % tf
        j = (i + 1) % len(rim_v)
        # a quad-ish band split into triangles between rim and table
        bm.faces.new((rv, rim_v[j], table_ring[ti2], table_ring[ti]))
    # flat table top (n-gon), slightly raised centre for a subtle crown
    ctr = bm.verts.new((0, 0, table_z + JAR_H * 0.004))
    for i in range(tf):
        j = (i + 1) % tf
        bm.faces.new((ctr, table_ring[i], table_ring[j]))
    bm.normal_update()
    return finish(bm, "CPB_Crown", smooth=False)

# ---------------------------------------------------------------- gold seam band
def build_seam():
    bm = bmesh.new()
    ths = [2 * math.pi * i / SEG for i in range(SEG)]
    h0, h1 = SEAM_H - 0.012, SEAM_H + 0.012
    lo, hi = [], []
    for th in ths:
        # polished, no grooves; sits just proud of the crystal
        r = HALF_W * 1.006 * superellipse_r(th, PLAN_EXP)
        lo.append(bm.verts.new((r * math.cos(th), r * math.sin(th), h0 * JAR_H)))
        hi.append(bm.verts.new((r * math.cos(th), r * math.sin(th), h1 * JAR_H)))
    for i in range(SEG):
        j = (i + 1) % SEG
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    bm.normal_update()
    return finish(bm, "CPB_SeamBand", smooth=True)

# ---------------------------------------------------------------- gold foot ring + starburst
def build_foot():
    bm = bmesh.new()
    ths = [2 * math.pi * i / SEG for i in range(SEG)]
    rr = HALF_W * 0.53
    top_z, bot_z = 0.02 * JAR_H, -0.004 * JAR_H
    top, bot = [], []
    for th in ths:
        r = rr * superellipse_r(th, PLAN_EXP)
        top.append(bm.verts.new((r * math.cos(th), r * math.sin(th), top_z)))
        bot.append(bm.verts.new((r * math.cos(th), r * math.sin(th), bot_z)))
    for i in range(SEG):
        j = (i + 1) % SEG
        bm.faces.new((bot[i], bot[j], top[j], top[i]))
    # radiating starburst underside: fan from a recessed centre to the bottom ring
    apex = bm.verts.new((0, 0, bot_z - 0.010 * JAR_H))
    for i in range(SEG):
        j = (i + 1) % SEG
        bm.faces.new((apex, bot[j], bot[i]))
    bm.normal_update()
    return finish(bm, "CPB_Foot", smooth=False)

# ---------------------------------------------------------------- ivory inner well + cream
def build_inner():
    bm = bmesh.new()
    ths = [2 * math.pi * i / SEG for i in range(SEG)]
    rr = HALF_W * 0.56
    h0, h1 = 0.14, 0.60
    lo, hi = [], []
    for th in ths:
        r = rr * superellipse_r(th, PLAN_EXP)
        lo.append(bm.verts.new((r * math.cos(th), r * math.sin(th), h0 * JAR_H)))
        hi.append(bm.verts.new((r * math.cos(th), r * math.sin(th), h1 * JAR_H)))
    for i in range(SEG):
        j = (i + 1) % SEG
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    # ivory floor
    fl = bm.verts.new((0, 0, h0 * JAR_H))
    for i in range(SEG):
        j = (i + 1) % SEG
        bm.faces.new((fl, lo[i], lo[j]))
    bm.normal_update()
    well = finish(bm, "CPB_InnerWell", smooth=True)

    # cream surface, a slightly domed disc near the top of the well
    bm2 = bmesh.new()
    cz = 0.55 * JAR_H
    ctr = bm2.verts.new((0, 0, cz + 0.01 * JAR_H))
    ring = []
    for th in ths:
        r = rr * 0.92 * superellipse_r(th, PLAN_EXP)
        ring.append(bm2.verts.new((r * math.cos(th), r * math.sin(th), cz)))
    for i in range(SEG):
        j = (i + 1) % SEG
        bm2.faces.new((ctr, ring[i], ring[j]))
    bm2.normal_update()
    cream = finish(bm2, "CPB_Cream", smooth=True)
    return well, cream

# ---------------------------------------------------------------- materials
def principled(name, **kw):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    def setv(sock, val):
        if sock in b.inputs:
            b.inputs[sock].default_value = val
    for k, v in kw.items():
        setv(k.replace("_", " ").title().replace("Ior", "IOR"), v)
    return m

def crystal_mat():
    m = principled("CPB_CRYSTAL",
                   base_color=(1.0, 0.955, 0.86, 1.0),
                   metallic=0.0, roughness=0.02, ior=1.62)
    b = m.node_tree.nodes["Principled BSDF"]
    for s in ("Transmission Weight", "Transmission"):
        if s in b.inputs: b.inputs[s].default_value = 1.0
    for s in ("Dispersion", "Transmission Dispersion"):
        if s in b.inputs: b.inputs[s].default_value = 0.035   # only exists on 4.2+
    return m

def gold_mat():
    return principled("CPB_GOLD",
                      base_color=(1.0, 0.82, 0.42, 1.0),
                      metallic=1.0, roughness=0.12)

def ivory_mat():
    return principled("CPB_IVORY",
                      base_color=(0.96, 0.92, 0.82, 1.0),
                      metallic=0.0, roughness=0.5)

def cream_mat():
    return principled("CPB_CREAM",
                      base_color=(0.98, 0.95, 0.88, 1.0),
                      metallic=0.0, roughness=0.35)

# ---------------------------------------------------------------- build
def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)

    body, _ = build_body()
    crown   = build_crown()
    seam    = build_seam()
    foot    = build_foot()
    well, cream = build_inner()

    body.data.materials.append(crystal_mat())
    crown.data.materials.append(crystal_mat())
    seam.data.materials.append(gold_mat())
    foot.data.materials.append(gold_mat())
    well.data.materials.append(ivory_mat())
    cream.data.materials.append(cream_mat())

    parts = [body, crown, seam, foot, well, cream]

    # normalise overall height to exactly JAR_H and sit the base on z=0
    zmin = min((o.matrix_world @ Vector(c)).z for o in parts for c in o.bound_box)
    zmax = max((o.matrix_world @ Vector(c)).z for o in parts for c in o.bound_box)
    factor = JAR_H / max(zmax - zmin, 1e-9)
    M = Matrix.Translation((0, 0, -zmin * factor)) @ Matrix.Diagonal((factor, factor, factor, 1.0))
    for o in parts:
        o.data.transform(M)

    if JOIN_ONE:
        bpy.ops.object.select_all(action='DESELECT')
        for o in parts:
            o.select_set(True)
        bpy.context.view_layer.objects.active = body
        bpy.ops.object.join()
        parts = [body]
        body.name = "CPB_LaCreme"

    # report bounds so you can sanity-check against the real jar (read real verts)
    allz = [v.co.z for o in parts for v in o.data.vertices]
    zmin, zmax = min(allz), max(allz)
    print(f"[cpb] built. height = {(zmax - zmin) * 1000:.1f} mm, "
          f"half-width = {HALF_W * 1000:.1f} mm, grooves = {BODY_GROOVES}, "
          f"plan-exp = {PLAN_EXP}, table-facets = {TABLE_FACETS}")

    if OUT_BLEND:
        bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
        print("[cpb] saved blend ->", OUT_BLEND)
    def export_obj(path):
        try:
            bpy.ops.wm.obj_export(filepath=path)
        except AttributeError:
            bpy.ops.export_scene.obj(filepath=path)
        print("[cpb] exported obj ->", path)

    if EXPORT_GLB:
        try:
            bpy.ops.export_scene.gltf(filepath=EXPORT_GLB, export_format='GLB')
            print("[cpb] exported glb ->", EXPORT_GLB)
        except Exception as e:
            alt = os.path.splitext(EXPORT_GLB)[0] + ".obj"
            print(f"[cpb] glb export failed ({e}); falling back to obj")
            export_obj(alt)
    if EXPORT_OBJ:
        export_obj(EXPORT_OBJ)

main()
