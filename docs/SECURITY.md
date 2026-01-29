# InsightX AI - Security Guidelines

## Secrets Management

### ✅ DO
- Store all secrets in environment variables
- Use `.env` files for local development (gitignored)
- Use secret management services in production (AWS Secrets Manager, HashiCorp Vault)

### ❌ DON'T
- Commit API keys to version control
- Log API keys or session tokens
- Hard-code secrets in source code

## Required Environment Variables

```bash
# Required
GEMINI_API_KEY=your_key_here  # Never commit this

# Optional but recommended
REDIS_URL=redis://localhost:6379  # For session storage
```

## API Security

### Rate Limiting
- LLM calls limited to `RATE_LIMIT_PER_MIN` per session
- IP-based rate limiting via nginx: 10 req/s burst 20

### CORS
- Restricted to `FRONTEND_ORIGIN` environment variable
- No wildcard origins in production

### Input Validation
- All inputs validated via Pydantic schemas
- Maximum message length: 2000 characters
- Session IDs must be valid UUIDs

## Container Security

### Non-Root Users
Both Dockerfiles create and use non-root users:
```dockerfile
RUN useradd --create-home --shell /bin/bash appuser
USER appuser
```

### Health Checks
Enabled for automated container recovery:
```dockerfile
HEALTHCHECK --interval=30s --timeout=5s CMD curl -f http://localhost:8000/api/health
```

## Data Security

### No PII Logging
- Never log full user messages containing potential PII
- Truncate logged content to first 100 characters
- Use request IDs for audit trails

### Transaction Data
- Sample data generation uses synthetic values
- Production data should be anonymized for testing

## Network Security

### HTTPS Required
- Enable SSL in nginx for production
- Use Let's Encrypt for free certificates
- Redirect all HTTP to HTTPS

### Internal Communication
- Backend and frontend communicate over internal Docker network
- Only nginx exposed to public internet

## Checklist for Production

- [ ] GEMINI_API_KEY is not the placeholder value
- [ ] SSL/TLS certificates installed
- [ ] CORS origin matches actual domain
- [ ] Rate limiting enabled
- [ ] Logs don't contain secrets
- [ ] Non-root containers verified
- [ ] Health checks responding
- [ ] Firewall rules configured

## Incident Response

If a secret is exposed:
1. Immediately rotate the API key in Google Cloud Console
2. Update the environment variable
3. Restart services
4. Review access logs for unauthorized usage
5. Report to security team

## Dependencies

Regularly update dependencies:
```bash
# Backend
pip install --upgrade -r requirements.txt

# Frontend
npm update
npm audit fix
```

## Contact

For security issues, contact the security team directly.
Do not file public GitHub issues for security vulnerabilities.
