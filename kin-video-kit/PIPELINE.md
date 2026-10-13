# Production pipeline

The stages for a green-screen talking-head episode, in order. Claude writes and runs the code for each stage. You ask for the stage, check the result, and say go. PROMPTS.md uses the same stage numbers.

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
| 1 | Reference | Break down a reference video: cuts, shot length, text moves, sound hits. | A written plan for what we copy from it. |
| 2 | Story | The one belief, the turn, who it is for, in five lines. | You can say the repeatable line out loud. |
| 3 | Script | The talking-head framework, 150 to 200 words, curiosity-gap pass. | Nothing sounds written instead of said. |
| 4 | Offline cut | The editor cuts the A-roll in Resolve and tightens pauses. | No word clipped, no gaps, no black frames. |
| 5 | Beat map | Every line mapped to a picture, text and sound effect. Marks which A-roll shots stay on screen. | Pacing meets the standard without moving A-roll after the lock. |
| 6 | Lock the cut | The editor exports the locked cut from Resolve (.drt). | Nothing in the A-roll changes after this, or swaps must be paid for again. |
| 7 | Prep inputs | One clip per on-screen A-roll shot, framed like the cut, at least about 3.3 s long. | Every A-roll shot the beat map keeps on screen is covered. |
| 8 | Pilot swap | Kling video edit on Higgsfield replaces the green screen on one shot. | Face unchanged, lip sync 0 to 1 frame off, look approved. |
| 9 | Batch swap | The rest of the on-screen shots, one style reference per camera angle. | Each clip passes the same sync check. |
| 10 | Rebuild the plate | Swapped clips spliced back into the cut, frame for frame. | Sync measured from the camera audio, not the mouth. |
| 11 | Person cut-out | A steady matte (RVM) so text can sit behind the head. | No flicker frame to frame. |
| 12 | Text and inserts | Headlines, captions and B-roll inserts from the beat map. | Safe zone audit: 0 text outside the box. |
| 13 | Sound | Effects on the picture, music under the voice, -14 LUFS. | Loudness and true peak measured on the render. |
| 14 | Version | Render vNN and build it as a layered Resolve timeline, one track per layer. Review, notes, repeat. | Opens in Resolve with nothing offline. Every note marked done or not done. |
| 15 | Final | Grade in Resolve and copy it to every clip, render H.265 hvc1, plus the safe zone check copy. | Saved in the episode's Final folder. |

## The lock

After stage 6, notes can change anything above the plate: text, inserts, captions, sound and grade. A note that moves, adds or removes an A-roll cut reopens the lock, and every shot it touches is swapped and paid for again. Removing an insert counts too, because it shows A-roll that was never swapped.

## Rules that cost us versions

- Only the background is generated. The presenter's face is never changed.
- Swap only the A-roll the viewer will see. Shots fully covered by a card or full-frame footage stay green.
- Kling copies the framing of the style reference, so use one reference per camera angle (close, wide, side).
- Never write "zoom out" in a Higgsfield prompt. It triggers a preset and the job will not submit.
- Use RVM for the person cut-out, not Apple Vision. Vision flickers frame to frame.
- Check frame rates before rebuilding a cut. Cameras at 24 fps on a 23.976 timeline drift almost a second out of sync by the end of a long take.
- Never chop a word. Cut out at the first quiet frame after a word, in at the last quiet frame before one.
- Higgsfield for all image and video generation. ElevenLabs for voice, music and sound effects only.
