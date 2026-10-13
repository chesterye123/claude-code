---
name: reverse-shot
description: Reverse-engineer any video into a structured cinematography breakdown (a "reverse prompt"). Extracts MEASURED editing pace + motion + keyframes with ffmpeg, pulls the timestamped transcript, then analyzes cinematography, camera movement, angles, lighting, lens, location, shooting method, and ad structure. Outputs a fixed SHOT BREAKDOWN schema plus a generator-ready recreate prompt for Luma/Kling/Veo/Higgsfield and a shot-by-shot replication plan. Use when the user says "reverse prompt this video", "break down how this was shot", "reverse-engineer this clip", or gives a reference video to recreate. Use on any YouTube, Instagram, TikTok or Vimeo link the user shares.
---

# reverse-shot

Turn a reference video into a shootable/generatable breakdown. The rule: **measure what
can be measured, infer the rest, and label inference as inference.** Never launder a guess
about lens or camera movement into a stated fact.

## Reliability ladder (tell the truth in the output)
- MEASURED (trust it): editing pace / cuts / ASL, duration, fps, resolution, motion presence.
- OBSERVED (high confidence from frames): location, shot sizes, angles, lighting, color grade, composition.
- INFERRED (guesses, must carry a confidence 0-100): camera movement type, lens/focal length, rig, camera format.

Camera movement and lens are the least recoverable fields (even top video models score
~15-20% on movement). Always attach confidence; never overclaim.

## Inputs
- A local video path, OR a URL (needs `yt-dlp`, installed).
- Requires `ffmpeg` + `ffprobe` (installed).
- Transcript: platform captions via `yt-dlp` (free), or any local speech-to-text tool you have.

## Why this runs (read before you start)
This is not film-appreciation. The output is a build order. Every reference you drop
is headed for a real build: an episode, a client project, or a generated ad. So the breakdown has to end with
something a generator can execute, not a paragraph about mood. If you cannot turn a
section into an instruction, cut it.

## Procedure

1. **Resolve input.** Get the local path or URL from the user. Pick an output dir, default
   `/tmp/reverse-shot-<shortname>`.

2. **Extract evidence.** Run the bundled script, `scripts/extract.sh` in this skill's folder
   (`~/.claude/skills/reverse-shot/` when installed for one user, `.claude/skills/reverse-shot/`
   when it lives in a project):
   ```
   <skill folder>/scripts/extract.sh <video-or-url> <outdir> [fps] [scene_threshold]
   ```
   Defaults: `fps=1`, `scene_threshold=0.3`. For a fast-cut TikTok/reel, drop threshold to
   `0.2`; for slow cinematic footage raise to `0.4`. For clips over ~90s, use `fps=0.5` to
   cap frame count.

3. **Read the measured layer first** (cheap, high value):
   - `pace.json` -> duration, cuts, Average Shot Length, cuts/min, pace label.
   - `metadata.json` -> resolution, fps, codec. **Scan the `tags` blocks for `focal_length`,
     `lens`, `model`, `make`**, if present, lens/camera are FACT not guess (say so). Most
     social re-uploads strip these; note when absent.
   - `cuts.csv` -> exact cut timestamps = the edit rhythm. Note if cuts accelerate, sit on
     beats, or are even.

4. **Read the frames** (the eyes). Prefer `cutframes/` (one still per shot = a storyboard)
   over the dense `frames/`. **Cap it:** Read at most ~20-25 frames. If there are more,
   sample evenly across the timeline and say how many you skipped, do not silently truncate.
   Estimate/confirm token cost before reading a large batch.

5. **Motion pass (do this, movement is the field most often faked).**
   Check the extractor's `motion` line before you decide:
   - **`motion.trf written`** -> a real per-frame motion signal. Use it. (Some ffmpeg builds include libvidstab.)
   - **`skipped (libvidstab not in this ffmpeg)`** -> this is the normal case on a
     Mac. There is no local motion signal. Send the video to Higgsfield
     `video_analysis_create` (temporal, sees motion natively) and poll
     `video_analysis_status`.

   If neither signal was obtained, every movement call is a guess: cap its confidence at 40
   and state in the output that no motion signal was run. Never present an unverified
   movement call at high confidence, this is the easiest place to launder a guess into a
   fact, and a wrong movement call sends a whole generation job the wrong way.

6. **Transcript (do this, don't skip it).** VO and on-screen copy carry the ad's argument,
   and you cannot write a replication plan without them. Pull captions with `yt-dlp
   --write-auto-subs --skip-download`, or transcribe the audio locally. If no
   transcript can be produced, say so in one line and continue, a silent or music-only
   reference is legitimate, a *silently dropped* transcript is not.

   Then scan the transcript for deictic cues ("look at this", "watch what happens",
   "here's the thing") and re-run the frame pass with `--timestamps T1,T2,…` pointed at the
   **already-downloaded local file** so those beats get a frame. Presenters flag their own
   money shots; scene-change detection misses them because pointing at something is a low
   visual delta.

7. **Emit the breakdown** in the exact schema below. Then the recreate prompt, then the
   replication plan.

## Output schema (fixed, always this shape)

```
SHOT BREAKDOWN, <title>

MEASURED
- Duration / fps / resolution:
- Cuts / cuts-per-min / Average Shot Length:
- Editing pace: <rapid | moderate | slow> + rhythm note (accelerating? on-beat? even?)
- Motion signal: <locked | subtle handheld | active handheld | gimbal-smooth | whip/fast> [source: trf / higgsfield / inferred]

OBSERVED
- Location & setting:
- Shot sizes used:
- Angles: <eye/high/low/dutch/overhead>, height, subject relationship
- Lighting: key direction, hard vs soft, contrast ratio, color temp, motivation, time of day
- Color grade: palette, contrast, saturation, emulation vibe
- Composition: framing, symmetry, negative space, depth layers

INFERRED (each line ends with confidence 0-100)
- Camera movement per beat: ...  (conf: NN)
- Lens / focal length: <wide 14-24 / normal 35-50 / tele 85+ / anamorphic?> + why  (conf: NN)
- Rig: <tripod / handheld / gimbal / drone / slider>  (conf: NN)
- Camera format: <phone / mirrorless / cinema>  (conf: NN)

AD STRUCTURE (what the video is doing, beat by beat)
- Hook (0:00-0:0X): what earns the first two seconds, visual, claim, or pattern break
- Beats: each turn in the argument with its timestamp and its job
- Product reveal: when, how big, how the product is lit and held
- Proof: demo, before/after, stat, testimonial, or none
- Close / CTA: what it asks for and how hard
- On-screen copy: every text card, verbatim, with timestamp
- VO / dialogue spine: the argument in 3 lines
- Why it works: the one mechanism worth stealing. Not a list. One.

REPLICATION PLAN (how we rebuild this without a shoot)
- Shot-by-shot table: # | timestamp | duration | what happens | generator | prompt seed
- Generator routing per shot (check Higgsfield models_explore for the current best model).
- Assets to lock before generating: product sheet, character sheet, set, style ref
- What will NOT survive AI generation, and the honest workaround for each
- Estimated shot count and rough credit cost
```

## Save the breakdown (do not skip)
The breakdown is an asset, not chat output. When it is written:

1. **Ask the user where it goes.** Never guess. Default: the project's `Ref/` folder.
2. **Version the filename** `reverse-shot-<slug>-v01.md`, bump to v02 and up. Never overwrite.
3. **Open the file and its containing folder** once written.

## Chaining
- Feeds Higgsfield `generate_video` via the RECREATE PROMPT.

## Guardrails
- Style/technique only. Do not attempt to identify or recreate a real, private individual.
- Confidence numbers are mandatory on every INFERRED line. No naked guesses.
- If frames were sampled/capped, state the count dropped. No silent truncation.
- Do not describe the reference as something Epitome shot, and do not call the replication
  a shoot. It is VFX, CGI and code.
- If a reference is a competitor's ad being broken down for a client pitch, keep the
  breakdown internal. It is a working document, not a deliverable.
