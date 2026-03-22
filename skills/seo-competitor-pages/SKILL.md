---
name: seo-competitor-pages
description: >
  Generate SEO-optimized competitor comparison and alternatives pages. Covers
  "X vs Y" layouts, "alternatives to X" pages, feature matrices, schema markup,
  and conversion optimization. Use when user says "comparison page", "vs page",
  "alternatives page", "competitor comparison", or "X vs Y".
---

# Competitor Comparison & Alternatives Pages

## Page Types

### "X vs Y" Comparison Pages
- URL pattern: `/[product-a]-vs-[product-b]/`
- Minimum word count: 1,500
- Unique content: 80%+
- Target keyword: `[Product A] vs [Product B]`

### "Alternatives to X" Pages
- URL pattern: `/alternatives-to-[product]/` or `/[product]-alternatives/`
- Minimum word count: 2,000
- Lists 5-10 alternatives with honest pros/cons
- Target keyword: `[Product] alternatives`, `best [Product] alternatives`

## Required Sections

### Comparison Page
1. **Introduction** — who this comparison is for, key decision factors
2. **Quick comparison table** — side-by-side features, pricing, ratings
3. **Detailed breakdown** — each key feature compared in depth
4. **Pricing comparison** — all tiers, free trials, hidden costs
5. **Pros & cons** — for each product, honest and balanced
6. **Use case recommendations** — "choose X if...", "choose Y if..."
7. **Verdict** — clear recommendation with reasoning
8. **FAQ** — common comparison questions

### Alternatives Page
1. **Introduction** — why someone might look for alternatives
2. **Quick comparison table** — all alternatives at a glance
3. **Each alternative** — dedicated section per product (200-300 words)
4. **Summary table** — feature/price matrix
5. **How to choose** — decision framework
6. **FAQ** — common alternatives questions

## Comparison Table Layout

```
| Feature      | Product A | Product B |
|--------------|:---------:|:---------:|
| Price        | $X/mo     | $Y/mo     |
| Free plan    | ✅        | ❌        |
| Feature 1    | ✅        | ✅        |
| Feature 2    | ✅        | ❌        |
| Rating       | 4.5/5     | 4.2/5     |
```

## Schema Markup

### Product Schema (for each product)
```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Product Name",
  "description": "Brief description",
  "brand": {
    "@type": "Brand",
    "name": "Brand Name"
  },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.5",
    "reviewCount": "1000"
  }
}
```

## Keyword Targeting

### Comparison Intent Patterns
| Pattern | Example | Intent |
|---------|---------|--------|
| `X vs Y` | "Notion vs Confluence" | Comparison |
| `X vs Y pricing` | "Slack vs Teams pricing" | Pricing |
| `X vs Y which is better` | "React vs Vue which is better" | Decision |
| `X alternatives` | "Jira alternatives" | Switching |
| `best X alternatives` | "best Salesforce alternatives" | Discovery |
| `X competitors` | "HubSpot competitors" | Research |

### Title Tag Formulas
- `[A] vs [B]: Full Comparison (2026) | [Site]`
- `[A] vs [B]: Pricing, Features & Which to Choose | [Site]`
- `10 Best [Product] Alternatives in 2026 | [Site]`

## Fairness Guidelines

- **Accuracy**: All claims must be verifiable and current
- **Balance**: Acknowledge your own product's weaknesses if applicable
- **Cite sources**: Link to official pricing pages
- **Date stamp**: Include "Last updated: {date}"
- **No fake reviews**: Don't fabricate ratings or testimonials

## Conversion Optimization

- CTA placement: after verdict section and at page bottom
- Social proof: customer quotes, G2/Capterra ratings
- Trust signals: "updated monthly", data sources cited
- Internal links: to feature pages, pricing, free trial

## DataForSEO Integration (Optional)

If DataForSEO MCP tools are available, use `serp_organic_live_advanced` to check current SERP for comparison queries and identify content gaps vs ranking pages.
