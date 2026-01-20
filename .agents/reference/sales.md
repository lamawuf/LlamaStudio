# Sales Reference

## Message Generator

```bash
cd sales
python generator.py ../crm/data/archive/leads_master.csv cold_first
python generator.py ../crm/data/archive/leads_master.csv cold_short 10
```

## Message Templates (`sales/templates/`)

| Template | When to Use |
|----------|-------------|
| `cold_first.txt` | First contact, detailed offer |
| `cold_short.txt` | Mass outreach, brief |
| `follow_up.txt` | 2-3 days after first message |
| `with_site_analysis.txt` | If they have existing site |

## Placeholders

```
{name}           — Company name
{phone}          — Phone
{city}           — City
{category}       — Niche
{portfolio_link} — Example site URL
{whatsapp_link}  — wa.me link
```

## Sales Scripts

Located in `scripts/`:
- `sales_script.md` — Cold call script
- `sales_flow.mermaid` — Visual call flow
- `seo_script.md` — SEO checklist for clients

---

*Updated: 2026-01-20*
