# Bug Bounty Recon Platform

A highly automated, continuous reconnaissance and monitoring platform for bug bounty hunting. Built with a focus on safety, reliability, and precision. Authorized use only.

## Architecture

```
+-----------+       +-------------------+       +-----------------+
| Dashboard | <---> | FastAPI (Backend) | <---> | PostgreSQL (DB) |
+-----------+       +-------------------+       +-----------------+
                              ^                          ^
                              |                          |
                              v                          |
+------------------------------------+                   |
|           Redis Message Broker     |                   |
+------------------------------------+                   |
    ^                          ^                         |
    |                          |                         |
    v                          v                         |
+-----------------+   +------------------+               |
| Monitor Service |   | Celery Workers   | <-------------+
| (H1/Bugcrowd)   |   | (Recon & Alert)  |
+-----------------+   +------------------+
```

## Tech Stack

| Component | Technology |
|---|---|
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0 |
| Database | PostgreSQL 16 |
| Task Queue | Celery, Redis |
| Frontend | React, Node.js 20 |
| Recon Tools | Subfinder, Httpx, Katana, Gau, Gowitness (Go) |
| Reverse Proxy | Caddy |

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/bugbounty-recon.git
   cd bugbounty-recon
   ```

2. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. Start the stack:
   ```bash
   docker-compose up --build -d
   ```

4. Access the platform:
   - Dashboard: http://localhost:3000
   - API Docs: http://localhost:8000/docs

## Development Setup

If you prefer to run services locally without Docker:
1. Create a Python virtual environment and install requirements.
2. Install Go 1.22+ and the required recon tools (subfinder, httpx, katana, gau, gowitness).
3. Set up a local PostgreSQL and Redis instance.
4. Update your `.env` file with the correct URIs.
5. Run the services manually:
   - FastAPI: `uvicorn api.main:app --reload`
   - Worker: `celery -A recon.pipeline worker -l info`
   - Frontend: `cd frontend && npm install && npm run start`

## Safety Constraints

This platform is designed with strict safety boundaries:
1. **Scope Verification**: Every single reconnaissance action checks the PostgreSQL database in real-time to verify the target is unequivocally `in_scope`. Out-of-scope targets trigger an immediate abort.
2. **Read-Only Operations**: No exploit payloads or write operations are ever sent to targets. Reconnaissance is strictly passive and passively-active (e.g., DNS brute-forcing, crawling).
3. **Subprocess Safety**: Command executions avoid `shell=True` entirely. Complete arguments are explicitly passed in arrays to prevent injection.
4. **Secrets Management**: No hardcoded credentials. All secrets are managed securely through environment variables and Pydantic configuration settings.

## Testing

Run the test suite using pytest:
```bash
pytest tests/
```
Coverage reports can be generated with:
```bash
pytest tests/ --cov=. --cov-report=html
```

## License

MIT License. See `LICENSE` for details.
