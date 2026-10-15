# LangGraph Customer Support & Refund Agent — CSV Edition

Uses **Groq + LangGraph + FastAPI**, with `data/orders.csv` for orders and `data/refunds.csv` for a demo refund ledger. **No SQLite.**

## Windows PowerShell setup

```powershell
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and set `GROQ_API_KEY`. Run:

```powershell
uvicorn main:app --reload
```

Open http://127.0.0.1:8000/docs.

## Examples

POST `/support`:

```json
{"thread_id":"demo-1","message":"Please refund ORD-1002"}
```

`ORD-1002` costs $120 and triggers human approval. Resume by POSTing to `/review/demo-1`:

```json
{"approved":true}
```

Other scenarios: `ORD-1001` ($75, auto-approved); `ORD-1003` ($350, human review); `ORD-1004` (expired refund window); `ORD-1005` (already refunded). Use a new `thread_id` per request.

## Data files

On first server startup, the project automatically creates 20 demo orders in `data/orders.csv` and an empty `data/refunds.csv`. Subsequent startups preserve edits and refunds. To reset, stop the server, delete the two CSV files, and restart.

## Important limitations

- LangGraph uses `InMemorySaver` for checkpoints: **pending approvals are lost on server restart**. CSV data remains.
- CSV writes are protected by a Python thread lock only within a single process. Run one server worker; do not edit the CSV while the server is running.
- CSV storage is educational and is **not transactional** across multiple files. A crash between writing the refund ledger and updating the order may leave inconsistent records, though the ledger helps block duplicate refunds.
- The demo only records refunds locally. No real payments are made.
- The review endpoint has no authentication; add it before any deployment.
