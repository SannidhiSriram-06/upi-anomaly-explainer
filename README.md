# UPI Transaction Anomaly Explainer

> Multi-agent AI system that detects, explains, and adversarially validates UPI payment fraud — deployed on Hugging Face Spaces.

**Live Demo**: [https://huggingface.co/spaces/Sannidhi-Sriram/upi-anomaly-explainer](https://huggingface.co/spaces/Sannidhi-Sriram/upi-anomaly-explainer)

---

## What It Does

Upload a CSV of UPI transactions. Three specialized AI agents sequentially analyze it:

1. **Analyst** — flags each transaction as HIGH / MEDIUM / LOW risk with a reason
2. **Explainer** — rewrites those findings in plain English for non-technical readers
3. **Red Team** — adversarially challenges every flag and issues CONFIRM / DOWNGRADE / DISMISS verdicts

The output is a full fraud report rendered in a dark cyberpunk dashboard with risk stats, a donut chart, a transaction table, and multi-format export.

---

## Architecture

```
CSV Upload
    │
    ▼
heuristics.py ──── Rule-based pre-filter
(velocity, amount spikes, odd hours)
    │
    ▼ flagged transactions
crew.py (Process.sequential)
    │
    ├─► agents/analyst.py   ──→ TXN_ID | HIGH/MEDIUM/LOW | reason
    │         │
    ├─► agents/explainer.py ──→ plain-English explanation blocks
    │         │ (context= analyst output)
    └─► agents/redteam.py   ──→ CONFIRM/DOWNGRADE/DISMISS + assessment
              (context= analyst + explainer outputs)
    │
    ▼
app.py (Flask) → JSON response → index.html (dashboard UI)
```

All agents share context via CrewAI's `task.context` chaining — no redundant API calls.

---

## Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Agent Framework | CrewAI | 1.14.3 |
| LLM Backend | Groq API — LLaMA 3.1 8B Instant | — |
| LLM Routing | LiteLLM | 1.83.0 (unpinned) |
| Web Server | Flask | 3.1.3 |
| Data Processing | pandas | 3.0.2 |
| Numerical | numpy | 2.4.4 |
| Env Management | python-dotenv | 1.2.2 |
| Container | Docker (python:3.11-slim) | — |
| Deployment | Hugging Face Spaces (Docker SDK) | — |
| Language | Python 3.13 (local) / 3.11 (container) | — |

---

## Project Structure

```
upi-anomaly-explainer/
├── agents/
│   ├── analyst.py          # Senior UPI Fraud Analyst agent
│   ├── explainer.py        # Customer Communication Specialist agent
│   └── redteam.py          # Adversarial Fraud Validation agent
├── crew.py                 # Sequential orchestration + context chaining
├── heuristics.py           # Rule-based pre-filter (no LLM)
├── app.py                  # Flask backend
├── templates/
│   └── index.html          # Cyberpunk dashboard UI
├── sample_data/
│   └── transactions.csv    # 15-row mock UPI dataset
├── Dockerfile
├── requirements.txt
└── .gitignore
```

---

## API Reference

### `POST /analyze`

Accepts a CSV file, runs the full agent pipeline, returns a JSON fraud report.

**Request**: `multipart/form-data`, field name `file` (CSV, max 2MB)

**Required CSV columns**: `transaction_id`, `amount`, `timestamp`, `sender_upi`, `receiver_upi`

**Response 200**:
```json
{
  "total_transactions": 15,
  "flagged_count": 10,
  "analyst": "TXN001 | HIGH | velocity spike detected...\nTXN002 | HIGH | ...",
  "explainer": "---\nTransaction: TXN001\nRisk: HIGH\nExplanation: ...",
  "redteam": "TXN001 | HIGH | DOWNGRADE | ...\n\nOverall assessment: ..."
}
```

**Response 400 / 500**:
```json
{ "error": "description" }
```

---

## Sample Data

`sample_data/transactions.csv` contains 15 mock UPI transactions. 10 of 15 are flagged by heuristics in testing. Use it to verify the pipeline end-to-end.

```csv
transaction_id,amount,timestamp,sender_upi,receiver_upi
TXN001,49500.00,2024-01-15 02:34:00,user1@upi,merchant99@upi
TXN002,49800.00,2024-01-15 02:35:00,user1@upi,merchant99@upi
...
```

---

## Local Setup

### Prerequisites
- Python 3.11+
- A [Groq API key](https://console.groq.com) (free tier)

### Steps

```bash
# Clone the repo
git clone https://github.com/SannidhiSriram-06/upi-anomaly-explainer.git
cd upi-anomaly-explainer

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

**.env**:
```
GROQ_API_KEY=your_groq_key_here
CREWAI_TRACING_ENABLED=false
```

```bash
# Run locally
PORT=8080 python3 app.py
# Open http://localhost:8080
```

---

## Docker

```bash
# Build
docker build -t upi-anomaly-explainer .

# Run
docker run -p 7860:7860 -e GROQ_API_KEY=your_key -e CREWAI_TRACING_ENABLED=false upi-anomaly-explainer
```

**Dockerfile**:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 7860
ENV PORT=7860
CMD ["python3", "app.py"]
```

---

## Deploying to Hugging Face Spaces

1. Create a new Space on Hugging Face — SDK: **Docker**
2. Add `GROQ_API_KEY` as a Space secret in Settings
3. Add `CREWAI_TRACING_ENABLED` = `false` as a Space secret
4. Add the HF Space as a git remote and push:

```bash
git remote add space https://huggingface.co/spaces/YOUR_HF_USERNAME/upi-anomaly-explainer
git push space main
```

Build logs are visible in the HF Space UI. Cold start takes ~60 seconds on first run.

---

## UI Features

- Dark cyberpunk dashboard — scanlines, grid background, neon accents
- Fonts: Rajdhani (display) + Share Tech Mono (monospace labels)
- **Stat cards**: total transactions, flagged count, flag rate %, session run count
- **Donut chart**: HIGH / MEDIUM / LOW / CLEAN risk distribution
- **Transaction table**: TXN ID | Risk badge | Verdict badge | Reason
- **Agent panels**: Analyst (cyan), Explainer (yellow), Red Team (red)
- **History tab**: all session runs, expandable with full outputs + table, badge counter
- **Export**: TXT, CSV, JSON, Markdown, HTML — all generated client-side, no backend storage

---

## Key Engineering Decisions

**Python 3.11 in container, 3.13 locally**
HF Spaces Docker is more stable on 3.11. LiteLLM and CrewAI have fewer conflicts on 3.11. Local dev uses 3.13 — only the container targets 3.11.

**Unpinned litellm**
`litellm==1.83.14` pins `pydantic==2.12.5`, which conflicts with `crewai==1.14.3`'s `pydantic~=2.11.9`. Leaving litellm unpinned lets pip resolve to 1.83.0, which is compatible with both.

**Minimal requirements.txt**
A full `pip freeze` from the local 3.13 venv produced version conflicts in the 3.11 Docker build. Switched to listing only direct dependencies — pip resolves the rest correctly in the target environment.

**CREWAI_TRACING_ENABLED=false**
CrewAI's execution trace prompt (`Would you like to view your execution traces? [y/N]`) is interactive and hangs in non-TTY Docker environments. Disabling it is mandatory for containerized deployment.

**Heuristics pre-filter**
Rule-based pre-processing (velocity checks, amount spikes, odd-hour flags) reduces the number of transactions sent to the LLM, keeping usage comfortably within Groq's free tier.

**Client-side exports**
All five download formats (TXT, CSV, JSON, Markdown, HTML) are generated in browser JavaScript. No backend storage, no extra endpoints, no privacy concerns.

---

## Requirements

```
Flask==3.1.3
crewai==1.14.3
groq==1.2.0
litellm
python-dotenv==1.2.2
pandas==3.0.2
numpy==2.4.4
```

---

## License

MIT
