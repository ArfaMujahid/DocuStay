# IPs to allow in Stripe “Manage API key → IP restrictions”

Stripe API calls are made **only from your backend** (FastAPI). So you must allow the **public IP(s) of the machine(s) that run the backend**.

## What to add in Stripe

In **Stripe Dashboard → Developers → API keys → [your key] → Manage API key → IP restrictions**, add:

| Environment      | What to add |
|------------------|-------------|
| **Local dev**    | Your current public IP (home/office router). Changes when your ISP changes it or you move. |
| **Production**   | The public IP(s) of the server(s) running the FastAPI app (e.g. VPS, EC2, Railway, Render). |
| **CI / scripts** | IP of the runner if any script calls Stripe (e.g. cron on a server). |

You can add multiple IPs. Use a single address (e.g. `65.249.73.90`) or a range in CIDR (e.g. `65.249.73.0/24`).

## How to get the IP Stripe will see

### Option 1 – From the machine that runs the backend

On the **same machine** where you run `uvicorn` (or your production server), run one of these. The result is the IP you should allow for that environment.

**PowerShell (Windows):**
```powershell
(Invoke-WebRequest -Uri "https://api.ipify.org" -UseBasicParsing).Content
```

**Or (any OS, if you have curl):**
```bash
curl -s https://api.ipify.org
```

**Or:**
```bash
curl -s https://ifconfig.me
```

### Option 2 – From your backend (Python)

Temporarily add a route that returns the outbound IP (same IP Stripe sees when your app calls them):

```python
# One-off: in a router or main.py
import httpx
@router.get("/debug/my-public-ip")
def my_public_ip():
    r = httpx.get("https://api.ipify.org", timeout=5)
    return {"ip": r.text}
```

Call `GET /debug/my-public-ip` from the server (or from your browser if the server is local); the returned `ip` is what to add in Stripe.

## Checklist

1. Run the backend (locally or on the server).
2. From **that same machine**, get the public IP (Option 1 or 2).
3. In Stripe: **Developers → API keys → [Secret key] → Manage API key**.
4. Under **IP restrictions**, add that IP (e.g. `65.249.73.90` or `65.249.73.0/24`).
5. Save. Only those IPs will be able to use that key.

If you use **multiple servers** (e.g. dev + prod), add each server’s public IP. If your host uses **dynamic IPs**, consider a small range (e.g. `/24`) or ask your host for static IPs.
