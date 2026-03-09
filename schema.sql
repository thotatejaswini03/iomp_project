-- ============================================================
-- Grievance Redressal System v2 — Updated Schema
-- IMPORTANT: Run this in Supabase Dashboard → SQL Editor
-- ============================================================

drop table if exists grievances;
drop table if exists users;

-- 3 roles: employee, hr_admin, senior_admin
create table users (
  id            uuid primary key default gen_random_uuid(),
  name          text not null,
  email         text not null unique,
  password_hash text not null,
  role          text not null check (role in ('employee', 'hr_admin', 'senior_admin')),
  created_at    timestamptz default now()
);

create table grievances (
  id               uuid primary key default gen_random_uuid(),
  owner_email      text not null references users(email) on delete cascade,
  text             text not null,
  category         text not null default 'General',
  priority         text not null check (priority in ('Low', 'Medium', 'High')) default 'Low',
  status           text not null check (
                     status in ('Pending', 'In Progress', 'Escalated', 'Resolved', 'Closed')
                   ) default 'Pending',
  escalation_level integer not null default 1 check (escalation_level in (1, 2)),
  admin_notes      text,
  created_at       timestamptz default now()
);

create index idx_grievances_owner    on grievances(owner_email);
create index idx_grievances_status   on grievances(status);
create index idx_grievances_priority on grievances(priority);
create index idx_grievances_level    on grievances(escalation_level);
