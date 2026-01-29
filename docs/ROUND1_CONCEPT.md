# InsightX AI - Round 1 Concept Document

## Elevator Pitch

> **InsightX AI — Conversational analytics for payments: ask plain English, get precise, explainable answers.**

---

## 1. Problem Statement

Leadership teams in digital payments organizations face a critical challenge: they need quick, accurate answers from transaction data to make informed decisions, but current analytics solutions require either:

- **Technical expertise** (SQL, data science skills) that executives don't have
- **Long wait times** for analysts to prepare reports
- **Static dashboards** that can't answer ad-hoc questions
- **Risk of hallucination** when using generic AI assistants

The result: slow decision-making, reliance on intermediaries, and potential for errors when AI makes up numbers.

---

## 2. Target Users

| User | Pain Point | Value |
|------|-----------|-------|
| **CFO/Finance Leaders** | Need instant metrics for board meetings | Get accurate numbers with methodology |
| **Product Managers** | Want to understand failure patterns | Natural language exploration |
| **Operations Heads** | Track real-time performance | Immediate answers with SQL transparency |
| **Compliance Officers** | Require auditable data queries | Every answer shows the exact query used |

---

## 3. Proposed Solution

InsightX AI is a conversational analytics assistant that:

1. **Accepts natural language queries** about payment transactions
2. **Extracts intent** using Google Gemini with strict schema output
3. **Executes deterministic analysis** using DuckDB (no LLM-generated numbers)
4. **Generates explanations** constrained to computed results only
5. **Maintains session context** for follow-up questions

```
┌─────────────────┐
│   User Query    │
│ "What's the     │
│  failure rate?" │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Intent Extract  │  ◄── Gemini (temp=0)
│ {metric: rate,  │
│  filters: {...}}│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ DuckDB Analysis │  ◄── Deterministic SQL
│ SELECT COUNT... │
│ returns: 3.45%  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Explain Results │  ◄── Gemini (temp=0.2)
│ "Failure rate   │      ONLY uses computed
│  is 3.45%..."   │      numbers
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Response +    │
│   SQL Query +   │
│   Follow-ups    │
└─────────────────┘
```

---

## 4. Key Features

### 🎯 Intent Extraction
- Strict JSON schema output from Gemini
- Supports: metric queries, comparisons, time series, segmentation
- Handles ambiguity with clarification requests

### 📊 Deterministic Analysis
- DuckDB for sub-second aggregations on 250k+ rows
- Pre-built functions: failure_rate, aggregate, compare_segments, time_series
- Every query returns the SQL used for transparency

### 🛡️ Anti-Hallucination Guardrails
- LLM instructed with "—DO NOT MAKE UP NUMBERS—"
- Explanation only receives computed results as input
- If data insufficient: "I can't answer that from available data"

### 💡 Explainability
- Every response includes:
  - Summary line (≤30 words) for executives
  - Key numbers with calculation details
  - Method explanation
  - Actual SQL query (toggleable)
  - Follow-up suggestions

### 🔄 Session Context
- Maintains last 6 conversation turns
- Enables follow-up questions: "Now show by device"
- Redis-swappable for distributed deployment

---

## 5. Tech Stack

| Layer | Technology | Why |
|-------|------------|-----|
| **Frontend** | Next.js + TypeScript + Tailwind | Fast, type-safe, responsive |
| **Backend** | FastAPI + Python 3.11 | Async, fast, Pydantic validation |
| **Database** | DuckDB | OLAP-optimized, in-process, SQL |
| **LLM** | Google Gemini 1.5 Flash | Fast, accurate, structured output |
| **Infra** | Docker + nginx | Production-ready, portable |

---

## 6. Explainability Approach

Every InsightX AI response includes three levels of transparency:

### Level 1: Executive Summary
```
"Failure rate is 3.45% (345 of 10,000 transactions), below the 5% threshold."
```

### Level 2: Numbers with Context
| Metric | Value | Calculation |
|--------|-------|-------------|
| Failure Rate | 3.45% | 345 / 10,000 |
| Total Transactions | 10,000 | COUNT(*) |
| Failed Transactions | 345 | COUNT WHERE status='Failed' |

### Level 3: SQL Transparency
```sql
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN status='Failed' THEN 1 ELSE 0 END) as failed,
    ROUND(100.0 * SUM(CASE WHEN status='Failed' THEN 1 ELSE 0 END) / COUNT(*), 2) as rate
FROM transactions
WHERE timestamp >= '2025-01-01'
```

---

## 7. Mock Screenshots

### Chat Interface
```
┌──────────────────────────────────────────────┐
│  InsightX AI              [New Chat]         │
├──────────────────────────────────────────────┤
│                                              │
│  You: What is the failure rate last week?    │
│                                              │
│  ┌────────────────────────────────────────┐  │
│  │ 📊 Failure rate is 3.45% (345 of      │  │
│  │    10,000 transactions)                │  │
│  │                                        │  │
│  │ ┌──────────────┬──────────────┐        │  │
│  │ │ Failure Rate │    3.45%     │        │  │
│  │ │ Total Txns   │   10,000     │        │  │
│  │ │ Failed       │     345      │        │  │
│  │ └──────────────┴──────────────┘        │  │
│  │                                        │  │
│  │ ▸ View SQL Query                       │  │
│  │                                        │  │
│  │ Try: [Compare by device] [Show trend]  │  │
│  └────────────────────────────────────────┘  │
│                                              │
│  ┌────────────────────────────────────────┐  │
│  │ Ask about your payment data...    [▶]  │  │
│  └────────────────────────────────────────┘  │
└──────────────────────────────────────────────┘
```

---

## 8. Evaluation Metrics

For judges to evaluate:

| Criteria | How We Address It |
|----------|-------------------|
| **Accuracy** | Deterministic SQL, no LLM-computed numbers |
| **Explainability** | SQL shown, method explained, numbers traced |
| **Usability** | Clean chat UI, suggested follow-ups, mobile-ready |
| **Performance** | <6s response time for simple queries |
| **Security** | Env vars for secrets, rate limiting, HTTPS |
| **Completeness** | Full stack: UI, API, tests, Docker, docs |

---

## 9. Implementation Timeline

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| **1. Foundation** | Day 1 | Project skeleton, DuckDB setup |
| **2. Core Logic** | Day 2-3 | Analysis service, LLM layer |
| **3. API & UI** | Day 4-5 | FastAPI endpoints, Next.js chat |
| **4. Polish** | Day 6-7 | Tests, Docker, documentation |

---

## 10. Team Roles

| Role | Responsibilities |
|------|-----------------|
| **Backend Lead** | FastAPI, DuckDB, analysis functions |
| **LLM Engineer** | Gemini integration, prompt engineering |
| **Frontend Dev** | Next.js chat UI, responsive design |
| **DevOps** | Docker, CI/CD, deployment |

---

## Summary

InsightX AI transforms how leadership interacts with payment data:

✅ **Natural language** → No SQL skills required  
✅ **Deterministic** → No hallucinated numbers  
✅ **Explainable** → SQL shown for every answer  
✅ **Production-ready** → Docker, tests, CI/CD included

---

*InsightX AI — Because leaders shouldn't wait for reports.*
