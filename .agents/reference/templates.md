# Site Templates Reference

## Template Types

### Base Templates (`templates/base/`)
Raw theme designs without client data:
- `corporate/` — Dark blue, professional
- `minimal/` — Light, clean
- `warm/` — Earth tones, friendly
- `bold/` — Bright accents, energetic
- `dark/` — Dark mode, modern
- `cyberpunk/` — Neon, futuristic
- `premium/` — Elegant, luxury

### Portfolio Sites (`templates/portfolio/`)
Live deployed examples:

| Site | Style | URL | Best For |
|------|-------|-----|----------|
| site1 | Corporate | privozzz-remont.vercel.app | Ремонт, B2B |
| site2 | Minimal | site2-remont.vercel.app | Салоны, медицина |
| site3 | Vibrant | site3-remont.vercel.app | Автосервис |
| site4 | Classic | site4-remont.vercel.app | Универсальный |
| site5 | Modern | site5-remont.vercel.app | IT, стартапы |
| site6 | Premium | site6-remont.vercel.app | Рестораны, отели |
| multipage | Professional | tech-komfort.vercel.app | Многостраничник |

## Creating New Site

1. **Copy template** (never edit originals!):
```bash
cp -r templates/portfolio/site{N} templates/portfolio/{company-slug}
```

2. **Edit config.json** with client data

3. **Preview locally**:
```bash
cd templates/portfolio/{company-slug} && python3 -m http.server 8080
```

4. **Deploy**:
```bash
vercel --prod
```

## config.json Structure

```json
{
  "company": "Company Name",
  "phone": "+7 XXX XXX-XX-XX",
  "city": "Краснодар",
  "niche": "repair|ceilings|auto|beauty"
}
```

---

*Updated: 2026-01-20*
