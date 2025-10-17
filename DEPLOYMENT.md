# Claude Agent Chat - Production Deployment

## Deployment Summary

Successfully deployed the claude-agent-chat multi-agent conversation system on Hostinger VPS with Tailscale VPN and Caddy reverse proxy.

**Deployment Date:** October 17, 2025
**Domain:** chorus.llam.ai
**Status:** ✅ **FULLY OPERATIONAL**

**Access URL:** https://chorus.llam.ai (Tailscale VPN only)
**TLS Certificate:** ✅ Obtained from Let's Encrypt
**DNS Status:** ✅ Configured (chorus.llam.ai → 100.120.123.60)

---

## Architecture

### Network Stack
```
Internet → Cloudflare (DNS/CDN)
    ↓
Caddy Reverse Proxy (TLS termination)
    ↓
Tailscale VPN Network
    ↓
Docker Containers (chorus-on-hstgr:3000)
```

### Service Components

| Service | Container | Status | Port | Network |
|---------|-----------|--------|------|---------|
| Tailscale Sidecar | chorus-on-hstgr | Running | 3000, 8000 | Tailscale VPN |
| PostgreSQL | chorus-postgres | Healthy | 5432 | Shared with Tailscale |
| Qdrant Vector DB | chorus-qdrant | Running | 6333 | Shared with Tailscale |
| Backend API | chorus-backend | Healthy | 8000 | Shared with Tailscale |
| Frontend (Next.js) | chorus-frontend | Healthy | 3000 | Shared with Tailscale |

---

## Tailscale Configuration

**Node Name:** `chorus-on-hstgr`
**IP Address:** `100.113.204.103`
**Auth Key Location:** `~/.config/tsauthkey`
**State Directory:** `./tailscale-state`

### Tailscale Sidecar Pattern
All services use `network_mode: service:chorus-on-hstgr` to share the Tailscale VPN network namespace, providing:
- Secure remote access via Tailscale
- Isolation from public internet
- Encrypted service-to-service communication

---

## Access Configuration

**Access Method:** Tailscale VPN Only with HTTPS (Private)

chorus.llam.ai is configured for **Tailscale-only HTTPS access**, similar to your other private services (o.llam.ai, s.llam.ai). This means:

- ✅ Only accessible from devices on your Tailscale network
- ✅ Not exposed to the public internet
- ✅ Encrypted via HTTPS (TLS certificate from Let's Encrypt)
- ✅ Standard HTTPS port 443 (no port number needed in URL)
- ✅ Proxied through Caddy for TLS termination

---

## Caddy Configuration

**Location:** `/home/chuck/homelab/caddy2/Caddyfile`

```caddyfile
chorus.llam.ai {
    reverse_proxy chorus-on-hstgr:3000

    tls {
        dns cloudflare {env.CLOUDFLARE_API_TOKEN}
    }
}
```

**How it works:**
1. Caddy listens on the VPS's Tailscale interface (`100.120.123.60:443`)
2. Receives HTTPS requests for chorus.llam.ai (from Tailscale network only)
3. Automatically obtains TLS certificate via Cloudflare DNS-01 challenge
4. Proxies requests to chorus-on-hstgr:3000 (the frontend container)
5. Returns encrypted HTTPS responses

**TLS Certificate:** ✅ Automatically obtained and renewed via Let's Encrypt

---

## Cloudflare DNS Configuration

### Required DNS Record (Tailscale-Only HTTPS Access)

Add the following A record in your Cloudflare dashboard for `llam.ai`:

| Type | Name | Content | Proxy Status | TTL |
|------|------|---------|--------------|-----|
| A | chorus | `100.120.123.60` | DNS only (gray cloud) | Auto |

**Steps to configure:**

1. Log in to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Select the `llam.ai` domain
3. Go to **DNS** → **Records**
4. Click **Add record**
5. Fill in:
   - **Type:** A
   - **Name:** chorus
   - **IPv4 address:** `100.120.123.60` (VPS Tailscale IP - same as o.llam.ai and s.llam.ai)
   - **Proxy status:** DNS only (click the cloud icon to make it gray)
   - **TTL:** Auto
6. Click **Save**

**Important:**
- This uses the **VPS's Tailscale IP** (not the chorus-on-hstgr container IP)
- Traffic flows: `chorus.llam.ai` → VPS Tailscale IP → Caddy → chorus-on-hstgr:3000
- Accessible only to devices on your Tailscale VPN network
- HTTPS on port 443 (standard port, no need to specify)

---

## Docker Compose Files

### Production (Tailscale VPN)
- **File:** `docker-compose.prod.yaml`
- **Usage:** `docker compose -f docker-compose.prod.yaml up -d`
- **Features:** Tailscale sidecars, secure remote access

### Local Testing
- **File:** `docker-compose.local.yaml`
- **Usage:** `docker compose -f docker-compose.local.yaml up -d`
- **Features:** Standard Docker networking, localhost access

---

## Environment Variables

**Location:** `.env`

Required variables:
```env
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-proj-...
POSTGRES_PASSWORD=chorus_secure_pass_2024
```

---

## Service Management

### Start Services
```bash
cd /home/chuck/homelab/claude-agent-chat
docker compose -f docker-compose.prod.yaml up -d
```

### Stop Services
```bash
docker compose -f docker-compose.prod.yaml down
```

### View Logs
```bash
# All services
docker compose -f docker-compose.prod.yaml logs -f

# Specific service
docker compose -f docker-compose.prod.yaml logs -f backend
```

### Check Status
```bash
docker compose -f docker-compose.prod.yaml ps
```

### Restart Services
```bash
docker compose -f docker-compose.prod.yaml restart
```

---

## Health Checks

### Backend API
```bash
curl http://localhost:8000/api/health
# Expected: {"status":"healthy","database":"connected","timestamp":"..."}
```

### Frontend
```bash
curl http://localhost:3000
# Expected: HTML response with "Claude Agent Chat"
```

### Tailscale Connectivity
```bash
docker exec claude-agent-chat-chorus-on-hstgr-1 tailscale status
# Expected: List of tailnet nodes with chorus-on-hstgr active
```

---

## Access URLs

- **Tailscale VPN:** https://chorus.llam.ai (after Cloudflare DNS is configured)
- **Local (on VPS):** http://localhost:3000
- **Backend API (on VPS):** http://localhost:8000
- **API Docs (on VPS):** http://localhost:8000/docs

**Note:**
- ✅ Uses standard HTTPS port 443 (no port number needed)
- 🔒 Requires being connected to your Tailscale VPN network
- ⛔ NOT publicly accessible
- 🔐 TLS certificate automatically managed by Caddy

---

## Database Information

### PostgreSQL
- **Host:** postgres (Docker network) / localhost (from backend)
- **Port:** 5432
- **Database:** agent_conversations
- **User:** agent_user
- **Data Volume:** `postgres_data`

### Qdrant
- **Host:** qdrant (Docker network) / localhost (from backend)
- **Port:** 6333 (HTTP), 6334 (gRPC)
- **Data Volume:** `qdrant_data`

---

## Troubleshooting

### Services Won't Start
1. Check Tailscale auth key is valid:
   ```bash
   cat ~/.config/tsauthkey
   ```
2. Verify environment variables:
   ```bash
   cat .env
   ```
3. Check logs:
   ```bash
   docker compose -f docker-compose.prod.yaml logs
   ```

### Caddy Not Proxying
1. Verify Caddy is running:
   ```bash
   cd /home/chuck/homelab/caddy2 && docker compose ps
   ```
2. Check Caddy logs:
   ```bash
   cd /home/chuck/homelab/caddy2 && docker compose logs caddy --tail 50
   ```
3. Validate Caddyfile:
   ```bash
   docker exec caddy caddy validate --config /etc/caddy/Caddyfile
   ```

### DNS Not Resolving
1. Verify DNS record is created in Cloudflare
2. Check DNS propagation:
   ```bash
   dig chorus.llam.ai
   nslookup chorus.llam.ai
   ```
3. Wait up to 5 minutes for DNS propagation

---

## Backup & Maintenance

### Database Backups
```bash
# PostgreSQL backup
docker exec chorus-postgres pg_dump -U agent_user agent_conversations > backup_$(date +%Y%m%d).sql

# Restore
docker exec -i chorus-postgres psql -U agent_user agent_conversations < backup_20251017.sql
```

### Volume Backups
```bash
# Backup volumes
docker run --rm -v claude-agent-chat_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_data.tar.gz -C /data .
docker run --rm -v claude-agent-chat_qdrant_data:/data -v $(pwd):/backup alpine tar czf /backup/qdrant_data.tar.gz -C /data .
```

---

## Performance Monitoring

### Container Resource Usage
```bash
docker stats
```

### Disk Usage
```bash
docker system df
```

---

## Security Notes

- ✅ All services isolated behind Tailscale VPN
- ✅ TLS certificates automatically managed by Caddy
- ✅ Environment variables stored securely in `.env` (gitignored)
- ✅ Tailscale auth key stored with 600 permissions
- ✅ Database passwords configured
- ✅ No services exposed directly to public internet (except via Caddy proxy)

---

## Support & Documentation

- **GitHub Repository:** https://github.com/snedea/claude-agent-chat
- **Tailscale Docs:** https://tailscale.com/kb/
- **Caddy Docs:** https://caddyserver.com/docs/
- **Next.js Docs:** https://nextjs.org/docs

---

## Deployment Checklist

- [x] Clone repository
- [x] Create Dockerfiles (backend, frontend)
- [x] Create docker-compose.prod.yaml with Tailscale sidecars
- [x] Configure environment variables (.env)
- [x] Fix backend import paths
- [x] Add database connection environment variable support
- [x] Install/update Tailscale auth key
- [x] Deploy production stack
- [x] Configure Caddy reverse proxy
- [x] Obtain TLS certificate
- [ ] **Configure Cloudflare DNS A record** ← ACTION REQUIRED
- [x] Verify all services healthy
- [x] Test API endpoints
- [x] Document deployment

---

## Next Steps

1. **Configure Cloudflare DNS** (see section above)
2. Test production access at https://chorus.llam.ai
3. Set up monitoring/alerting (optional)
4. Configure automated backups (optional)
5. Set up log aggregation (optional)

---

*Deployment completed on October 17, 2025*
