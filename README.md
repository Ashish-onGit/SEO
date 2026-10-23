# Automated SEO Research & Blog Drafting System

> **Production-minded, unattended SEO intelligence and blog drafting automation for student accommodation in Uttar Pradesh, India.**

This system runs unattended every morning (via Windows Task Scheduler) to discover trending search topics, conduct keyword research, analyze competing articles, score and select the highest-opportunity topic, generate an evidence-grounded 20-point SEO brief, write a complete human-grade first draft using Gemini, execute multi-layer quality assurance, persist state in SQLite, and email the results via Gmail.

---

## 1. Uttar Pradesh Student Accommodation Focus

The system is configured specifically for higher education hubs and student coaching clusters across **Uttar Pradesh**:

- **Greater Noida**: Knowledge Park I, II & III; Pari Chowk; Galgotias, Sharda, Gautam Buddha University, Bennett University.
- **Noida**: Sector 125/126 Institutional Corridor, Sector 62; Amity University, JIIT.
- **Lucknow**: Hazratganj, Indira Nagar, Faizabad Road; University of Lucknow, AKTU, BBD University, IIM Lucknow.
- **Kanpur**: Kakadeo (coaching hub for NEET/JEE), Kalyanpur; IIT Kanpur, HBTU, CSJMU.
- **Varanasi**: Lanka, Assi Ghat; Banaras Hindu University (BHU), IIT (BHU).
- **Prayagraj**: Katra, Civil Lines; Allahabad University, MNNIT, coaching centers.
- **Ghaziabad**: ABES, KIET, Raj Nagar, Indirapuram.

---

## 2. Complete Workflow & Architecture

```
[ Stage A: Topic Discovery ] (Google Trends RSS + UP Regional Seeds + Google Suggest)
           │
[ Stage B: Keyword Research ] (Intent: Informational / Commercial / Transactional / Navigational)
           │
[ Stage C: Competitor Analysis ] (Scrapes up to 5 competitors, extracts headings, gaps & word counts)
           │
[ Stage D: Weighted Scoring ] (Accommodation 35%, Trend 20%, Rank 20%, Biz 25% + Deduplication Penalty)
           │
[ Stage E: SEO Brief Generation ] (20-Point Brief, 10 Grounded FAQs, Verified Internal Links)
           │
[ Stage F: Blog Draft Generation ] (Gemini API with Anti-Hallucination & Anti-Price-Invention Prompts)
           │
[ Stage G: Multi-Layer QA Gate ] (Deterministic Structural/Link/Factual + AI-Assisted Qualitative Review)
           │
[ Stage H: SQLite State Persistence ] (Atomic state machine: DISCOVERED -> RESEARCHED -> ... -> EMAIL_SENT)
           │
[ Stage I: Delivery & Export ] (Gmail OAuth 2.0 HTML report + Markdown artifact attachment)
```

---

## 3. Quick Start & Installation

### Prerequisites
- Windows 10 / 11
- Python 3.11+ (Python 3.14 tested and verified)
- Git for Windows

### 1. Clone & Install Dependencies
Open PowerShell in the project directory:
```powershell
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```powershell
copy .env.example .env
```

Key environment settings in `.env`:
```env
# AI Provider ('gemini' or 'mock' for test simulation)
AI_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash

# Geographic and Brand Scope
TARGET_STATE=Uttar Pradesh
TARGET_CITIES=Greater Noida,Noida,Lucknow,Kanpur,Varanasi,Prayagraj,Ghaziabad
COMPANY_NAME=CampusNest UP
COMPANY_WEBSITE=https://campusnest-up.example.com

# Gmail Delivery
GMAIL_SENDER_EMAIL=your_email@gmail.com
GMAIL_RECIPIENT_EMAIL=editorial_team@gmail.com
EMAIL_DRY_RUN=true   # Set to false once Gmail OAuth credentials.json is provided
```

### 3. Configure Brand Details & Verified Internal URLs
Edit `config/brand_config.json` to insert your company's actual:
- Brand name and website domain.
- Verified internal URLs and target anchor texts.
*(The system strictly validates internal links against this list to prevent hallucinated URLs).*

---

## 4. Running the System

### Manual Run (Full Pipeline with Console Progress)
```powershell
python main.py --manual
```

### Dry-Run Mode (100% Offline Simulation)
Runs without requiring external API keys. Generates the brief, draft, QA report, and exports the email report to `output/emails/`:
```powershell
python main.py --dry-run
```

### View System Status & Recent Execution History
```powershell
python main.py --status
```

### Resume an Interrupted Run
If a run was stopped midway, resume from its last safe stage:
```powershell
python main.py --resume run_YYYYMMDD_HHMMSS
```

---

## 5. Setting up Windows Task Scheduler (Daily at 07:00 AM)

The application includes an automated PowerShell setup script with **missed-run recovery** (if your laptop is asleep at 7:00 AM, the task executes automatically upon wake-up).

### Automated Setup via PowerShell
Run PowerShell as Administrator in the project directory:
```powershell
powershell -ExecutionPolicy Bypass -File .\setup_scheduler.ps1
```

### Manual Setup via Windows GUI
1. Open Windows Search and type **Task Scheduler**.
2. Click **Create Task...** (not Basic Task):
   - **General**: Name it `SEO_Daily_Draft_Automation`. Check *Run whether user is logged on or not* or *Run only when user is logged on*.
   - **Triggers**: Click *New*, set to *Daily* at `07:00 AM`.
   - **Actions**: Click *New*, set Action to *Start a program*:
     - Program/script: `cmd.exe`
     - Add arguments: `/c "run_daily.bat"`
     - Start in: `C:\Users\Ashish Pandey\OneDrive\Desktop\Ryuk\SEO Automation Tool`
   - **Conditions**: Check *Wake the computer to run this task*. Uncheck *Stop if the computer switches to battery power*.
   - **Settings**: Check *Run task as soon as possible after a scheduled start is missed*. Set *If the task is already running: Do not start a new instance*.

---

## 6. How to Obtain Credentials

### 1. Gemini API Key (Free Tier)
1. Visit [Google AI Studio](https://aistudio.google.com/).
2. Sign in with your Google account.
3. Click **Get API key** -> **Create API key**.
4. Paste the key into your `.env` file under `GEMINI_API_KEY=...`.

### 2. Gmail OAuth 2.0 Credentials (for Live Email Sending)
1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (e.g. `SEO-Automation`).
3. Enable the **Gmail API** in *APIs & Services > Library*.
4. Configure the **OAuth Consent Screen** (User Type: External, add your email under Test Users).
5. Go to *APIs & Services > Credentials* -> **Create Credentials** -> **OAuth client ID**:
   - Application type: **Desktop app**.
   - Download the JSON file and save it in the project root as `credentials.json`.
6. Set `EMAIL_DRY_RUN=false` in `.env`.
7. On first live run, a browser window will open asking you to authorize the Gmail send scope. The resulting token will be safely stored in `token.json` for subsequent unattended runs.

---

## 7. Automated Testing Suite

All features include unit and integration tests. Run tests anytime with:
```powershell
python -m pytest tests/ -v
```

### Test Coverage Highlights
- `tests/test_storage.py`: SQLite migrations, repository CRUD, and email idempotency.
- `tests/test_scoring.py`: 4-factor scoring weights, handling missing competitor data, deduplication penalty, threshold gate.
- `tests/test_keywords.py`: Search intent classification (Informational, Transactional, Commercial, Navigational) and business relevance heuristics.
- `tests/test_brief.py`: 20-point brief specification and verified internal link compliance.
- `tests/test_qa.py`: Deterministic heading hierarchy, forbidden claim detection, unverified URL blocking, and QA Gate pass/fail logic.
- `tests/test_pipeline.py`: Complete end-to-end pipeline execution with artifact writing.
- `tests/test_retry_recovery.py`: Interrupted run resumption and duplicate email prevention.

---

## 8. Artifacts & Directories

- `output/drafts/`: Generated blog drafts in GitHub-flavored Markdown with YAML frontmatter.
- `output/briefs/`: Structured 20-point SEO briefs.
- `output/emails/`: Formatted HTML email reports.
- `logs/`: Daily rotated execution logs.
- `data/seo_automation.db`: SQLite persistent state database.
