-- =========================
-- EXTENSIONS
-- =========================
create extension if not exists pgcrypto;

-- =========================
-- TABLES
-- =========================

create table if not exists public.user_profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  email text,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.itineraries (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  destination text not null,
  number_of_days integer not null check (number_of_days between 1 and 10),
  trip_start date,
  itinerary_type text not null,
  budget text not null check (budget in ('Low', 'Medium', 'High')),
  title text not null,
  summary text,
  status text not null default 'saved' check (status in ('saved')),
  source_prompt jsonb not null,
  current_version integer not null default 1 check (current_version >= 1),
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.itinerary_versions (
  id uuid primary key default gen_random_uuid(),
  itinerary_id uuid not null references public.itineraries (id) on delete cascade,
  version_number integer not null check (version_number >= 1),
  itinerary_json jsonb not null,
  created_at timestamptz not null default timezone('utc', now()),
  unique (itinerary_id, version_number)
);

create table if not exists public.itinerary_messages (
  id uuid primary key default gen_random_uuid(),
  itinerary_id uuid not null references public.itineraries (id) on delete cascade,
  role text not null check (role in ('user', 'assistant')),
  content text not null,
  created_at timestamptz not null default timezone('utc', now())
);

-- =========================
-- ALTER TABLE (SAFE ORDER)
-- =========================

alter table public.itineraries
  add column if not exists client_request_id text;

-- =========================
-- INDEXES
-- =========================

create index if not exists itineraries_user_id_updated_at_idx
  on public.itineraries (user_id, updated_at desc);

create unique index if not exists itineraries_user_id_client_request_id_uidx
  on public.itineraries (user_id, client_request_id)
  where client_request_id is not null;

create index if not exists itinerary_versions_itinerary_id_version_number_idx
  on public.itinerary_versions (itinerary_id, version_number desc);

create index if not exists itinerary_messages_itinerary_id_created_at_idx
  on public.itinerary_messages (itinerary_id, created_at asc);

-- =========================
-- RLS ENABLE
-- =========================

alter table public.user_profiles enable row level security;
alter table public.itineraries enable row level security;
alter table public.itinerary_versions enable row level security;
alter table public.itinerary_messages enable row level security;

-- =========================
-- POLICIES (IDEMPOTENT)
-- =========================

drop policy if exists "Users can view their own profile" on public.user_profiles;
create policy "Users can view their own profile"
  on public.user_profiles
  for select
  using (auth.uid() = id);

drop policy if exists "Users can insert their own profile" on public.user_profiles;
create policy "Users can insert their own profile"
  on public.user_profiles
  for insert
  with check (auth.uid() = id);

drop policy if exists "Users can update their own profile" on public.user_profiles;
create policy "Users can update their own profile"
  on public.user_profiles
  for update
  using (auth.uid() = id)
  with check (auth.uid() = id);

drop policy if exists "Users can manage their own itineraries" on public.itineraries;
create policy "Users can manage their own itineraries"
  on public.itineraries
  for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

drop policy if exists "Users can manage versions of their own itineraries" on public.itinerary_versions;
create policy "Users can manage versions of their own itineraries"
  on public.itinerary_versions
  for all
  using (
    exists (
      select 1
      from public.itineraries
      where itineraries.id = itinerary_versions.itinerary_id
        and itineraries.user_id = auth.uid()
    )
  )
  with check (
    exists (
      select 1
      from public.itineraries
      where itineraries.id = itinerary_versions.itinerary_id
        and itineraries.user_id = auth.uid()
    )
  );

drop policy if exists "Users can manage messages of their own itineraries" on public.itinerary_messages;
create policy "Users can manage messages of their own itineraries"
  on public.itinerary_messages
  for all
  using (
    exists (
      select 1
      from public.itineraries
      where itineraries.id = itinerary_messages.itinerary_id
        and itineraries.user_id = auth.uid()
    )
  )
  with check (
    exists (
      select 1
      from public.itineraries
      where itineraries.id = itinerary_messages.itinerary_id
        and itineraries.user_id = auth.uid()
    )
  );