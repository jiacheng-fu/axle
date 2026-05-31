# CarScout — Supabase setup (accounts + saved cars)

One-time setup so sign-in (Google) and saved/hearted cars work. ~10 minutes.

## 1. Create the Supabase project
1. Go to https://supabase.com → sign in → **New project**.
2. Pick a name/region, set a database password (save it somewhere), create it.
3. When it's ready, open **Settings → API** and copy:
   - **Project URL** → `VITE_SUPABASE_URL`
   - **anon public** key → `VITE_SUPABASE_ANON_KEY`
4. Paste both into `frontend/.env` (it's git-ignored). Restart `npm run dev`.

## 2. Create the table
- Dashboard → **SQL Editor → New query** → paste the contents of
  [`supabase/migrations/0001_saved_vehicles.sql`](../supabase/migrations/0001_saved_vehicles.sql)
  → **Run**. This creates `saved_vehicles` with Row-Level Security (each user only
  sees their own saved cars).

## 3. Google sign-in (OAuth)
**a. Google Cloud — create an OAuth client**
1. https://console.cloud.google.com → create/select a project.
2. **APIs & Services → OAuth consent screen** → External → fill app name + your email → save. Add yourself under **Test users** (so you can sign in while it's unverified).
3. **APIs & Services → Credentials → Create credentials → OAuth client ID** → type **Web application**.
4. **Authorized redirect URIs** → add (from Supabase → Authentication → Providers → Google, it shows the exact callback):
   ```
   https://<your-project-ref>.supabase.co/auth/v1/callback
   ```
5. (Optional) **Authorized JavaScript origins**: `http://localhost:5173`.
6. Create → copy the **Client ID** and **Client secret**.

**b. Supabase — enable Google**
1. Dashboard → **Authentication → Providers → Google** → enable.
2. Paste the **Client ID** and **Client secret** → save.

**c. Allow the app's redirect**
1. Dashboard → **Authentication → URL Configuration**:
   - **Site URL**: `http://localhost:5173`
   - **Redirect URLs**: add `http://localhost:5173` (and your deployed URL later).

That's it. Start the app, click **Sign in with Google**, and hearts/saved cars will work.

> Notes
> - The anon key is meant to be public; RLS is what protects the data.
> - No backend changes are involved — the React app talks to Supabase directly.
> - If `frontend/.env` has no Supabase values, the app still runs; sign-in is just disabled.
