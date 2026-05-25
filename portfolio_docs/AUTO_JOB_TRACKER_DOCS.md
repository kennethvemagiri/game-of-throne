# Auto Job Tracker — Project Documentation

> **Author:** Kenny (Prabhakar Kenneth Vemagiri)
> **Status:** In Development
> **Started:** May 2026
> **Stack:** Node.js, Express, React, Gmail API, Discord Webhooks
> **Cost:** £0.00 — Fully free stack

---

## 1. Problem Statement

Job hunting is emotionally draining. Every time you open your inbox, you're hit with rejections, silence, and the occasional good news buried under noise. The mental toll of manually checking emails, tracking applications in spreadsheets, and feeling the weight of each "unfortunately" adds up fast.

**The core pain:**
- Checking emails repeatedly for job updates
- Feeling the emotional hit of every rejection
- Losing track of which companies responded and which ghosted
- Missing time-sensitive interview invites buried in inbox noise

---

## 2. Solution

An automated job application tracker that:
- Watches your Gmail inbox for job-related emails
- Classifies them automatically (interview, rejection, assessment, etc.)
- Updates a live dashboard with stats and timeline
- Only notifies you via Discord when something actionable happens (interviews, assessments)
- Keeps rejections silent — counted but never pushed to you

**One sentence:** A Gmail-to-Discord pipeline that shields you from rejection noise and only alerts you when it matters.

---

## 3. System Architecture

```
┌─────────────────┐
│   Gmail Inbox   │
└────────┬────────┘
         │ Gmail API (polls every 5 min)
         ▼
┌─────────────────┐
│   Pre-filter    │ ──→ Is this job-related? (subject/sender keywords)
└────────┬────────┘
         │ yes
         ▼
┌─────────────────┐
│   Classifier    │ ──→ Keyword matching + confidence scoring
│   (The Brain)   │
└───┬─────┬────┬──┘
    │     │    │
  HIGH   MED  LOW confidence
    │     │    │
    ▼     ▼    ▼
┌──────┐ ┌──────────┐ ┌──────────────┐
│Auto  │ │Suggested │ │Needs Review  │
│assign│ │+ flagged │ │(manual queue)│
└──┬───┘ └────┬─────┘ └──────┬───────┘
   │          │              │
   ▼          ▼              ▼
┌─────────────────────────────────────┐
│          JSON Store                 │
│      (applications.json)            │
└────────┬───────────────┬────────────┘
         │               │
         ▼               ▼
┌─────────────┐   ┌──────────────┐
│  React      │   │  Discord     │
│  Dashboard  │   │  Webhook     │
│  (stats +   │   │  (alerts for │
│   timeline) │   │   good news) │
└─────────────┘   └──────────────┘
```

---

## 4. Project Structure

```
job-tracker/
├── .env                        # Secrets (never commit to git)
├── .gitignore
├── package.json
├── README.md
│
├── server/
│   ├── index.js                # Express server entry point
│   │
│   ├── auth/
│   │   └── gmail.js            # Google OAuth 2.0 setup + token management
│   │
│   ├── services/
│   │   ├── emailWatcher.js     # Polls Gmail inbox every 5 minutes
│   │   ├── classifier.js       # Keyword matching + confidence scoring
│   │   └── notifier.js         # Discord webhook + daily digest via node-cron
│   │
│   ├── db/
│   │   └── store.js            # JSON file read/write operations
│   │
│   └── data/
│       └── applications.json   # The actual data store
│
├── client/
│   ├── index.html
│   ├── App.jsx                 # Main dashboard component
│   ├── components/
│   │   ├── StatCards.jsx        # Stats grid (total, interviews, rejected, etc.)
│   │   ├── Timeline.jsx         # Application journey timeline
│   │   ├── ProgressBar.jsx      # Pipeline breakdown bar
│   │   ├── FilterBar.jsx        # Status filter buttons
│   │   └── ReviewQueue.jsx      # Manual review queue for flagged emails
│   └── hooks/
│       └── useApplications.js   # Fetches data from server API
│
└── docs/
    └── AUTO_JOB_TRACKER_DOCS.md # This file
```

---

## 5. Build Phases

### Phase 1: Dashboard UI (DONE)
- React component with mock data
- 6 stat cards: total, interviews, rejected, ghosted, response rate, streak
- Pipeline breakdown progress bar
- Timeline view with status-colored cards
- Filter buttons by status
- Interview alert banner

### Phase 2: Gmail API Integration
- Google Cloud project setup
- OAuth 2.0 consent screen (testing mode, personal use only)
- Token management (access + refresh tokens)
- Email polling every 5 minutes via setInterval
- Pre-filter: scan subject and sender for job-related keywords

**Key file:** `server/auth/gmail.js`

**Pre-filter keywords (subject/sender):**
```
application, applied, interview, position, role, hiring,
recruitment, career, job, candidate, opportunity, offer,
assessment, shortlist, HR, talent, recruiter
```

### Phase 3: Keyword Classifier
- Input: email subject + body + sender address
- Output: { status, company, role, confidence }

**Classification statuses:**

| Status | Description | Example trigger |
|--------|-------------|-----------------|
| interview | Interview or call invite | "invite you for an interview" |
| rejected | Application unsuccessful | "unfortunately", "regret to inform" |
| acknowledged | Application received confirmation | "thank you for applying" |
| assessment | Coding test or task sent | "complete this coding challenge" |
| recruiter_inbound | Recruiter reached out to you | "came across your profile" |
| needs_review | Ambiguous, low confidence | Unclear email, mixed signals |
| skip | Not job-related | Newsletter, promo, spam |

**Keyword banks:**

```javascript
const KEYWORDS = {
  interview: [
    'interview', 'invite you', 'schedule a call',
    'meet the team', 'next stage', 'shortlisted',
    'would like to speak', 'book a time'
  ],
  rejected: [
    'unfortunately', 'regret to inform', 'not progressing',
    'other candidates', 'not successful', 'wish you well',
    'decided not to', 'will not be moving forward'
  ],
  acknowledged: [
    'received your application', 'thank you for applying',
    'application has been submitted', 'confirmation of application',
    'we have received', 'your application for'
  ],
  assessment: [
    'coding challenge', 'technical test', 'assessment',
    'complete this task', 'take-home', 'online test',
    'aptitude test', 'skills assessment'
  ],
  recruiter_inbound: [
    'came across your profile', 'reaching out',
    'would you be interested', 'exciting opportunity',
    'i found your', 'on behalf of our client'
  ]
};
```

**Confidence scoring:**
- HIGH (3+ keyword matches from same category) → auto-classify
- MEDIUM (1-2 matches) → suggest status, flag for review
- LOW (0 matches but job-related sender domain) → needs_review

**Company extraction logic:**
1. Parse sender email domain: `hr@fanduel.com` → "FanDuel"
2. Fallback: scan subject for company name patterns
3. Clean up: remove common suffixes (.co.uk, Ltd, Inc, PLC)

**Role extraction logic:**
1. Regex: `for the (.*?) (position|role|vacancy)`
2. Regex: `RE: (.*?) (application|role)`
3. Fallback: first line of subject after company name

### Phase 4: Wire Everything Together
- Connect emailWatcher → classifier → JSON store
- Create REST API: `GET /api/applications`
- Add CORS for frontend-backend communication
- Build review queue UI component
- One-click confirm/reassign for flagged emails
- API endpoint: `POST /api/applications/:id/status` for manual updates

### Phase 5: Discord Notifications
- Discord webhook integration (no bot needed, just a URL)
- Rich embed messages with color-coded status

**Notification routing:**

| Status | Alert Type | When |
|--------|-----------|------|
| interview | INSTANT | Immediately on classification |
| assessment | INSTANT | Immediately on classification |
| recruiter_inbound | INSTANT | Immediately on classification |
| needs_review | DAILY DIGEST | Batched at 9:00 PM via node-cron |
| rejected | SILENT | Dashboard only, no notification |
| acknowledged | SILENT | Dashboard only, no notification |
| applied | SILENT | Dashboard only, no notification |

**Discord embed examples:**

Interview alert (green):
```json
{
  "embeds": [{
    "title": "🔥 Interview invite!",
    "color": 1096065,
    "fields": [
      { "name": "Company", "value": "FanDuel", "inline": true },
      { "name": "Role", "value": "QA Engineer", "inline": true },
      { "name": "Snippet", "value": "We'd like to invite you for a first-round interview..." }
    ],
    "timestamp": "2026-05-24T10:30:00.000Z"
  }]
}
```

Assessment alert (teal):
```json
{
  "embeds": [{
    "title": "📝 Assessment received!",
    "color": 1941875,
    "fields": [
      { "name": "Company", "value": "Scott Logic", "inline": true },
      { "name": "Role", "value": "Graduate Dev", "inline": true },
      { "name": "Snippet", "value": "Please complete the following coding challenge within 5 days..." }
    ],
    "timestamp": "2026-05-24T14:00:00.000Z"
  }]
}
```

Daily digest (purple):
```json
{
  "embeds": [{
    "title": "📋 Daily review queue — 3 emails need your attention",
    "color": 9146046,
    "fields": [
      { "name": "1. Morgan Stanley", "value": "Subject: Following up on your application..." },
      { "name": "2. Capgemini", "value": "Subject: Update regarding your candidacy..." },
      { "name": "3. Leonardo UK", "value": "Subject: RE: Software Engineer role..." }
    ],
    "footer": { "text": "Review these at your dashboard" },
    "timestamp": "2026-05-24T21:00:00.000Z"
  }]
}
```

### Phase 6: Deploy
- Frontend → Vercel (free tier)
- Backend → Vercel Serverless Functions OR run locally
- Gmail polling → Vercel Cron Jobs (free tier, 2 jobs, hourly minimum)
- Alternative: keep server running locally during active job hunt

---

## 6. Tech Stack

| Layer | Technology | Cost |
|-------|-----------|------|
| Runtime | Node.js | Free |
| Server | Express.js | Free |
| Frontend | React | Free |
| Email | Gmail API + OAuth 2.0 | Free |
| Classification | Custom keyword matching (JS) | Free |
| Database | JSON file (applications.json) | Free |
| Notifications | Discord Webhooks | Free |
| Scheduling | node-cron | Free |
| Hosting | Vercel (free tier) | Free |
| **Total** | | **£0.00/month** |

---

## 7. Environment Variables

```env
# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/callback

# Discord
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your/webhook/url

# Server
PORT=3001
```

**IMPORTANT:** Never commit `.env` to git. Add it to `.gitignore`.

---

## 8. Data Schema

Each application entry in `applications.json`:

```json
{
  "id": "uuid-string",
  "company": "FanDuel",
  "role": "QA Engineer",
  "status": "interview",
  "confidence": "high",
  "dateApplied": "2026-05-15",
  "dateLastEmail": "2026-05-20",
  "responseTimeDays": 5,
  "emailSnippet": "We'd like to invite you for a first-round...",
  "senderEmail": "recruitment@fanduel.com",
  "flaggedForReview": false,
  "suggestedStatus": null,
  "history": [
    { "status": "applied", "date": "2026-05-15" },
    { "status": "acknowledged", "date": "2026-05-16" },
    { "status": "interview", "date": "2026-05-20" }
  ]
}
```

**Key design decisions:**
- `history` array tracks the full journey of each application
- `suggestedStatus` is populated when confidence is medium
- `flaggedForReview` marks items for the manual review queue
- `responseTimeDays` is auto-calculated from dateApplied to dateLastEmail

---

## 9. API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/applications | Get all applications |
| GET | /api/applications/:id | Get single application |
| POST | /api/applications/:id/status | Manually update status |
| GET | /api/stats | Get aggregated statistics |
| GET | /api/review-queue | Get items flagged for review |
| POST | /api/review-queue/:id/confirm | Confirm suggested status |
| POST | /api/review-queue/:id/reassign | Assign different status |
| GET | /auth/google | Start OAuth flow |
| GET | /auth/callback | OAuth callback handler |

---

## 10. Dashboard Features

### Stats Panel
- Total applications sent
- Interview invites received
- Rejections count
- Ghosted count (no reply after 14 days)
- Response rate percentage
- Current application streak (consecutive days)

### Pipeline Breakdown
- Visual progress bar showing proportion of each status
- Color-coded segments: green (interview), blue (acknowledged), gray (applied), purple (ghosted), red (rejected), teal (assessment)

### Timeline View
- Chronological list of all applications
- Each card shows: company, role, status badge, days ago, response time
- Color-coded by status
- Filterable by status

### Review Queue
- List of emails classified as needs_review or medium confidence
- Shows email snippet and suggested status
- One-click confirm button for suggested status
- Dropdown to manually assign different status
- Clears from queue once resolved

### Interview Alert Banner
- Green banner at top when active interviews exist
- Lists company names with interview status
- Pulsing indicator for visual attention

---

## 11. Discord Webhook Setup Guide

1. Open Discord → go to your server
2. Click the gear icon on the channel you want alerts in
3. Go to Integrations → Webhooks
4. Click "New Webhook"
5. Name it "Job Tracker" (or whatever you like)
6. Copy the webhook URL
7. Paste it in your `.env` file as `DISCORD_WEBHOOK_URL`
8. Done — no bot creation, no token management, no permissions

---

## 12. Gmail API Setup Guide

1. Go to https://console.cloud.google.com
2. Create a new project (e.g. "Job Tracker")
3. Enable the Gmail API (APIs & Services → Library → search "Gmail API")
4. Go to APIs & Services → Credentials
5. Click "Create Credentials" → "OAuth client ID"
6. Application type: "Web application"
7. Add redirect URI: `http://localhost:3000/auth/callback`
8. Copy Client ID and Client Secret to your `.env`
9. Go to OAuth consent screen → set to "Testing"
10. Add your Gmail address as a test user
11. Done — this runs in testing mode so only YOUR account works

**Scopes needed:**
```
https://www.googleapis.com/auth/gmail.readonly
```

We only need read access. The app never sends emails or modifies your inbox.

---

## 13. Future Scope (SaaS Potential)

If this proves useful as a personal tool, here's the expansion path:

| Feature | Effort | Impact |
|---------|--------|--------|
| Multi-user auth | Medium | Turns it into a real product |
| Chrome extension | Medium | One-click tracking from job boards |
| AI classifier upgrade (Gemini free tier) | Low | Better accuracy than keywords |
| Mobile app (React Native) | High | Check stats on the go |
| Integration with LinkedIn, Indeed | Medium | Auto-detect applications |
| Team/cohort view | Medium | Bootcamp graduates tracking together |
| Analytics & insights | Low | "You get more interviews on Tuesdays" |
| Resume A/B testing | Medium | Track which CV version gets more callbacks |

**Validation before building any of these:**
- Can you name 10 people who'd pay for this?
- Can you sell it before building it?
- Is there an exponentially growing market?

---

## 14. Known Limitations

- Keyword classifier won't catch every email format (85% accuracy estimated)
- Gmail API in testing mode limited to 100 test users
- JSON file storage won't scale past ~10,000 entries (migrate to Supabase if needed)
- Vercel free tier cron jobs run hourly minimum (not real-time)
- Company name extraction from email domains isn't perfect (e.g. `noreply@greenhouse.io` is a job platform, not the actual company)
- Some companies use recruitment platforms (Workday, Greenhouse, Lever) — sender domain won't match company name

**Mitigation:** The `needs_review` queue catches what the classifier misses. Review daily, take 2 minutes, done.

---

## 15. Git Ignore

```gitignore
node_modules/
.env
server/data/applications.json
dist/
.DS_Store
```

---

*Built by Kenny — because caveman brain shouldn't suffer through rejection emails.* 🦴
