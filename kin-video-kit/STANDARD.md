# The talking-head standard

The default for every talking-head episode until it is changed on purpose.

## Pacing

- About 31 cuts a minute. The average shot is just under 2 seconds.
- The first cut lands inside 3 seconds.
- Each turn in the argument gets a quick burst of shots, then a face or a card holds for 3 to 6 seconds so the viewer can breathe.

## Mix of shots

Roughly a third face to camera, a third cards and diagrams, a fifth full-screen footage, and the rest split screens. Every spoken line gets a picture. Real footage and photos beat AI images.

## Voice and edit

- About 3.3 words a second.
- Pauses longer than a third of a second are tightened to about a fifth. No word is ever clipped.
- Held moments use real footage of the presenter's face, never a black frame.
- End on a one-second hold after the last word so the text can finish.
- Clips butt together with no gaps. Check every render for black frames.

## Text

- Every word appears on the frame it is spoken, never before.
- One move: each line rises 36 pixels and fades in over about a fifth of a second.
- Big headlines sit behind the presenter's head: Neue Haas Bold capitals, signal red, soft glow.
- Small lines in Neue Haas Medium. Labels in small Neue Haas capitals.
- The one emotional word is Instrument Serif Italic, never in capitals.
- Captions show the whole line faintly, light up the word being said, and hide when they would repeat the big text.

## Devices

- Card montage for an opening.
- Shelf of three cards for any list of three.
- Vertical list for "pick one".
- Centre-line diagram for a process.
- Warning sign for a risk.
- Real proof cards (press pages, product shots, archive footage) instead of AI images.

## Layout

Everything readable stays inside the Instagram and TikTok safe area: x 65 to 930 and y 260 to 1420 on a 1080 x 1920 frame. Every layout is measured, with equal gaps, and checked by a script before it ships. Each final also gets a "safe zone check" copy with the zones drawn on.

## Sound

- Each voice clip is levelled to match the others, cleaned and compressed.
- Music sits about 9 dB under the voice.
- Sound effects follow the picture: a whoosh on each cut, a hit when a headline lands, a soft tick for small lines, a few special sounds on the big turns. Nothing lands within 0.16 s of another effect.
- Final mix at -14 LUFS, true peak under -1 dB.

## Delivery

Every version is an editable DaVinci Resolve timeline with each layer on its own track: face, footage, text behind, cut-out, text in front, captions, dialogue, music, effects. The grade is done in Resolve and copied to every clip. The final is rendered out of Resolve in H.265 with the hvc1 tag. Preview renders are previews only.
