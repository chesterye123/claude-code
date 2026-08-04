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

## Tuning knobs

Measured dimensions are baked in as defaults (**70 mm tall, 63 mm wide, ratio
0.90**, seam at dead centre). The rest is eyeballed off the photos — override any of it:

```bash
blender -b --factory-startup --python cpb_jar_builder.py -- \
    --height 0.070 \        # overall height, metres (measured)
    --width-ratio 0.90 \    # width / height (measured 63/70)
    --facets 18 \           # count of vertical facets around
    --panel-frac 0.85 \     # flat-panel width vs. groove within each facet
    --groove-depth 0.12 \   # base V-groove depth (deepens toward crown/base)
    --plan-exp 3.6 \        # 2 = circle, ~4 = rounded square; match the top-down
    --table-frac 0.38 \     # flat lid table radius (fraction of half-width)
    --crown-rise 0.06 \     # how far the crown table sits above the rim
    --seam-h 0.50 \         # height fraction of the gold seam band
    --out jar.blend --export-glb jar.glb
```

The `PROFILE` list near the top of `cpb_jar_builder.py` is the front-elevation
silhouette (height fraction → radius fraction). Edit it directly to match the
side-profile photo screened as a background image.

## What's faithful vs. what still needs work

**In and correct**
- Measured proportions: 70 × 63 mm, ratio 0.90, seam (widest) at dead centre.
- Superellipse plan (rounded square), not a cylinder — matches the top-down.
- Onion/cushion silhouette: widest at the seam, lid and body both taper away.
- Broad flat crystal facets split by narrow V-grooves that deepen toward the crown
  and base, so facets read as a gem cut rather than flutes.
- Cushion crown: a sawtooth of pointed arches (the lid-facet tips) rising to a flat
  central table — the signature CPB top.
- Polished gold seam band at dead centre; rounded crystal base + optional gold foot.
- Ivory inner well + a domed cream surface (visible when rendered open / cut).
- Four separate material slots (crystal / gold / ivory / cream), exact height.

**Still approximations — refine against the full photo set**
- Facet **count** is inferred (18); confirm off a clean top-down/side.
- The **profile curve** is interpolated from photos; refine from a straight side.
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
