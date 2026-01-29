# InsightX AI

> **Conversational analytics for payments: ask plain English, get precise, explainable answers.**

InsightX AI is a production-ready conversational analytics platform for digital payment data. It enables leadership teams to query transaction data using natural language and receive accurate, explainable insights backed by deterministic analysis.

## ✨ Features

- **Natural Language Queries**: Ask questions in plain English
- **Intent Extraction**: Powered by Google Gemini for accurate understanding
- **Deterministic Analysis**: DuckDB-backed for fast, precise computations
- **Explainability**: Every response includes SQL used, method explanation, and key statistics
- **Session Context**: Maintains conversation history for follow-ups
- **No Hallucination**: LLM uses only computed results - never invents numbers

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────────────────────────────┐
│   Next.js UI    │────▶│              FastAPI Backend             │
│   (Chat Window) │     │                                          │
└─────────────────┘     │  ┌─────────────┐    ┌─────────────────┐  │
                        │  │ LLM Service │    │ Analysis Service│  │
                        │  │  (Gemini)   │    │    (DuckDB)     │  │
                        │  └─────────────┘    └─────────────────┘  │
                        └──────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Google Gemini API key

### 1. Clone and Setup

```bash
git clone https://github.com/your-org/insightx-ai.git
cd insightx-ai

# Copy environment file
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 2. Generate Sample Data

```bash
cd scripts
python ingest_sample_data.py --rows 50000
# Creates: data/sample_transactions_50k.csv
```

### 3. Start Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Update DATA_PATH in .env to point to your CSV
uvicorn app.main:app --reload --port 8000
```

### 4. Start Frontend

```bash
cd frontend/nextjs-app
npm install
npm run dev
```

Open http://localhost:3000 and start asking questions!

## 🐳 Docker Quick Start

```bash
# Generate sample data first
python scripts/ingest_sample_data.py --rows 50000

# Set your API key in .env
echo "GEMINI_API_KEY=your_key_here" > .env

# Start with Docker Compose
docker compose -f infra/docker-compose.yml up --build
```

Access the app at http://localhost:3000

## 📝 Sample Queries

Try these example queries:

1. "What is the overall failure rate in the last 30 days?"
2. "Compare failure rate on Android vs iOS"
3. "Show average transaction amount by category"
4. "What are the top 3 failure codes?"
5. "Provide an executive summary for January 2026"

See [docs/sample_queries.json](docs/sample_queries.json) for 15+ queries with expected responses.

## 🔧 Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | *Required* |
| `GEMINI_MODEL` | Gemini model version | `gemini-1.5-flash` |
| `DATA_PATH` | Path to transaction CSV | `./data/transactions.csv` |
| `FRONTEND_ORIGIN` | Frontend URL for CORS | `http://localhost:3000` |
| `MAX_CONTEXT_TURNS` | Session history length | `6` |
| `RATE_LIMIT_PER_MIN` | LLM calls per minute | `10` |
| `REDIS_URL` | Redis URL (optional) | *In-memory* |

## 🧪 Testing

```bash
cd backend

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_analysis.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

## 📁 Project Structure

```
insightx-ai/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── models/       # Pydantic schemas
│   │   ├── prompts/      # LLM prompt templates
│   │   └── services/     # Business logic
│   ├── tests/            # Unit & integration tests
│   └── Dockerfile
├── frontend/
│   ├── nextjs-app/
│   │   ├── components/   # React components
│   │   ├── lib/          # API client
│   │   └── pages/        # Next.js pages
│   └── Dockerfile
├── infra/
│   ├── docker-compose.yml
│   └── nginx.conf
├── scripts/
│   └── ingest_sample_data.py
└── docs/
    ├── DEPLOY.md
    ├── ROUND1_CONCEPT.md
    └── sample_queries.json
```

## 📚 Documentation

- [Deployment Guide](docs/DEPLOY.md) - Production deployment instructions
- [Round 1 Concept](docs/ROUND1_CONCEPT.md) - Hackathon submission document
- [Security Guidelines](docs/SECURITY.md) - Security best practices

## 🔒 Security

- API keys stored in environment variables only
- CORS restricted to frontend origin
- Rate limiting on API endpoints
- Non-root Docker containers
- Input sanitization on all user inputs

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

Built with ❤️ for the InsightX AI Hackathon
