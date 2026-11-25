-- Axle — saved ("hearted") vehicles.
-- One row per (user, vehicle). `car` stores a snapshot of the listing so the
-- saved list still renders and compares even if the live listing changes.
-- Run this in the Supabase dashboard: SQL Editor -> New query -> paste -> Run.

create table if not exists public.saved_vehicles (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid not null references auth.users (id) on delete cascade,
  vin         text not null,
  car         jsonb not null,
  created_at  timestamptz not null default now(),
  unique (user_id, vin)
);

create index if not exists saved_vehicles_user_idx
  on public.saved_vehicles (user_id, created_at desc);

-- Row-Level Security: each user can only touch their own rows.
alter table public.saved_vehicles enable row level security;

drop policy if exists "saved_select_own" on public.saved_vehicles;
create policy "saved_select_own" on public.saved_vehicles
  for select using (auth.uid() = user_id);

drop policy if exists "saved_insert_own" on public.saved_vehicles;
create policy "saved_insert_own" on public.saved_vehicles
  for insert with check (auth.uid() = user_id);

drop policy if exists "saved_delete_own" on public.saved_vehicles;
create policy "saved_delete_own" on public.saved_vehicles
  for delete using (auth.uid() = user_id);
