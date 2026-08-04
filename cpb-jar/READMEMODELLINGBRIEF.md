# CPB La Crème — Blender modelling brief

Model the Clé de Peau Beauté La Crème 50ml jar as an accurate 3D asset. Once it exists we can
render it at any angle, in any environment, with physically correct refraction and real caustics,
and it never drifts. That is the thing no AI generation or 2D composite can give us.

**We have the physical product in the office. Measure it. Do not trust any dimension in this
document without checking it against the real jar with calipers.**

---

## What's in this folder

| | |
|---|---|
| `reference-photos/` | 19 photographs of the actual jar, 7008 x 4672. Lighting is flat and cool, ignore it, the form is what matters. Closed, open, top-down, three-quarter, side. |
| `reference-cropped/` | The five clearest angles, white-balance corrected and cropped. Use these for quick reference, the full-res originals for detail. |
| `official-packshots/` | Brand front elevation and open jar. Cleaner lighting, useful for the label and the gold. |
| `cpb_studio.py` | A finished Blender studio. See below. |

---

## The object

Heavy cut crystal cosmetic jar, warm champagne tint, with a polished gold seam band and foot ring.
Squat and dense. It should feel like it weighs something.

### Construction, read the photos carefully

- **Lid top** is a genuine gem-cut table. Radiating triangular facets, like the crown of a cut
  stone, with a small gold CPB monogram inset dead centre. This faceting is on the outside and it
  is sharp.
- **Lid sides and body** carry deep, sharp, V-shaped cuts chiselled into thick glass. Hard crisp
  edges, real depth. These are **not** soft flutes, not gentle ribbing. Think cut lead crystal or a
  gemstone pavilion.
- **The lid is low and integrated.** It reads as one continuous form with the body, not as a
  separate cap stacked on top. Getting this wrong is the most common error.
- **Thin polished gold seam band** just below mid-height, where lid meets body.
- **Base pinches** to a small polished gold foot ring, with a radiating starburst cut underneath.
- **Lockup** in gold serif on the body below the seam: `clé de peau BEAUTÉ` over `LA CRÈME`.
  Small embossed `CLÉ DE PEAU BEAUTÉ` on the lid rim.
- **Inside**, a separate ivory inner well holds the cream. Visible in the open shots.

### Proportions

Measured off the official front packshot, so treat as a starting point and verify against the real jar:

- Overall silhouette is close to square, **width ≈ 0.90 of height**
- Widest through the middle 60% of its height, and it holds that width evenly rather than bulging
- Lid crown narrows to about 0.68 of max width at the top
- Foot ring pinches to about 0.53 of max width

Nominal size 50ml. **Height and width in mm are unverified — measure the real jar.**

### How it should look when lit

High contrast. Individual cut wedges go near-black and deep bronze where they refract shadow,
directly beside bright champagne and near-white where they catch light. If your render reads as a
uniformly pale, milky, low-contrast pot, the cuts are too shallow or the lighting is too flat.

---

## The studio script

`cpb_studio.py` is a working headless Blender scene. It saves you the lighting and shader work.

```bash
# render the current stand-in
blender -b --factory-startup --python cpb_studio.py -- --out hero.png --samples 512

# drop your model in
blender -b --factory-startup --python cpb_studio.py -- --mesh /path/to/jar.obj --out hero.png --samples 512

# turntable, 96 frames over 90 degrees
blender -b --factory-startup --python cpb_studio.py -- --mesh jar.obj --frames 96 --rot 90 --out //turn/

# product on transparent, for compositing
blender -b --factory-startup --python cpb_studio.py -- --mesh jar.obj --alpha --out plate.png
```

It gives you:

- Cycles on GPU, with transmission bounces raised to 24 so the glass doesn't go black
- A crystal shader: IOR 1.62, dispersion on, noise-driven micro-roughness so it isn't unnaturally clean
- Real emissive softbox geometry either side, so reflections are rectangular with real edges,
  plus a hard fresnel key with shadow caustics enabled and a bounce card
- A real camera: 85mm, 36mm sensor, f/5.6, depth of field
- AgX view transform, so highlights roll off instead of clipping
- `--mesh` auto-scales any OBJ/FBX/GLB/STL to the right height and sits it on the floor

**Ignore the stand-in mesh.** It's a lathe I built from a profile before I understood the
construction, and it's wrong — no real facets, silhouette too smooth. It exists only to prove the
lighting works. Model from the photographs, not from it.

---

## Suggested approach

The jar is rotationally symmetric, which makes it far more tractable than it looks.

1. Build the profile curve from the side-profile photo, screen it as a background image
2. Lathe it for the base form
3. Add the V-cuts as a radial array of boolean cutters or a bevelled crease pattern, matched to the
   photos for count and depth
4. Lid table as a separate gem-cut crown, radiating triangles
5. Gold seam band and foot ring as separate material slots
6. Label as a decal on the body, not modelled geometry
7. Inner cream well as a separate object

Facet **count** matters. Count them off the top-down and side photos rather than guessing.

---

## Known render cost

Refractive glass is heavy. On an M3 with a 10-core GPU, 540x960 at 64 samples took **4m44s**. Plan
for hero frames in tens of minutes and a full turntable overnight, or move it to a machine with a
real GPU. That's normal for this kind of material, not a problem with the scene.

---

## What good looks like

Put your render next to `reference-photos/DSC08939.JPG` and `DSC08937.JPG`. If the silhouette,
facet count, facet depth and the position of the seam band all match, it's right. The lighting will
differ, and that's fine, that's ours to change.
