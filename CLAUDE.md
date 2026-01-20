# LlamaStudio

Бизнес по продаже сайтов для малого бизнеса.

## When to Read

| Need | Document |
|------|----------|
| Create new site | `.agents/reference/templates.md` |
| CRM, parse leads | `.agents/reference/crm.md` |
| Outreach messages | `.agents/reference/sales.md` |
| Pricing, business | `.agents/reference/pricing.md` |
| Skills (commands) | `.claude/project.skills.md` |

## Structure

```
LlamaStudio/
├── crm/                    # CRM app + lead farming
│   ├── app.py              # Flask app (Railway deploy)
│   ├── farmer.py           # 2GIS parser
│   └── data/leads.db       # SQLite database
├── sales/                  # Outreach generator
├── templates/              # Site templates
│   ├── base/               # Raw themes (7)
│   └── portfolio/          # Live examples (8)
├── scripts/                # Sales scripts
└── docs/                   # Plans, architecture
```

## Quick Reference

- **Price**: 5,000₽ (50% prepay)
- **Timeline**: 1 day
- **Cities**: Краснодар, Москва, Сочи
- **Niches**: Ремонт, потолки, авто, красота

## Portfolio URLs

| Site | URL |
|------|-----|
| site1 | privozzz-remont.vercel.app |
| site2 | site2-remont.vercel.app |
| site3 | site3-remont.vercel.app |
| site4 | site4-remont.vercel.app |
| site5 | site5-remont.vercel.app |
| site6 | site6-remont.vercel.app |
| multipage | tech-komfort.vercel.app |

---

*Updated: 2026-01-20*
