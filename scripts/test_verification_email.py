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
    from app.config import get_settings
    from app.services.notifications import send_verification_email

    s = get_settings()
    print("Config:")
    print(f"  MAILGUN_DOMAIN={repr(s.mailgun_domain)}")
    print(f"  MAILGUN_FROM_EMAIL={repr(s.mailgun_from_email)}")
    print(f"  MAILGUN_API_KEY={'***' if s.mailgun_api_key else '(empty)'}")
    print(f"  Sending verification email to: {to_email}")
    print("-" * 50)

    ok = send_verification_email(to_email, "123456")
    if ok:
        print("Result: SUCCESS - Mailgun accepted the message. Check inbox (and spam).")
    else:
        print("Result: FAILED - Check the [Mailgun] lines above for status/response.")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
