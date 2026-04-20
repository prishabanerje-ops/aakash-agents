---
name: dev-quality
description: Build production-quality Node.js/Express/React applications with the discipline of a senior developer. Enforces testing, security, modular architecture, and error handling best practices. Use when building new backend APIs, full-stack apps, or refactoring existing code to production standards.
---

This skill guides building production-grade applications with the discipline real developers apply — not just feature completeness, but testability, security, error resilience, and maintainability.

The user provides a feature, API, or application to build. Apply every principle below. Do not skip testing or security steps even when the user doesn't explicitly ask.

---

## Architecture Principles

### Folder Structure
Always separate concerns clearly:
```
backend/
  routes/         # One file per resource (auth.js, sites.js, reports.js)
  services/       # Business logic, DB queries, external API calls
  middleware/     # Auth, validation, rate limiting
  db/             # Schema, migrations, connection
  config/         # Environment-aware config
frontend/
  src/
    api/          # Centralized API client (one file, all endpoints)
    components/   # Reusable UI pieces
    pages/        # Route-level components
    context/      # Shared state (auth, sites, theme)
```

Never put business logic in route handlers. Route handlers should: validate input → call service → return response.

### Configuration
- Always use `.env` for secrets — never hardcode
- Always provide `.env.example` with all keys documented (no real values)
- Add `.env` to `.gitignore` immediately — check before first commit
- Use a centralized config object:
```javascript
const config = {
  port: process.env.PORT || 3001,
  jwtSecret: process.env.JWT_SECRET, // no fallback for secrets
  db: { path: process.env.DB_PATH || "./data/app.db" }
};
if (!config.jwtSecret) throw new Error("JWT_SECRET env var required");
```

---

## Security (Non-Negotiable)

Before writing any feature code, set up:

1. **Helmet** for security headers:
```javascript
import helmet from "helmet";
app.use(helmet());
```

2. **Rate limiting** on auth endpoints:
```javascript
import rateLimit from "express-rate-limit";
const authLimiter = rateLimit({ windowMs: 15 * 60 * 1000, max: 20 });
app.use("/api/auth", authLimiter);
```

3. **Input validation** — validate at the route level, never trust req.body:
```javascript
if (!email || !password) return res.status(400).json({ error: "Email and password required" });
if (password.length < 8) return res.status(400).json({ error: "Password must be at least 8 characters" });
try { new URL(url); } catch { return res.status(400).json({ error: "Invalid URL" }); }
```

4. **Parameterized queries** — never string-interpolate SQL:
```javascript
// NEVER: db.query(`SELECT * FROM users WHERE email = '${email}'`)
// ALWAYS:
db.prepare("SELECT * FROM users WHERE email = ?").get(email);
```

5. **Secret checklist before commit:**
   - [ ] `.env` in `.gitignore`
   - [ ] No hardcoded API keys, passwords, or tokens in source
   - [ ] JWT secret has no fallback string
   - [ ] Service account files excluded from git

---

## Error Handling

Every error should tell you: **what failed, why, and where**.

```javascript
// BAD — too vague
catch (err) { res.status(500).json({ error: err.message }); }

// GOOD — contextual
catch (err) {
  console.error(`[audit] Failed to audit ${url}:`, err.message);
  res.status(500).json({
    error: "Audit failed",
    detail: err.message,
    url
  });
}
```

### Graceful Degradation
For non-critical failures, degrade gracefully instead of crashing:
```javascript
await page.waitForLoadState("networkidle", { timeout: 5000 })
  .catch(() => console.warn("⚠️ Network idle timeout — continuing"));
```

### Aggregate errors in batch operations:
```javascript
const results = [];
for (const url of urls) {
  try {
    results.push(await auditUrl(url));
  } catch (err) {
    results.push({ url, error: err.message, status: "failed" });
  }
}
// Never let one failure abort the whole batch
```

---

## Testing (Required, Not Optional)

Every feature must have tests. No exceptions.

### Backend — use Jest + supertest:
```javascript
// routes/auth.test.js
import request from "supertest";
import app from "../app.js";

describe("POST /api/auth/login", () => {
  it("returns 400 when email missing", async () => {
    const res = await request(app).post("/api/auth/login").send({ password: "test1234" });
    expect(res.status).toBe(400);
    expect(res.body.error).toMatch(/email/i);
  });

  it("returns 401 for wrong credentials", async () => {
    const res = await request(app).post("/api/auth/login").send({ email: "x@x.com", password: "wrongpass" });
    expect(res.status).toBe(401);
  });
});
```

### Frontend — use Vitest + React Testing Library:
```javascript
// components/LoginForm.test.jsx
import { render, screen, fireEvent } from "@testing-library/react";
import LoginForm from "./LoginForm";

test("shows error when fields empty", () => {
  render(<LoginForm />);
  fireEvent.click(screen.getByText("Login"));
  expect(screen.getByText(/required/i)).toBeInTheDocument();
});
```

### Test scripts in package.json:
```json
"scripts": {
  "test": "jest --coverage",
  "test:watch": "jest --watch"
}
```

Always run tests before declaring a feature done.

---

## API Design

- Group routes by resource, one file per resource
- Use consistent response shape:
```javascript
// Success
res.json({ data: result, meta: { total, page, limit } });

// Error
res.status(400).json({ error: "Human-readable message", code: "VALIDATION_ERROR" });
```
- Always paginate list endpoints:
```javascript
const { limit = 50, offset = 0 } = req.query;
const safeLimit = Math.min(Number(limit), 500);
const safeOffset = Math.max(Number(offset), 0);
```
- Return 404 for missing resources, not empty arrays
- Use HTTP verbs correctly: GET (read), POST (create), PUT/PATCH (update), DELETE (remove)

---

## Frontend Architecture

### Centralized API client — never use fetch() directly in components:
```javascript
// src/api/index.js
import axios from "axios";
const api = axios.create({ baseURL: "/api", withCredentials: true });

export const getSites = () => api.get("/sites");
export const createAudit = (siteId, data) => api.post(`/sites/${siteId}/audit`, data);
export const getReport = (jobId, params) => api.get(`/reports/${jobId}`, { params });
```

### Auth context with loading state:
```javascript
const [user, setUser] = useState(undefined); // undefined = loading, null = logged out
useEffect(() => {
  api.get("/auth/me")
    .then(r => setUser(r.data.user))
    .catch(() => setUser(null));
}, []);

if (user === undefined) return <Spinner />;
```

### Component rules:
- Components only handle UI and user interaction
- Data fetching goes in custom hooks or page-level components
- Reusable pieces go in `/components`, route-level go in `/pages`

---

## Database

Always use migrations, never alter the schema manually:
```javascript
// db/migrations/001_initial.js
db.exec(`
  CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'user',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  )
`);
```

Enable WAL mode and foreign keys from the start:
```javascript
db.exec("PRAGMA journal_mode = WAL");
db.exec("PRAGMA foreign_keys = ON");
```

---

## Code Review Checklist

Before marking any task done, verify:

- [ ] No secrets in code or committed files
- [ ] Rate limiting on auth/sensitive endpoints
- [ ] Input validation at route level
- [ ] Parameterized DB queries
- [ ] Error messages include context (what, why, where)
- [ ] Tests written and passing
- [ ] `.env.example` updated with new vars
- [ ] No business logic in route handlers
- [ ] API client centralized (no inline fetch in components)
- [ ] Pagination on list endpoints

---

## What NOT to Do

- **Don't over-engineer v1** — avoid multi-tenant, scheduling, email notifications until needed
- **Don't add dependencies for features that aren't used** — if you install rate-limit, use it
- **Don't swallow errors silently** — every catch block must log or return context
- **Don't commit without checking secrets** — run `git diff --staged` and look for API keys
- **Don't skip tests** — "I'll add tests later" means tests never get added
