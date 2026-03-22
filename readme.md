# ⚖️ AI-Grievance Redressal and Escalation System using NLP and Automated Workflow Management

**CVR College of Engineering** (UGC Autonomous · NAAC 'A' Grade)  
**Department of CSE (AI & ML)** | B.Tech CSE(AI&ML) | III Year II Sem  
**Industry Oriented Major Project (IOMP) — Batch 16**

---

### 👥 Team

| Name | Roll Number |
|---|---|
| Thota Tejaswini | 23B81A66J5 |
| Yanala Indhu | 23B81A66E6 |
| Almareddy Srinidhi | 23B81A66J0 |

**Supervisor:** Mr. J. Phani Prasad, Sr. Asst. Prof., Dept. of CSE (AI&ML)

---

## 🎯 Project Overview

An AI-powered Grievance Redressal System that allows employees to submit workplace grievances in natural language. The system automatically classifies grievances by **category** and **priority** using NLP, routes them through a **2-level escalation hierarchy**, and enforces a **24-hour SLA** through an automated background escalation engine — completely independent of user activity.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Language** | Python 3.9+ |
| **Frontend** | Streamlit |
| **Charts & Visualisation** | Plotly |
| **NLP — Vectorisation** | TF-IDF (scikit-learn) |
| **NLP — Classification** | Cosine Similarity (scikit-learn) |
| **NLP — Text Processing** | NLTK (tokenisation, lemmatisation, stopword removal) |
| **Priority Detection** | Keyword Matching (rule-based, raw + preprocessed) |
| **Database** | Supabase (PostgreSQL) |
| **DB Client** | Supabase Python SDK |
| **Data Tables** | Pandas |
| **Auto-Escalation** | Python background scheduler (time module) |
| **Authentication** | SHA-256 password hashing + Streamlit session state |
| **Platform** | Windows / Linux / macOS |

---

## 📁 Project Structure

```
iomp/
│
├── app.py                    ← Streamlit main application (all pages & UI)
├── classifier.py             ← NLP pipeline (TF-IDF + Cosine Similarity + keyword priority)
├── supabase_client.py        ← Supabase PostgreSQL connection
├── escalation_scheduler.py   ← Standalone 24h auto-escalation background engine
├── schema.sql                ← PostgreSQL schema (run once in Supabase SQL Editor)
├── escalation.log            ← Auto-generated log of all escalation events
└── README.md                 ← This file
```

---

## 🚀 Setup & Run

### Step 1: Install dependencies
```bash
pip install streamlit supabase plotly pandas scikit-learn nltk
```

### Step 2: Set up Supabase
1. Go to supabase.com and create a free project
2. Open SQL Editor → paste and run contents of schema.sql
3. Copy your Project URL and anon key from Project Settings → API

### Step 3: Configure supabase_client.py
```python
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-anon-key"
```

### Step 4: Run the app

**Terminal 1 — Web App:**
```bash
streamlit run app.py
```
Opens at: http://localhost:8501

**Terminal 2 — Auto-Escalation Scheduler:**
```bash
python escalation_scheduler.py
```

> Both terminals must run simultaneously for auto-escalation to work.

---

## 📱 App Pages

| Role | Tab | Features |
|---|---|---|
| 👤 Employee | My Grievances | View all submitted grievances with status, priority, level badges |
| | Track Grievances | Pie charts, timeline, individual lifecycle flowchart |
| | Submit New | AI chatbot — type grievance, get instant category + priority prediction |
| 🟦 HR Manager | Manage Grievances | Review, update status, add notes, enforce priority-based rules |
| | Analytics & Insights | KPI cards, charts, gauges, filterable grievance table |
| 🟥 Dept Head | Final Decisions | Resolve or Close escalated grievances |
| | Analytics & Insights | Organisation-wide analytics dashboard |

---

## 🤖 AI / NLP Features

### 1. Grievance Classifier (classifier.py)

**Algorithm:** TF-IDF Vectorisation + Cosine Similarity

```
Raw Text → Preprocess → TF-IDF Vector → Cosine Similarity → Category + Confidence Score
```

**Preprocessing steps:**
- Lowercase conversion
- Punctuation removal
- NLTK tokenisation
- Stopword removal
- WordNet lemmatisation

**Output Categories:**

| Category | Example Grievances |
|---|---|
| HR & Payroll | Salary issues, leave, appraisal, transfer |
| IT & Systems | Laptop not working, network issues, software access |
| Finance & Reimbursement | Expense claims, payment pending, wrong deductions |
| Facilities & Infrastructure | Office maintenance, AC, parking, cafeteria |
| Management & Policy | Unfair treatment, workload, toxic environment |
| Legal & Compliance | Harassment, fraud, contract breach |

---

### 2. Priority Detector (Rule-Based NLP)

Checks raw text before preprocessing to preserve multi-word phrases:

| Priority | Triggered By |
|---|---|
| 🔴 High | salary not credited, payment pending, harassment, threat, illegal, fraud, urgent |
| 🟡 Medium | delay, broken, not working, leave rejected, attendance issue, unfair |
| 🟢 Low | General queries not matching above patterns |

---

### 3. Auto-Escalation Engine (escalation_scheduler.py)

```
Scheduler starts → runs every 15 minutes
        ↓
Fetch all Level 1 grievances (Pending / In Progress)
        ↓
Calculate age = current_time − created_at
        ↓
If age ≥ 24 hours:
   → status           = "Escalated"
   → escalation_level = 2
   → admin_notes     += "⚡ Auto-escalated: No HR action within 24h"
   → log to escalation.log
```

---

## 📊 Database Schema

### users table
| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| name | text | Full name |
| email | text | Unique login email |
| password_hash | text | SHA-256 hashed password |
| role | text | employee / hr_admin / senior_admin |
| created_at | timestamptz | Registration timestamp |

### grievances table
| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| owner_email | text | FK → users.email |
| text | text | Raw grievance text submitted by employee |
| category | text | AI-classified category |
| priority | text | Low / Medium / High |
| status | text | Pending / In Progress / Escalated / Resolved / Closed |
| escalation_level | integer | 1 = HR Manager, 2 = Department Head |
| admin_notes | text | Notes added by HR or Dept Head |
| created_at | timestamptz | Grievance submission timestamp |

---

## 🔐 Roles & Permissions

| Feature | Employee | HR Manager | Dept Head |
|---|---|---|---|
| Submit grievance (chatbot) | ✅ | ❌ | ❌ |
| View own grievances | ✅ | ❌ | ❌ |
| Track grievance lifecycle | ✅ | ❌ | ❌ |
| View all Level 1 grievances | ❌ | ✅ | ❌ |
| View all Level 2 grievances | ❌ | ❌ | ✅ |
| Resolve Low / Medium priority | ❌ | ✅ | ✅ |
| Resolve High priority | ❌ | ❌ | ✅ |
| Manually escalate to Dept Head | ❌ | ✅ | ❌ |
| Analytics & Insights dashboard | ❌ | ✅ | ✅ |

---

## ⚡ Escalation Policy

| Scenario | Action |
|---|---|
| HR resolves Low/Medium | Status → Resolved (Level 1) |
| HR escalates High priority | Status → Escalated, Level → 2 |
| No HR action within 24 hours | Auto-escalated by scheduler → Level 2 |
| Dept Head resolves | Status → Resolved / Closed (Final) |

---

## 🗺️ Grievance Lifecycle

```
Employee Submits Grievance
          ↓
       Pending
          ↓
   In Progress  (HR Manager reviews)
       ↓                    ↓                      ↓
 (Low/Medium)         (High priority)        (No action in 24h)
  Resolved ✅          Escalated 🚨  ←────── Auto-Escalated ⚡
                            ↓
                  Department Head reviews
                       ↓           ↓
                  Resolved ✅   Closed 🔒
```

---

## 🔭 Future Scope

- Email / SMS notifications on escalation events
- NLP upgrade to transformer-based models (BERT) for higher accuracy
- Integration with HRMS / ERP systems
- Mobile application
- Voice-based grievance submission
- Department-wise report export to PDF / Excel

---

## 📌 Hardware Requirements

| Component | Requirement |
|---|---|
| Processor | Intel i5 or above |
| RAM | Minimum 8 GB |
| Storage | 10 GB free disk space |
| Internet | Required (Supabase cloud DB) |

---


*AI-Grievance Redressal and Escalation System · CVR College of Engineering · IOMP Batch 16*