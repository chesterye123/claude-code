# Kin Video Workflow Kit

The structure and framework for making a talking-head episode with Claude Code. The step-by-step guide is the web page that came with this kit. This folder holds the reference files that go with it.

## What is in here

**PROMPTS.md**
The prompt for each stage, ready to copy.

**STANDARD.md**
The house standard for every talking-head episode: pacing, text, sound, layout and delivery, in numbers.

**PIPELINE.md**
The production stages in order, what each one does, and what to ask Claude for at each one.

**Editing/EDITING.md**
The editing playbook: selects, tightening, pace, zooms, sound, hand-off to motion and grade, review rounds.

**Editing/MOTION.md**
The motion design system: type, every device, timings, and the checks before anything ships.

**After Effects/**
Eight tested scripts that build an episode in After Effects from words.json and inserts.json: the text-behind-the-head comp, captions, headlines, kinetic headline, depth words, inserts, safe zone audit and render. Read its README first.

**DaVinci Resolve/**
Resolve scripts (build the layered timeline, copy a grade) and Fusion versions of the motion devices. Read its README first.

**Example data/**
A working words.json and inserts.json, plus `make_test_media.sh`, which makes fake media so you can try every script before a real episode.

**Claude skills**
Copy each folder into `~/.claude/skills/` so Claude Code can use them.

- `reverse-shot` breaks a reference video down into shots, pace, text moves and sound, plus a plan to copy it.
- `curiosity-gap` checks a script so every line opens or pays off a question.

## Before you start

1. You need Claude Code, Python 3.11 with `uv`, ffmpeg, After Effects, and DaVinci Resolve Studio with external scripting set to Local.
2. Connect the Higgsfield, ElevenLabs and Firecrawl MCPs in Claude Code.
3. Fonts: Neue Haas Grotesk Display through Adobe Fonts. Instrument Serif and IBM Plex Mono are free on Google Fonts.
4. One person or one Claude session works in a project folder at a time.
