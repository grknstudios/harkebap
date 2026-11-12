# Per-game promo videos: handoff for the Mac session

This toolkit was built in a cloud session that produced `promo/PopGames_Promo_60s.mp4`
(the 4-game, 60-second, 16:9 promo). The next job needs the latest game builds, which
exist only in `~/flutterprojeler` on the Mac, so it continues in a local Claude Code session.

## The job

Make **one promo video per game**, each in **two formats**:

| Format | Size | Use |
|---|---|---|
| 9:16 | 1080×1920 | Reels / TikTok / Shorts |
| 16:9 | 1920×1080 | YouTube / web |

### Step 1: ask the owner before producing anything
1. Scan `~/flutterprojeler` and list every game project. Expected so far: **Feather Pop,
   Park Pop, Nut Pop, Terminal Tangle, Tileva Pop**. Show anything else you find too.
2. Send the list to the owner and **wait for approval** of which games to make videos for.
3. Also confirm the length per video (suggest ~30 s) before you start.

### Step 2: record real gameplay (latest code from `~/flutterprojeler`)
- Do not modify or commit to the game projects.
- Run each approved game on an iOS Simulator (M1 Mac): `flutter run -d <sim-id>`.
- Record with `xcrun simctl io booted recordVideo --codec=h264 <game>_raw.mp4`.
- To play it: prefer an automated `integration_test` that taps through a level, using the
  game's own solver or hint system if it has one (the store copy says levels are solver-checked).
  If that isn't practical, record while the owner plays, after asking them.
- Capture ~20–40 s per game: a level being solved, the win screen, and one special feature.

### Step 3: build the videos with the engine in `engine/`
`engine/main.js` is a canvas motion-graphics engine rendered frame-by-frame with Playwright:
`node tools/render.js engine <startFrame> <endFrame> out.mp4` (30 fps). Reuse its pieces:
- **Intro:** the GRKN Studios logo pop-in (`IMG.logo`, see `introScene`).
- **Game title card:** icon pop + bouncing title + subtitle pill (`gameScene`).
- **Phone mockup:** `drawPhone(...)` with the screen callback. Replace the screenshot
  slideshow (`parkShots`) with frames of the recorded gameplay video. Easiest: extract frames
  (`ffmpeg -i raw.mp4 -vf fps=30 frames/%05d.jpg`) and draw frame N at time t.
- **Caption chips:** `chip(...)`.
- **End card:** store badge + "Search … on the App Store" (Tileva Pop is on **Google Play**, so
  use a Google Play badge there unless the owner says it is on the App Store too).
- **16:9 layout:** text on the left, phone on the right (as in the current 60 s video).
- **9:16 layout:** title and icon at the top, the phone (or full-bleed gameplay) in the middle,
  captions and the store badge at the bottom.

Change `W`/`H` at the top of `main.js` (and the viewport in `tools/render.js`) for 9:16.

### Step 4: voiceover and audio
- ElevenLabs voice **Killian – Clear, Warm, Upbeat & Friendly**
  (`voice_id Whez8hBysHW6IVGRgjGA`), model `eleven_v4`, English.
- Write one short script per game (~20–25 s) from its App Store description. Verified facts:
  - **Feather Pop:** "Relaxing colour sorting game". Group birds by kind; four of a kind make a
    flock that sings, sparkles and flies away. No timers, no lives; every level is solvable.
  - **Park Pop:** "Relaxing car parking puzzle". Park cars by colour until every lane is full;
    mystery "?" cars; Park Escape bonus every 10 levels.
  - **Nut Pop:** "Relaxing colour screw game". Lift nuts and stack them by colour; frozen nuts,
    chained bolts, bombs; Plate Drop bonus every 10 levels.
  - **Terminal Tangle:** "Bus sorting & parking puzzles". Tap vehicles with a clear path; passengers
    board vehicles of the same colour; ambulance, fire, police and army vehicles.
  - **Tileva Pop:** read the project/store listing first; nothing is verified yet.
- `voiceover/` holds the 6 lines used in the 4-game video (reusable for intros/outros).
- `tools/audio.py <events.json> <vo_dir> <out.wav>` synthesises the music bed + SFX, ducks under
  the VO and mixes. Edit its `DUR`, `SCENE_STARTS` and `VO` timing list for each video.
  Get `events.json` from `EVENTS=events.json node tools/preview.js engine <outdir> 0`.
- Mux: `ffmpeg -i video.mp4 -i mix.wav -c:v copy -c:a aac -b:a 192k -af loudnorm=I=-16:TP=-1.5 -shortest out.mp4`

### Requirements on the Mac
`node` + `npm i playwright && npx playwright install chromium`, `python3` with `numpy scipy pillow`,
`ffmpeg` (`brew install ffmpeg`), Flutter + Xcode simulators.

### Deliverables
`promo/<Game>_9x16.mp4` and `promo/<Game>_16x9.mp4` for each approved game, plus a short
English share text per game (see `promo/share_text.md` for the house style).

## Store links
- Feather Pop: https://apps.apple.com/us/app/feather-pop-bird-sort-puzzle/id6819266125
- Park Pop: https://apps.apple.com/us/app/park-pop-car-colour-sort/id6817668148
- Nut Pop: https://apps.apple.com/us/app/nut-pop-bolts-colors/id6818778610
- Terminal Tangle: https://apps.apple.com/us/app/terminal-tangle/id6819357974
- Tileva Pop: Google Play (link to be confirmed)
