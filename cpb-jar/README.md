# CPB La Crème — procedural jar model

A parametric Blender build of the Clé de Peau Beauté "La Crème" 50ml jar, plus a
patched render studio. Companion to the original modelling brief
(`READMEMODELLINGBRIEF.md`).

This is a **first pass built from the five reference photos, not from calipers.**
It is structurally faithful — squircle (rounded-square) plan, deep vertical cut-crystal
facets, gem-cut radiating lid table, gold seam band + foot ring, ivory inner well —
and every dimension is a CLI parameter so you tune it against the real jar.

## Files

| File | What it is |
|---|---|
| `cpb_jar_builder.py` | Procedural jar builder. Writes `.blend` + `.obj`/`.glb`. |
| `cpb_studio.py` | The handoff studio, patched: GPU/CPU auto-detect, denoise fallback, per-slot materials. Drop-in for the original. |
| `cpb_preview.py` | Fast matte clay preview (few angles, low samples) for reading geometry. |

## Quick start

```bash
# 1. build the jar (defaults read off the photos)
blender -b --factory-startup --python cpb_jar_builder.py -- \
    --out jar.blend --export-glb jar.glb

# 2. hero render through the studio
blender -b --factory-startup --python cpb_studio.py -- \
    --mesh jar.glb --out hero.png --samples 512

# 3. or just read the geometry, fast
blender -b --factory-startup --python cpb_preview.py -- \
    --blend jar.blend --out prev
```

## Tuning to the real jar (this is the part that needs your calipers)

All defaults are guesses off the packshot. Measure and pass the truth:

```bash
blender -b --factory-startup --python cpb_jar_builder.py -- \
    --height 0.083 \        # overall height, metres — MEASURE
    --width-ratio 0.90 \    # width / height — MEASURE
    --body-grooves 20 \     # count the vertical V-cuts off the side photo
    --groove-depth 0.16 \   # how deep the cuts bite (fraction of radius)
    --plan-exp 3.4 \        # 2 = circle, ~4 = rounded square; match the top-down
    --table-facets 16 \     # radiating triangles on the lid crown
    --seam-h 0.455 \        # height fraction of the gold seam band
    --out jar.blend --export-glb jar.glb
```

The `PROFILE` list near the top of `cpb_jar_builder.py` is the front-elevation
silhouette (height fraction → radius fraction). Edit it directly to match the
side-profile photo screened as a background image.

## What's faithful vs. what still needs work

**In and correct**
- Superellipse plan (rounded square), not a cylinder — matches the top-down/open shots.
- Deep, sharp vertical V-cuts modelled into the cross-section (flat-shaded, real facets),
  not soft flutes — the brief's stated #1 failure mode.
- Domed gem-cut lid table with radiating triangles + central squircle table.
- Polished gold seam band at mid-height; gold foot ring with a radiating starburst base.
- Ivory inner well + a domed cream surface (visible when rendered open / cut).
- Four separate material slots (crystal / gold / ivory / cream), exact 83 mm height.

**Still approximations — tune against calipers + the full 19-photo set**
- Facet **count and depth** are eyeballed off five photos. Count them for real.
- The **profile curve** is interpolated from the packshot; refine from the side photo.
- The **CPB monogram** on the lid is a raised boss placeholder, not the real glyph —
  add it as a decal/logo, same for the **`clé de peau BEAUTÉ / LA CRÈME` lockup**
  (model it as a decal on the body, not geometry, per the brief).
- Facets are a symmetric zigzag; the real cut is closer to broad flat panels split by
  narrow V-notches. Adjustable, but not yet parameterised as panel-vs-notch width.

## Studio patch notes (vs. the original `cpb_studio.py`)

1. **Device auto-detect** — original hard-wired Apple METAL and disabled all other
   devices, which renders on nothing on a Linux/NVIDIA box. Now tries
   OPTIX > CUDA > METAL > HIP > ONEAPI, else CPU. Force with `--device CPU|CUDA|OPTIX|...`.
2. **Denoise fallback** — retries without denoising on builds lacking OpenImageDenoise
   instead of erroring.
3. **Per-slot materials** — applies the crystal shader to CRYSTAL/GLASS slots and gives
   GOLD/IVORY/CREAM their own shaders, so the multi-material jar renders right. A bare
   single-material mesh still gets all-crystal, exactly like before.

## Notes

- GLB export needs numpy in Blender's Python (present in standard desktop builds).
  If it's missing the builder falls back to writing `.obj` automatically.
- Refractive glass is heavy. Hero frames run in tens of minutes on a GPU; a full
  turntable is an overnight job (or an hour+ on CPU per frame). That's the material,
  not the scene.
