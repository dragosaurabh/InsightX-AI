# Demo Video Recording Instructions

This document provides a script and instructions for recording the InsightX AI demo video (3-5 minutes).

## Prerequisites

- InsightX AI running locally or deployed
- Screen recording software (OBS, Loom, or QuickTime)
- Microphone for voiceover

## Video Structure

### 1. Introduction (30 seconds)

**Script:**
> "Welcome to InsightX AI — a conversational analytics assistant for digital payments.
> 
> Leadership teams often need quick answers from transaction data, but they don't want to write SQL or wait for analyst reports.
> 
> InsightX AI lets you ask questions in plain English and get precise, explainable answers — with no risk of AI making up numbers."

**Visuals:**
- Show the InsightX AI landing page
- Logo and tagline visible

---

### 2. First Query Demo (60 seconds)

**Script:**
> "Let's start with a simple question. I'll ask: 'What is the overall failure rate in the last 30 days?'"

**Actions:**
1. Type the query in the chat input
2. Press Enter
3. Wait for response

**Script (while waiting):**
> "Notice the typing indicator — the system is extracting my intent, running a DuckDB query, and generating an explanation."

**Script (after response):**
> "The response includes:
> - A summary line written for executives
> - The exact numbers with calculation details
> - And if I click 'View SQL Query', I can see exactly how this was computed.
> 
> This transparency is key — every number is traceable."

---

### 3. Comparison Query (60 seconds)

**Script:**
> "Now let's try a comparison. I'll ask: 'Compare failure rate on Android vs iOS in Maharashtra.'"

**Actions:**
1. Type and send the comparison query
2. Show the response with chart

**Script:**
> "InsightX AI understands I want to compare two segments. It shows me:
> - The failure rate for each device type
> - The difference between them
> - A bar chart for visual comparison
> 
> And notice the suggested follow-ups at the bottom — these are clickable shortcuts for natural next questions."

---

### 4. Follow-up Question (45 seconds)

**Script:**
> "One of the most powerful features is session context. I'll click on a follow-up suggestion, or ask my own: 'Now show the trend over time.'"

**Actions:**
1. Click a suggested follow-up OR type a follow-up
2. Show the line chart response

**Script:**
> "The system remembers our conversation context. It knows we were discussing Android vs iOS, so it shows the time series for those segments.
> 
> This makes exploratory analysis feel natural — just like talking to a data analyst."

---

### 5. Anti-Hallucination Demo (45 seconds)

**Script:**
> "What if I ask something the data can't answer? Let me try: 'What's the customer satisfaction score?'"

**Actions:**
1. Type the impossible query
2. Show the clarification response

**Script:**
> "Instead of making up a number, InsightX AI tells me it can't answer that from the available data, and suggests related metrics it CAN provide.
> 
> This is crucial for trust — leaders need to know they can rely on these answers for real decisions."

---

### 6. Architecture Overview (30 seconds)

**Script:**
> "Under the hood, InsightX AI uses:
> - Google Gemini for intent extraction and explanation
> - DuckDB for fast, deterministic SQL analysis
> - A strict separation: the LLM never computes numbers — it only explains pre-computed results
> 
> The result: speed, accuracy, and explainability."

**Visuals:**
- Show the architecture diagram from README or ROUND1_CONCEPT.md

---

### 7. Conclusion (30 seconds)

**Script:**
> "InsightX AI brings conversational analytics to payment data:
> - Ask in plain English
> - Get precise, traceable answers
> - No hallucination, no SQL required
> 
> Thank you for watching. Visit our GitHub repo to try it yourself!"

**Visuals:**
- Show the GitHub repo URL
- Final InsightX AI logo

---

## Recording Tips

1. **Resolution**: 1920x1080 minimum
2. **Font size**: Increase browser zoom to 125% for readability
3. **Clean desktop**: Hide unnecessary icons/notifications
4. **Speak clearly**: Pause between sections
5. **Show mouse movements**: Viewers follow your cursor

## Post-Production

1. Add intro/outro cards with logo
2. Add captions if time permits
3. Export as MP4, H.264 codec
4. Target file size: <100MB

## Sample Queries to Use

1. "What is the overall failure rate?"
2. "Compare Android vs iOS"
3. "Show average amount by category"
4. "What are the top failure codes?"
5. "Now show by state" (follow-up)
6. "What's the customer satisfaction?" (anti-hallucination demo)

---

*Recording time target: 4 minutes*
