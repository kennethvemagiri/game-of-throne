# Gmail API Setup

Follow these steps to connect your Gmail inbox to Game of Throne.

## 1. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **Select a project** in the top bar, then **New Project**
3. Name it (e.g. "Game of Throne") and click **Create**

## 2. Enable the Gmail API

1. In your new project, go to **APIs & Services > Library**
2. Search for **Gmail API**
3. Click **Gmail API** and then **Enable**

## 3. Configure OAuth Consent Screen

1. Go to **APIs & Services > OAuth consent screen**
2. Select **External** and click **Create**
3. Fill in the required fields:
   - App name: `Game of Throne`
   - User support email: your email
   - Developer contact: your email
4. Click **Save and Continue**
5. On the **Scopes** page, click **Add or Remove Scopes**
   - Add `https://www.googleapis.com/auth/gmail.readonly`
   - Click **Update**, then **Save and Continue**
6. On the **Test users** page, click **Add Users**
   - Add the Gmail address you want to connect
   - Click **Save and Continue**
7. Click **Back to Dashboard**

## 4. Create OAuth 2.0 Credentials

1. Go to **APIs & Services > Credentials**
2. Click **Create Credentials > OAuth client ID**
3. Application type: **Web application**
4. Name: `Game of Throne Web`
5. Under **Authorized redirect URIs**, add:
   ```
   http://localhost:3001/api/auth/gmail/callback
   ```
6. Click **Create**
7. Copy the **Client ID** and **Client Secret**

## 5. Configure Environment Variables

Create a `.env` file in your project root (copy from `.env.example`):

```
GMAIL_CLIENT_ID=your_client_id_here
GMAIL_CLIENT_SECRET=your_client_secret_here
GMAIL_REDIRECT_URI=http://localhost:3001/api/auth/gmail/callback
```

## 6. Connect Your Gmail

1. Start the app:
   ```
   npm run dev
   ```
2. Open `http://localhost:5173` in your browser
3. Click the **Connect Gmail** button in the dashboard header
4. Sign in with your Google account and authorize the app
5. You will be redirected back to the dashboard

The OAuth token is saved to `backend/data/token.json` (gitignored). It auto-refreshes, so you only need to authorize once.

## 7. Syncing Emails

Once connected:

- Click **Sync** in the header to manually fetch and classify new emails
- Locally, emails are fetched automatically every 15 minutes via APScheduler
- On Vercel, a cron job hits `/api/gmail/fetch` every 15 minutes

## Production Deployment (Vercel)

For Vercel, update the redirect URI:

1. In Google Cloud Console, add your production callback URL to **Authorized redirect URIs**:
   ```
   https://your-domain.vercel.app/api/auth/gmail/callback
   ```
2. Set the environment variables in Vercel's dashboard:
   - `GMAIL_CLIENT_ID`
   - `GMAIL_CLIENT_SECRET`
   - `GMAIL_REDIRECT_URI` (your production callback URL)
   - `CRON_SECRET` (any random string — used to authenticate cron requests)

## Troubleshooting

- **"Access blocked" error**: Make sure your email is added as a test user in the OAuth consent screen
- **Token expired**: The app auto-refreshes tokens. If it fails, click "Connect Gmail" to re-authorize
- **No emails appearing**: Check that the Gmail account receives job-related emails. The classifier filters out non-job emails automatically
