"""
Test Smarty US Street API with address standardization.
Uses: 1 Infinite Loop, Cupertino, CA 95014, USA

Set DRY_RUN = False to actually call the API (uses 1 API credit on free trial).
Run from project root: python scripts/test_smarty.py
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Load .env before importing app
from dotenv import load_dotenv
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env")))

# Set to False to make real API call (uses 1 credit)
DRY_RUN = False

TEST_ADDRESS = {
    "street": "1 Infinite Loop",
    "city": "Cupertino",
    "state": "CA",
    "zipcode": "95014",
}


def main():
    from app.services.smarty import verify_address
    from app.config import get_settings

    settings = get_settings()
    if not settings.smarty_auth_id or not settings.smarty_auth_token:
        print("ERROR: SMARTY_AUTH_ID and SMARTY_AUTH_TOKEN must be set in .env")
        sys.exit(1)

    print("Smarty US Street API – Address Standardization Test")
    print("-" * 50)
    print("Test address:", f"{TEST_ADDRESS['street']}, {TEST_ADDRESS['city']}, {TEST_ADDRESS['state']} {TEST_ADDRESS['zipcode']}")
    print()

    if DRY_RUN:
        print("DRY_RUN=True – no API call made. Set DRY_RUN=False in this script to call the API.")
        print("Expected output structure:")
        print("  delivery_line_1: 1 Infinite Loop")
        print("  city_name: Cupertino")
        print("  state_abbreviation: CA")
        print("  zipcode: 95014")
        print("  plus4_code: (4-digit)")
        print("  latitude: ~37.33")
        print("  longitude: ~-122.03")
        return

    result = verify_address(
        street=TEST_ADDRESS["street"],
        city=TEST_ADDRESS["city"],
        state=TEST_ADDRESS["state"],
        zipcode=TEST_ADDRESS["zipcode"],
    )

    if result is None:
        print("API returned no match (empty response or error). Check credentials and address.")
        sys.exit(1)

    print("SUCCESS – standardized address:")
    print(f"  delivery_line_1:   {result.delivery_line_1}")
    print(f"  city_name:        {result.city_name}")
    print(f"  state_abbreviation: {result.state_abbreviation}")
    print(f"  zipcode:          {result.zipcode}")
    print(f"  plus4_code:       {result.plus4_code}")
    print(f"  latitude:         {result.latitude}")
    print(f"  longitude:        {result.longitude}")
    print()
    print("These fields will be stored in properties table when integrating with registration.")


if __name__ == "__main__":
    main()
