"""
Send a test email via Mailgun to verify the email service is configured correctly.
Usage: python scripts/test_mailgun_send.py [to_email]
Example: python scripts/test_mailgun_send.py arfamujahid333@gmail.com
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import get_settings
from app.services.notifications import send_email

def main():
    to_email = (sys.argv[1] if len(sys.argv) > 1 else "").strip()
    if not to_email:
        print("Usage: python scripts/test_mailgun_send.py <to_email>")
        print("Example: python scripts/test_mailgun_send.py your@email.com")
        sys.exit(1)

    settings = get_settings()
    if not settings.mailgun_api_key or not settings.mailgun_domain:
        print("Mailgun is not configured. Set MAILGUN_API_KEY and MAILGUN_DOMAIN in .env")
        print(f"  MAILGUN_API_KEY: {'(set)' if settings.mailgun_api_key else '(missing)'}")
        print(f"  MAILGUN_DOMAIN: {repr(settings.mailgun_domain) if settings.mailgun_domain else '(missing)'}")
        sys.exit(1)

    print(f"Sending test email to: {to_email}")
    print(f"From: {settings.mailgun_from_name} <{settings.mailgun_from_email}>")
    print(f"Domain: {settings.mailgun_domain}")

    subject = "[DocuStay] Test email – Mailgun is working"
    text = "This is a test from DocuStay. If you received this, the Mailgun email service is configured correctly."
    html = """
    <p>This is a <strong>test email</strong> from DocuStay.</p>
    <p>If you received this, the Mailgun email service is configured correctly.</p>
    <p>— DocuStay</p>
    """

    ok = send_email(to_email, subject, html, text_content=text)
    if ok:
        print("Success: Test email sent. Check the inbox (and spam) for", to_email)
    else:
        print("Failed: Mailgun returned an error.")
        print("  - Use the Private API key from Mailgun (Sending -> Domain -> API Keys), not the domain name.")
        print("  - For EU accounts set MAILGUN_BASE_URL=https://api.eu.mailgun.net in .env")
        print("  - Ensure MAILGUN_FROM_EMAIL is allowed for your domain (e.g. sandbox authorized recipients).")
        sys.exit(1)


if __name__ == "__main__":
    main()
