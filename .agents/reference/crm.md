# CRM Reference

## Overview
Flask app for lead management. Deployed on Railway with PostgreSQL.

## Local Development

```bash
cd crm
pip install -r requirements.txt
python app.py
# Opens at http://localhost:5000
```

## Database

- **Production**: PostgreSQL on Railway (via `DATABASE_URL`)
- **Local**: SQLite at `crm/data/leads.db`

## Lead Farming Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `farmer.py` | Parse 2GIS for leads without websites | `python farmer.py "Краснодар" "ремонт квартир"` |
| `farmer_avito.py` | Parse Avito | `python farmer_avito.py` |
| `clicker.py` | Interactive 2GIS clicker | `python clicker.py` |
| `parser.py` | Parse clipboard from 2GIS | Copy page, run `python parser.py` |

## Data Location

```
crm/data/
├── leads.db              # SQLite database
└── archive/              # Old CSV exports
```

## API Endpoints

- `GET /` — Lead list with filters
- `GET /api/leads` — JSON export
- `POST /api/leads/<id>/status` — Update lead status

---

*Updated: 2026-01-20*
