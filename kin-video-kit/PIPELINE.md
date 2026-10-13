# Production pipeline

The stages for a green-screen talking-head episode, in order. Claude writes and runs the code for each stage. You ask for the stage, check the result, and say go.

## Project folder

Make it in `~/Movies/<Episode>/`, never in iCloud (iCloud moves big files offline and breaks Resolve).

```
Ref/       references and their breakdowns
Looks/     style reference images, one per camera angle
kling/     input clips and swapped clips
Plate/     the rebuilt clean cut and the person cut-out
scripts/   the code Claude writes for this episode
sfx/       sound effects
Renders/   every version, numbered
```

## Stages

| # | Stage | What happens | Check before moving on |
|---|---|---|---|
| 1 | Lock the cut | The editor exports the locked cut from Resolve (.drt). | Nothing changes after this, or swaps must be paid for again. |
| 2 | Prep inputs | One clip per shot of the cut, framed like the cut, at least about 3.3 s long. | Every shot of the cut is covered. |
| 3 | Pilot swap | Kling video edit on Higgsfield replaces the green screen on one shot. | Face unchanged, lip sync 0 to 1 frame off, look approved. |
| 4 | Batch swap | The rest of the shots, one style reference per camera angle. | Each clip passes the same sync check. |
| 5 | Rebuild the plate | Swapped clips spliced back into the cut, frame for frame. | Sync measured from the camera audio, not the mouth. |
| 6 | Person cut-out | A steady matte (RVM) so text can sit behind the head. | No flicker frame to frame. |
| 7 | Text and inserts | Headlines, captions and B-roll inserts from the beat map. | Safe zone audit: 0 text outside the box. |
| 8 | Sound | Effects on the picture, music under the voice, -14 LUFS. | Loudness and peak measured on the render. |
| 9 | Version | Render vNN, review, notes, repeat. | Every note marked done or not done. |
| 10 | Layers to Resolve | Each layer rendered on its own track and built into a timeline. | Opens in Resolve, nothing offline. |
| 11 | Final | Grade in Resolve, render H.265 hvc1, plus the safe zone check copy. | Saved in the episode's Final folder. |

## Rules that cost us versions

- Only the background is generated. The presenter's face is never changed.
- Kling copies the framing of the style reference, so use one reference per camera angle (close, wide, side).
- Never write "zoom out" in a Higgsfield prompt. It triggers a preset and the job will not submit.
- Use RVM for the person cut-out, not Apple Vision. Vision flickers frame to frame.
- Check frame rates before rebuilding a cut. Cameras at 24 fps on a 23.976 timeline drift almost a second out of sync by the end of a long take.
- Never chop a word. Cut out at the first quiet frame after a word, in at the last quiet frame before one.
- Higgsfield for all image and video generation. ElevenLabs for voice, music and sound effects only.
