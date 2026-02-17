#!/usr/bin/env python3
"""Send a test verification email and print the result. Use to debug Mailgun delivery.
Usage: from project root, run:
  python scripts/test_verification_email.py
  python scripts/test_verification_email.py other@example.com
"""
import os
import sys

# Project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    to_email = (sys.argv[1] if len(sys.argv) > 1 else "arfamujahid12@gmail.com").strip()
    from pathlib import Path
    from app.config import _env_path, get_settings
    from app.services.notifications import send_verification_email

    s = get_settings()
    print("DocuStay verification email test")
    print(f"  .env path: {_env_path} (exists: {Path(_env_path).exists()})")
    print("  Config:")
    print(f"    MAILGUN_DOMAIN={repr(s.mailgun_domain) or '(empty)'}")
    print(f"    MAILGUN_FROM_EMAIL={repr(s.mailgun_from_email) or '(default)'}")
    print(f"    MAILGUN_API_KEY={'set (hidden)' if s.mailgun_api_key else '(empty)'}")
    print(f"  Sending verification code to: {to_email}")
    print("-" * 50)

    ok = send_verification_email(to_email, "123456")
    print("-" * 50)
    if ok:
        print("Result: SUCCESS - Mailgun accepted the message.")
        print("  If you do not receive it: check spam; if using a sandbox domain, add this address in Mailgun Dashboard > Authorized recipients.")
    else:
        print("Result: FAILED - See [Email]/[Mailgun] lines above for cause.")
        print("  Fix .env (MAILGUN_API_KEY, MAILGUN_DOMAIN), then restart the server and run this script again.")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
