# 🏏 Cricket Facts YouTube Shorts Factory

A production-grade, fully automated factory that researches, verifies, writes, narrates, animates, edits, and schedules **2 high-retention Cricket Facts YouTube Shorts daily** using **100% free, open-source tools**.

---

## 🌟 Key Features

1. **Fact Research & Verification Engine**:
   - Researches genuine, verified facts across 15 cricket categories (MCC Laws, IPL records, World Cup anomalies, legendary milestones).
   - Strict 4-tier fact quality scoring (**Reliability 40**, **Uniqueness 25**, **Curiosity 20**, **Visual Storytelling 15**; threshold **>= 80/100**).
   - Automated cross-verification with ESPNcricinfo, Wisden, ICC, MCC, and BCCI records. Rejects speculation and fabrication.
   - SQLite content database with SHA-256 deduplication (prevents duplicate facts and duplicate uploads).

2. **Professional Hindi Scriptwriting**:
   - Structured 30–45 second sports-documentary scripts.
   - **Hook (0–3s)**: High-curiosity opening line (no repetitive greetings).
   - **Main Story (3–28s)**: Fast-paced narrative in natural conversational Hindi with authentic English cricket terms.
   - **Surprise / Explanation (28–38s)**: Climactic detail or rule twist.
   - **Ending / CTA (38–42s)**: Specific question to stimulate viewer comments and engagement.

3. **High-Definition Deep Male Hindi Voice Narration**:
   - Powered by neural broadcast TTS (`hi-IN-MadhurNeural`) with rich sports-documentary bass (`-2Hz` pitch adjustment) and calibrated `1.2x` pacing.
   - Offline fallback support via local Piper ONNX model (`hi_IN-rohan-medium`).
   - Automated audio post-processing: silence trimming, pause compression, and broadcast loudness normalization to **-16 LUFS** (YouTube Shorts standard).
   - Background audio ducking with subtle cinematic sports tension bed.

4. **Authentic Programmatic Visual Generation & Editing**:
   - Generates exact **1080x1920 (9:16) 30 FPS MP4** videos matching the specific cricket fact being narrated.
   - Custom dynamic graphics:
     - Cricket pitch & field rule diagrams (e.g., ground helmet 5-penalty runs, non-striker run out).
     - Digital broadcast scoreboards and record comparison cards.
     - Player and historic match incident spotlight cards.
     - Call-to-action subscription and comment screens.
   - Subtle Ken Burns camera zoom and pan (`zoompan`) to eliminate static slideshow appearance.

5. **Word-Level Synchronized Devanagari Subtitles**:
   - High-contrast, bold Devanagari typography (`Noto Sans Devanagari`).
   - Electric Gold/Yellow highlighting on numbers, records, and cricket keywords.
   - Placed in the mobile safe zone (340px bottom margin) to avoid overlapping YouTube Shorts UI controls.

6. **Automated Quality Control (QC) Inspector**:
   - Inspects rendered videos via FFprobe before publishing:
     - Exact 1080x1920 resolution & 9:16 aspect ratio.
     - Duration strictly between 20s and 55s.
     - Valid H.264 video codec and AAC stereo audio.
     - Audio presence and black-frame detection.

7. **YouTube Data API v3 Upload & Scheduling**:
   - OAuth 2.0 authentication with automated token refreshing.
   - Scheduled upload support for Asia/Kolkata timezone:
     - **Short 1**: 11:00 AM IST
     - **Short 2**: 07:00 PM IST
   - Generates SEO-optimized titles, descriptions with source citations, hashtags, tags, and pinned comments.
   - Safe dry-run mode enabled by default (`AUTO_UPLOAD=false`).

8. **Rich CLI Dashboard**:
   - Live metrics display: facts researched, approved, videos rendered, pending uploads, scheduled publication dates, and recent production history.

---

## 🛠️ Free-First Technology Stack

| Component | Tool / Library | Cost |
| :--- | :--- | :--- |
| **Language & Engine** | Python 3.12 | Free / Open-Source |
| **Voice Synthesis (Primary)** | `edge-tts` (`hi-IN-MadhurNeural`, 1.2x, -2Hz) | 100% Free, Zero API Keys |
| **Voice Synthesis (Offline)** | `piper-tts` (`hi_IN-rohan-medium.onnx`) | 100% Free, Runs Locally |
| **Audio Processing** | FFmpeg (`silenceremove`, `loudnorm`, `amix`) | Free / Open-Source |
| **Visual Composition** | Pillow & NumPy (1080x1920 canvas) | Free / Open-Source |
| **Video Editing** | FFmpeg (`zoompan`, `ass`, `libx264`, `aac`) | Free / Open-Source |
| **Hindi Font** | Noto Sans Devanagari Bold | Free (SIL Open Font License) |
| **Database** | SQLite3 (`cricket_facts.db`) | Free / Built-in |
| **Scheduling** | Python `schedule` / Linux `cron` / `systemd` | Free / Built-in |
| **Publishing** | YouTube Data API v3 | Free Quota (10,000 units/day) |

---

## 📁 Project Architecture

```
Cricket shorts/
├── config/
│   ├── settings.yaml          # Channel specs, video resolutions, thresholds
│   └── voice_config.yaml      # Voice pitch, speech rate, loudness targets
├── database/
│   ├── models.py              # SQLite schemas, deduplication hashes, metrics
│   └── cricket_facts.db       # SQLite database (auto-created)
├── research/
│   ├── fact_repository.py     # Verified facts pool across 15 categories
│   ├── verify_facts.py        # Cross-reference & anti-speculation verifier
│   ├── fact_scorer.py         # 4-tier quality scoring engine (>=80 threshold)
│   └── discover_facts.py      # Candidate discovery and evaluation
├── scripts/
│   ├── generate_script.py     # Timed Hindi script (Hook, Story, Surprise, CTA)
│   └── generate_metadata.py   # SEO Title, Description, Hashtags, Pinned comment
├── voice/
│   ├── tts_engine.py          # Unified Edge-TTS & Piper TTS engine
│   └── audio_processor.py     # Silence trimmer, -16 LUFS normalizer, BGM ducking
├── visuals/
│   ├── animation_engine.py    # 1080x1920 graphics (stadium, pitch, scoreboard)
│   ├── visual_selector.py     # Sequences scenes matching narration timeline
│   └── subtitle_generator.py  # Synchronized ASS subtitles with yellow highlights
├── editor/
│   └── video_renderer.py      # Ken Burns zoom, subtitle burning, MP4 composition
├── qc/
│   └── video_qc.py            # FFprobe technical quality inspector
├── youtube/
│   ├── authenticate.py        # OAuth 2.0 flow & token storage
│   ├── upload.py              # Resumable upload & scheduled publishing
│   └── scheduler.py           # Publication planner (11:00 AM & 07:00 PM IST)
├── dashboard/
│   └── cli_report.py          # Rich terminal dashboard
├── assets/
│   ├── models/                # Local Piper ONNX voice models
│   ├── audio/                 # Optional custom BGM tracks
│   └── sfx/                   # Optional custom sound effects
├── output/
│   ├── videos/                # Finished 1080x1920 MP4 Shorts
│   ├── audio/                 # Processed audio tracks
│   └── snapshots/             # QC frame snapshots
├── tests/                     # Automated unit test suite (11 tests)
├── main.py                    # Master CLI orchestrator
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🚀 Setup & Execution Guide

### 1. Prerequisites
- **Linux / macOS / Windows (WSL)**
- **Python 3.10+**
- **FFmpeg 6+ or 7+** (with `libx264`, `libass`, `freetype` enabled)
- **Hindi Fonts**: `fonts-noto-core` (Installed via `sudo apt install fonts-noto-core`)

### 2. Installation
```bash
cd "Cricket shorts"

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Verify Setup with Unit Tests
```bash
./venv/bin/python3 -m unittest discover tests
```
*All 11 unit tests should pass with `OK`.*

---

## 🎬 How to Run

### Generate 1 Sample Short (Quick Verification)
```bash
./venv/bin/python3 main.py --single
```
*Generates one complete Short in `output/videos/`, runs QC, and previews the scheduled slot.*

### Generate Full Daily Quota (2 Shorts)
```bash
./venv/bin/python3 main.py --run
```
*Researches, verifies, renders, and prepares both daily Shorts for 11:00 AM IST and 07:00 PM IST.*

### View System Dashboard
```bash
./venv/bin/python3 main.py --dashboard
```

---

## 📡 YouTube Publishing Setup

### Step 1: Obtain Google Cloud Credentials
1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project named `Cricket-Shorts`.
3. Enable **YouTube Data API v3**.
4. Go to **APIs & Services > Credentials** > Create **OAuth client ID** (Application type: *Desktop App*).
5. Download the JSON credential file and save it as `client_secrets.json` in the root folder of this project:
   ```bash
   cp ~/Downloads/client_secret_*.json ./client_secrets.json
   ```

### Step 2: Authorize YouTube Account
Run the interactive authentication flow:
```bash
./venv/bin/python3 main.py --auth
```
A browser window will open asking you to grant permission. Once approved, `token.pickle` is generated and future uploads authenticate automatically without prompting.

### Step 3: Enable Automatic Upload
In `.env` or `config/settings.yaml`, update:
```env
AUTO_UPLOAD=true
```
When `AUTO_UPLOAD=false` (default), the pipeline runs safely in **Dry-Run Mode**: videos and metadata are fully generated, checked by QC, and logged, but no external API call is made.

---

## ⏰ Independent Daily Automation (No IDE Required)

The factory can run 100% autonomously in the background without needing Antigravity or any IDE open.

### Method A: Built-in Python Background Daemon
```bash
nohup ./venv/bin/python3 main.py --schedule > logs/scheduler.log 2>&1 &
```
*Runs continuously, triggering production at 08:30 AM IST every day so both Shorts are rendered, verified, and scheduled for the 11:00 AM and 07:00 PM publication windows.*

### Method B: Linux Cron Job (Recommended)
Edit your crontab:
```bash
crontab -e
```
Add the following entry (runs daily at 08:30 AM IST):
```cron
30 8 * * * cd "/home/rishabh/Cricket shorts" && ./venv/bin/python3 main.py --run >> logs/cron.log 2>&1
```

*Note: The machine must be powered on and connected to the internet during scheduled execution.*

---

## 🛡️ Content Policy & Quality Safeguards

- **Zero Broadcast Copyright Infringement**: Never downloads unauthorized TV clips. All visuals are dynamically rendered illustrations, authentic digital scoreboards, stadium aesthetics, and verified records.
- **Strict Anti-Fabrication**: Claims require official citations (MCC Laws, ICC match reports, ESPNcricinfo scorecards). Any statement with speculative language (*"rumored"*, *"might have"*) is automatically rejected by `FactVerifier`.
- **Deduplication Guarantee**: SHA-256 topic/fact normalization guarantees no fact is reused.
