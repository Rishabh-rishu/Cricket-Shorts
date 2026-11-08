# CRICKET RAAZ — OFFICIAL BROADCAST & PRODUCTION STYLE GUIDE (V3)

## Permanent Visual & Production Standard Baseline
**Version:** 3.0  
**Effective Date:** November 8, 2026  
**Status:** MANDATORY PRODUCTION STANDARD (Default for all future videos, manual runs, and GitHub Actions scheduled runs)

---

## 1. Executive Summary & Design Philosophy
Cricket Raaz produces premium, cinematic sports documentary YouTube Shorts. Every video must look like a high-budget international television sports broadcast (ESPN, Star Sports, Sky Sports) blended with cinematic sports documentary storytelling.

**Core Directives:**
1. **1080x1920 Full-Canvas Utilization**: Zero awkward empty areas, zero blank statistic pods, zero unpadded margins.
2. **Dynamic Broadcast Color Palettes**: Every video automatically receives a fresh, cohesive, premium color theme tailored to its topic, format, team, or player.
3. **Format-Specific Authentic Jerseys**: 100% historical accuracy. Never show Test whites in an ODI video, and never show colored kits in a Test video.
4. **Zero Photographic Reuse**: Strict 64-bit perceptual difference hashing (`dhash`). Every scene presents a fresh, high-resolution visual. No repeated photographs within a video or across future automation runs.
5. **Zero-Tofu Vector Typography**: All emojis (`★`, `👑`, `⚡`) are strictly rendered as font-independent PIL vector polygons, guaranteeing zero missing glyph tofu boxes (`[X]`).
6. **Zero Topic Repetition**: Multi-layer semantic deduplication rejecting rephrased or synonymous versions of previously published facts.

---

## 2. The 5-Scene Broadcast Architecture (1080x1920 @ 30 FPS)

```
+-----------------------------------------------------------------------+
| SCENE 1: OPENING HOOK & RECORD ALERT (~6.0s - 7.5s)                   |
| - Atmosphere: Night stadium floodlights beams (No player background)   |
| - Header: Red LIVE indicator + "CRICKET RAAZ • WORLD RECORDS"          |
| - Alert Capsule: Vector gold stars + "[FORMAT] RECORD ALERT"           |
| - Typography: Massive bold headline + Hinglish subtitle                |
| - Glass Pod: Match Venue, Historic Date, Opponent, Core Feat           |
| - Footer: "CRICKET RAAZ EXCLUSIVE • DAILY SHORTS ARCHIVE" ticker       |
+-----------------------------------------------------------------------+
| SCENE 2: PLAYER HERO SPORTS POSTER (~9.0s - 11.0s)                    |
| - Authentic Player Action/Portrait in FORMAT-ACCURATE JERSEY          |
| - Background: Massive vertical stencil typography (First & Last Name)  |
| - Top Capsule: Official Player Role / Tournament Tag                   |
| - 6 Floating Sports Keyword Badges (Record Holder, Milestones)        |
| - Gradient Safe Zone for bottom subtitles                             |
+-----------------------------------------------------------------------+
| SCENE 3: RECORD STATISTICS BREAKDOWN — ESPNcricinfo (~10.0s - 12.0s)  |
| - Left Half: High-resolution action cutout in format jersey           |
| - Right Half: Dark glass broadcast stats panel with gold border        |
| - Highlight Pod: Massive bold numeric callout in gold capsule          |
| - Tabular Breakdown: 4-5 statistical rows, generous padding            |
| - Divider Lines: Strictly positioned BELOW text (Zero collision)      |
| - Bottom Pills: Format & team hashtag capsules                        |
+-----------------------------------------------------------------------+
| SCENE 4: ALL-TIME LEADERBOARD / RECORD BOOKS (~8.5s - 10.5s)          |
| - Right Half: Player portrait in authentic format kit                  |
| - Left Half: "INTO THE RECORD BOOKS" header + Subtitle                |
| - Tabular Columns: #, PLAYER, MATCH / OPPONENT, STAT (Right-aligned)  |
| - Row 1 Highlight: Featured record in gold glow border + vector star   |
| - Bottom Capsule: Milestone context (e.g. "FASTEST TO 50 TONS")       |
+-----------------------------------------------------------------------+
| SCENE 5: OUTRO, COMMUNITY DEBATE & SUBSCRIBE CTA (~7.0s - 9.0s)       |
| - Background: Historic Trophy (Wisden / ICC WC) or stadium crowd       |
| - Header: "THE GREATEST RECORD IN CRICKET HISTORY?"                   |
| - Debate Card: "सवाल आपके लिए" + Hindi & English poll questions       |
| - CTA Pill: Channel branding + "SUBSCRIBE FOR MORE" interactive card   |
+-----------------------------------------------------------------------+
```

---

## 3. Dynamic Broadcast Color Palettes

Every video receives a unique palette automatically selected via `ThemeManager.get_theme_for_topic()`:

| Theme Name | Primary Accent | Secondary Accent | Gold Accent | Background Base | Recommended Topic / Vibe |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **CARIBBEAN_MAROON** | West Indies Maroon `#BE183C` | Rose Pink `#F472B6` | Trophy Gold `#FACC15` | Deep Mahogany `#12080E` | Test records, Brian Lara, historic red-ball cricket |
| **CRIMSON_OBSIDIAN** | Crimson Red `#E11D48` | Rose Crimson `#F43F5E` | Trophy Gold `#FACC15` | Midnight Obsidian `#0A0C12` | Virat Kohli, Sachin Tendulkar, ODI centuries, chase masters |
| **EMERALD_MASTER** | Mint Emerald `#22C55E` | Trophy Gold `#FACC15` | Ice Mint `#A7F3D0` | Forest Obsidian `#06120E` | Bowling records, Mohammed Shami, Anil Kumble, spin records |
| **NEON_CYBER** | Electric Cyan `#38BDF8` | Neon Pink `#F43F8E` | Trophy Gold `#FACC15` | Deep Cyber Navy `#080A18` | T20 cricket, fastest 50s/100s, IPL records, explosive feats |
| **CHARCOAL_EMBER** | Fire Orange `#F97316` | Amber Gold `#FBBF24` | Trophy Gold `#FACC15` | Charcoal Slate `#0E0E12` | Match finishes, MS Dhoni, Rinku Singh, last-over thrillers |
| **ROYAL_EMPIRE** | Canary Gold `#FACC15` | Royal Blue `#38BDF8` | Platinum `#F1F5F9` | Deep Royal Navy `#060E20` | Captaincy records, ICC World Cup trophies, legendary captains |

---

## 4. Format-Specific Jersey Rules

1. **Test Cricket Records**:
   - **MANDATORY**: Traditional Test cricket whites and Test cap / maroon/blue helmet.
   - **STRICTLY PROHIBITED**: Colored ODI jerseys, T20 league jerseys, training bibs.
2. **ODI Records (50 Overs & World Cup)**:
   - **MANDATORY**: Official national team colored ODI kit (e.g. India Royal Blue ODI kit).
   - **STRICTLY PROHIBITED**: Test cricket whites.
3. **T20 Records (T20I & Franchise Leagues)**:
   - **MANDATORY**: Official T20I or franchise league jersey.
   - **STRICTLY PROHIBITED**: Test whites.
4. **Validation Enforcement**:
   - `JerseyFormatValidator.validate_asset_jersey()` validates all image assets prior to rendering. Violations cause automatic asset replacement.

---

## 5. Photographic Selection & Image Uniqueness Standards

1. **Perceptual Difference Hashing (`dhash`)**:
   - All images evaluated using 64-bit grayscale difference hashing.
   - Hamming distance between any two scenes in a video must be **> 10 bits**.
   - Hamming distance against all past video assets in `database/asset_usage_registry.json` must be **> 10 bits**.
2. **Zero Image Reuse**:
   - Never use the same player photograph across multiple scenes in the same video.
   - Never use a player photograph as a fullscreen background in Scene 1 or Scene 5.
3. **Quality Gate**:
   - High-resolution, sharp photography only.
   - Authentic match photography preferred over stock photos.
   - Zero watermarked images, zero distorted AI faces.

---

## 6. Audio Engineering Standards

1. **Voice Synthesis**:
   - Engine: Microsoft Edge-TTS
   - Voice: `hi-IN-MadhurNeural`
   - Rate: `+20%` (dynamic sports documentary pacing)
   - Pitch: `-2Hz` (authoritative broadcast baritone)
2. **Loudness Normalization**:
   - Strict EBU R128 standard: **-16.0 LUFS** ($\pm 0.5$ LUFS).
   - Peak limit: **-1.0 dBFS**.
3. **Sound Design (Multi-Track Mixing)**:
   - Ambient cinematic tension drone bed at volume **0.08** (-22 dB relative to voice).
   - Acoustic SFX cues triggered at scene cuts:
     - Cut 0 $\rightarrow$ 1: `dramatic_boom`
     - Cut 1 $\rightarrow$ 2: `transition_whoosh`
     - Cut 2 $\rightarrow$ 3: `bat_hit`
     - Cut 3 $\rightarrow$ 4: `dramatic_boom`
     - Cut 4 $\rightarrow$ 5: `stadium_cheer`

---

## 7. Subtitle Engineering Standards

1. **Font**: Noto Sans Devanagari Bold / Mukta-Bold.
2. **Format**: Advanced SubStation Alpha (`.ass`).
3. **Highlighting**: Active keyword highlighted in Trophy Gold (`&H0015CCFA&`), base words in Crisp White (`&H00FFFFFF&`).
4. **Safe Area**: Bottom 280px reserved with a soft obsidian gradient overlay to guarantee 100% legibility against all backgrounds.

---

## 8. Topic Deduplication & Pre-Publish Validation

1. **Historical Ledger**:
   - Every published short is permanently stored in `database/published_topics_ledger.jsonl` and `cricket_facts.db`.
2. **Multi-Layer Semantic Deduplication**:
   - Exact key check.
   - Normalized title similarity check (rejection threshold > 0.38).
   - Entity collision check (players, match laws, numeric records).
   - Paraphrase and rewording detection.
3. **Automated Continuous Topics**:
   - Curated queue prioritized first.
   - Automated Gemini AI research engine activated when curated queue completes, passing 100% negative exclusion list of all previously published topics.

---

## 9. GitHub Actions & Production Pipeline Compliance

1. **Primary Entrypoint**: `main.py` executing `editor/v3_cinematic_engine.py`.
2. **No Fallback to Legacy Templates**: `V3CinematicEngine.render_v3_short()` is the sole production renderer.
3. **Artifact Persistence**: Both `database/cricket_facts.db`, `database/published_topics_ledger.jsonl`, and `database/asset_usage_registry.json` must be committed back on every run.
