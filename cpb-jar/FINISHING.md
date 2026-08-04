# CPB La Crème — finishing the model in Blender

The procedural builder gets you a measured-accurate, gem-cut base mesh
(`cpb_jar_builder.py` → `jar.blend`/`jar.glb`). This guide covers the last mile
that's faster and more precise done by hand in Blender 5.2 than in procedural code:
the **branding decals** and any **final facet polish**.

Everything below assumes you've built and opened the mesh:

```bash
blender --python cpb_jar_builder.py -- --out jar.blend
blender jar.blend
```

---

## 1. Branding decals (needs the real artwork)

The monogram and lockup are **not modelled** — they should be decals, per the brief.
I deliberately didn't fabricate Clé de Peau's logo; drop in the real vector art.

You need three pieces of artwork (ask brand/packaging for vectors, or trace at high res):

| Decal | Where | Source photo |
|---|---|---|
| CPB butterfly monogram | centre of the lid table (gold, slightly inset) | top-down shots |
| `clé de peau BEAUTÉ` / `LA CRÈME` lockup | front of the body, below the seam | front packshot |
| `CLÉ DE PEAU BEAUTÉ` (small caps) | the gold shoulder rim (visible only when open) | open-jar shots |

### Fastest route — a gold emission/metal decal via a second UV + image texture

1. Import the art as SVG (`File ▸ Import ▸ SVG`) or use a transparent PNG.
2. On the **CPB_Crystal** object (table) and **CPB_LaCreme** body, add a second UV map
   and project just the decal area flat (select the table faces → `U ▸ Project from View`
   looking straight down; select the front body faces → project from the front).
3. New material slot, assign it to those faces, or use a **Decal** setup:
   - `Image Texture` (the logo, Alpha) → `Mix Shader` factor between the crystal/gold
     shader and a **gold** Principled (Metallic 1.0, Base Color ~(1.0,0.82,0.42),
     Roughness 0.12). For the table monogram, give the gold a touch of Emission so it
     catches light like the real foil.
4. Scale/position with the UV editor against the reference photo.

### Cleaner route — real inset geometry (if you want relief, not just a texture)

1. Make a plane with the logo (SVG import → extrude slightly).
2. Shrinkwrap it to the table surface, then use it as a **Boolean** (Difference for an
   engrave, or keep it as a separate gold object for a raised foil).
3. Keep it a separate object with the gold material so it renders as inlaid metal.

The studio (`cpb_studio.py`) already routes any slot named `*GOLD*` to the gold shader,
so name decal materials `CPB_GOLD_MONOGRAM` etc. and they'll light correctly.

---

## 2. Final facet polish (optional, against the full photo set)

The base facets are parametric and close. If you want them exact:

- **Facet count** — set `--facets N` to whatever you count on the real jar
  (currently 18). Body and lid share the count; the seam split is automatic.
- **Kite shape** — `depth_at(h)` in the builder controls how the facets pinch
  (deep at base/seam/crown, shallow mid-half). Tweak the `0.30 + 1.5*…` constants
  for more or less lozenge.
- **Crown** — `--table-frac` (table size) and `--crown-rise` (how proud the table
  sits). The two-tier rose cut lives in `build_crystal()`'s crown block if you want
  to add a third facet tier.
- **Profile** — the `PROFILE` list is the silhouette (height→radius). Screen a
  straight-on side photo as a background image (`View ▸ Background Images`) and nudge
  the control points until the outline matches.

For a truly exact gem cut, the hand method beats procedure: import the base, screen
the top-down photo over the lid, and cut the star/kite facets with a **radial array
of a single knife-cut** (Knife → Bisect, or a boolean cutter arrayed with an Empty),
then `Shade Flat`. The base gives you correct proportions to cut against.

---

## 3. Render

```bash
# your GPU build, full quality
blender -b --python cpb_studio.py -- --mesh jar.glb --out hero.png --samples 512
# turntable
blender -b --python cpb_studio.py -- --mesh jar.glb --frames 96 --rot 90 --out //turn/
# transparent plate for compositing
blender -b --python cpb_studio.py -- --mesh jar.glb --alpha --out plate.png
```

The studio auto-detects your GPU (OPTIX/CUDA/METAL/…), applies the crystal shader to
`*CRYSTAL*` slots and gold/ivory/cream to theirs, and rolls highlights off with AgX.
On Blender 5.2 you also get the dispersion the base shader sets (`--samples` higher =
cleaner glass).
