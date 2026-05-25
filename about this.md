# Game of Throne — Automated Job Pipeline

## What it is

Game of Throne is a full-stack automation system that turns a chaotic job search into a structured, real-time pipeline — no spreadsheets, no manual sorting, no missed opportunities.

It connects directly to your Gmail inbox, pulls every job-related email, classifies it through a custom keyword-scoring engine, and routes it into the correct pipeline stage automatically: interview, assessment, recruiter inbound, acknowledged, or rejected. When the classifier isn't confident, it flags the item for human review with a suggested status rather than guessing wrong. When something time-sensitive lands — an interview invite, a coding assessment, a recruiter reaching out — it fires a real-time Discord notification within seconds.

A nightly digest at 9 PM summarizes everything still waiting for your attention. Nothing slips through.

## The value it delivers

- **Inbox chaos becomes a clean pipeline.** Every job-related email is classified and organized the moment it arrives. You review only what the system can't resolve on its own.
- **Time-sensitive signals surface instantly.** Interviews, assessments, and recruiter messages trigger real-time Discord alerts — you respond faster than candidates who check email once a day.
- **One dashboard, complete visibility.** Metric cards, a filterable application table, smooth area charts tracking pipeline activity over time, and a calendar view — all in a single tab-based interface with no page reloads.
- **Suggested jobs from external feeds.** Automation-scraped listings (e.g. Indeed) appear alongside your tracked applications with one-click reject or view actions.
- **Portable and deployable.** Runs locally with a single command, or deploys to Vercel with serverless functions, scheduled cron jobs, and a static frontend — zero infrastructure to manage.

## Why I'm building it

Job searching generates an overwhelming volume of fragmented, time-sensitive information scattered across inboxes, job boards, and recruiter DMs. Most people track this in spreadsheets — or not at all — which means missed interviews, forgotten follow-ups, and lost momentum at the worst possible time.

I built Game of Throne because I solve problems by building systems. This isn't a generic job board clone — it's a personal automation tool purpose-built for my own workflow, designed to scale with the volume of applications without adding cognitive load. It reflects how I think about software engineering: automate the repetitive, surface what matters, keep the interface honest, and ship something that actually runs in production.

## What makes this different

- **Classification without AI API costs.** The email classifier uses a deterministic keyword-scoring engine with priority ranking, company/role extraction, and confidence thresholds — no LLM calls, no API keys, no per-request billing, no latency. It handles the common cases reliably and routes edge cases to human review instead of hallucinating.
- **Notification-first architecture.** The system doesn't wait for you to check a dashboard. High-priority status changes fire instant webhook notifications. Low-priority items accumulate into a daily digest. You stay informed without polling.
- **Full-stack ownership, single codebase.** API, classifier, notification service, scheduler, frontend, deployment config — one repo, no glue services, no external dependencies beyond Gmail and Discord. I own every layer.
- **Editorial UI with restraint.** Warm neutral palette, strong typographic hierarchy, one accent color, no glow effects or decoration for its own sake. The dashboard communicates through clarity — smooth area charts, color-coded status badges, hover-reveal dismiss buttons — designed for daily use, not screenshots.

## The unique strengths I bring

This project demonstrates end-to-end product thinking — from problem identification to production deployment:

- **Systems design** — Architecting a pipeline that spans email ingestion, NLP classification, real-time notifications, scheduled digests, and a reactive frontend, all in a single deployable unit.
- **Pragmatic engineering** — Choosing a keyword classifier over an LLM because the use case doesn't need it. Using JSON storage for portability. Making hard trade-offs that serve the user, not the resume.
- **Production readiness** — Vercel serverless deployment, cron scheduling, OAuth2 integration, environment-based configuration, error handling with retry logic, and graceful degradation when services are unavailable.
- **Design sensibility** — Building a UI that's genuinely pleasant to use daily, not just functionally correct. Responsive layouts, smooth animations, accessible markup, and visual hierarchy that guides attention.

## Technology

**Backend — Python 3 / FastAPI**
- Async API with clean router separation and Pydantic validation
- Custom keyword classifier with confidence scoring, priority ranking, and company/role extraction
- Gmail API integration with OAuth2, pagination, retry logic, and incremental sync
- Discord webhook integration — instant notifications for high-priority events, nightly digest for review items
- APScheduler for local cron; Vercel Cron for production scheduling
- Mangum adapter wrapping FastAPI for Vercel serverless functions
- JSON file-based data store with Vercel-compatible `/tmp` fallback for serverless environments

**Frontend — React 18 / TypeScript / Vite**
- Single-page tab-based layout with zero routing dependencies
- Context-driven state management with custom hooks (`useApplications`, `useSuggestedJobs`)
- Pure SVG area charts with smooth bezier curves and gradient fills — no charting library
- Responsive editorial design system with warm neutrals and purposeful color
- Accessible markup with ARIA labels, keyboard navigation, and semantic HTML

**Infrastructure**
- Vercel deployment: `vercel.json` with rewrites, cron schedules, and serverless function config
- API proxy in development via Vite — seamless local/production parity
- Concurrently runs backend + frontend in one `npm run dev` command
- Environment-based configuration for Gmail OAuth, Discord webhooks, and cron secrets

## Running locally

```bash
npm install
cd frontend && npm install && cd ..
cp .env.example .env   # fill in your Gmail and Discord credentials
npm run dev
```

Backend on `http://localhost:3001` — Frontend on `http://localhost:5173`

## Deploying to Vercel

1. Push to GitHub
2. Import the repo in Vercel
3. Set environment variables: `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REDIRECT_URI`, `DISCORD_WEBHOOK_URL`, `CRON_SECRET`
4. Deploy — Vercel handles the build, serverless functions, and cron jobs automatically
