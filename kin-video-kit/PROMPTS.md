# Prompt sheet

Copy a prompt, fill in the parts in angle brackets, and paste it into Claude Code. One prompt per stage. Keep the version number in every message so Claude always knows which cut you mean.

## 1. Reference

```
Reverse-shot this reference: <link or file path>.
I want to borrow its <pace / text movement / B-roll style / sound>, nothing else.
Measure the cuts and the average shot length, list every text move and sound hit with its timestamp,
and end with a plan for how we copy it in <episode name>.
Save the breakdown in <project folder>/Ref/ as reverse-shot-<short name>-v01.md.
```

## 2. Story

```
Here is the raw idea for <episode name>: <brain dump, voice note transcript or rough notes>.
Find the one belief this episode argues, the moment it turns, and who it is for.
Give me the story in five lines: the situation, the problem, the turn, what changed,
and the one line people will repeat to a friend. Do not write the script yet.
```

## 3. Script

```
Write the script for this story with our talking-head framework:
Hook, Promise, Value 1, Open loop, Value 2, Open loop, Value 3, Call to action.
45 to 60 seconds spoken, 170 to 230 words.
Keep these lines word for word: <lines>.
Then run the curiosity-gap pass so every line opens, holds or pays off a question.
Flag any line that sounds written instead of said out loud.
```

## 4. Structure (beat map)

```
Here is the locked script and the editor's cut: <path to the .drt or the offline mp4>.
Build a beat map as a table: timecode, spoken line, what is on screen (face, card,
full-frame B-roll or insert), the text on frame, and the sound effect.
Follow the Epitome talking-head standard: first cut inside 3 seconds, average shot about 2 seconds,
every beat gets a real picture, text lands on the spoken word, everything inside the
safe zone (x 65 to 930, y 260 to 1420 on 1080 x 1920).
Then list the B-roll we need that we do not have yet.
```

## 5. Background swap (green screen)

Prompt to Claude:

```
Replace the green screen on every A-roll shot of the locked cut with Kling video edit on Higgsfield
(model kling_video_edit). Style reference: <image path>. Use a separate reference image per camera angle.
Pilot one shot first. Check lip sync against the input (lag and correlation), show me a frame,
and wait for my go before you run the rest.
```

The prompt Kling itself gets (Claude sends this, per shot):

```
This is a <CLOSE-UP / MEDIUM / WIDE>. Keep the exact same framing, crop and size of the presenter in frame.
Replace only the green screen behind them with the studio from the reference image: <describe it, e.g.
dark teal-grey seamless backdrop with a soft cool teal circular spotlight halo behind the head>.
Keep the presenter completely unchanged: same face, expression, mouth and lip movement, hands, microphone,
clothes and timing. Natural neutral skin, no green tint or green edges.
```

Never write "zoom out" in a Higgsfield prompt. It triggers a preset and the job will not submit.

## 5b. Text and motion (After Effects or Fusion)

Make the data file:

```
Here is the locked cut: <path to the mp4>. Make words.json for it in the kit's format
(see Example data/words.json): one entry per line of text, every word with the second it is spoken,
from a word-level transcript. Use the beat map for which lines are captions, headlines, kinetic,
depth or feel, and which sit in front of or behind the head. Spell names from the brief, not the transcript.
Then make inserts.json from the beat map's B-roll list.
```

Build it:

```
Point project.json at <plate>, <matte>, words.json and inserts.json. Run the After Effects scripts
01 to 07 in order with run_jsx.sh, read each log, and fix anything the safe zone audit flags.
Render a still at <timecodes> so I can check the look before the full render.
```

For Fusion, the same prompt with "the DaVinci Resolve Fusion scripts" instead.

Tune it:

```
The kinetic headline at <timecode> feels <too bouncy / too slow / too stiff>.
Change SPRING in 04_kinetic_headline.jsx (DAMP, FREQ, LIFT, TILT), re-run 04, and show me frames
at <t>, <t + 0.2 s> and <t + 0.5 s>.
```

## 6. Notes and changes

```
v<NN> notes:
0:04  <what is wrong>  ->  <what I want>.  Ref: <link or file>
0:12  <what is wrong>  ->  <what I want>
0:31  <what is wrong>  ->  <what I want>
Fix all of these and render v<NN+1>. Update the Resolve timeline.
Then list every note as done or not done, with the reason for anything not done.
```

When a word like "dynamic", "3D" or "clean" could mean two things, show it:

```
This is what I mean by <word>: <ref link or file>. Copy <the exact thing> from it.
Do not copy <the thing you do not want>.
```

## 7. Delivery

```
Lock v<NN>. Build the layers for Resolve (talking head, text behind, B-roll, text in front,
dialogue, sound effects), build the timeline, render the safe zone check copy,
and give me the final in H.265 with the hvc1 tag at -14 LUFS.
```
