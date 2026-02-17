/**
 * Validates phone number for owner/guest signup.
 * Accepts common formats: +1 (555) 123-4567, (555) 123-4567, 555-123-4567, 5551234567.
 * After stripping non-digits (except leading +), requires 10–15 digits (E.164 style).
 */
const MIN_DIGITS = 10;
const MAX_DIGITS = 15;

export function normalizePhone(input: string | null | undefined): string {
  const s = (input ?? "").trim();
  const hasPlus = s.startsWith("+");
  const digits = s.replace(/\D/g, "");
  return hasPlus ? `+${digits}` : digits;
}

export function validatePhone(input: string | null | undefined): { valid: boolean; error?: string } {
  const s = (input ?? "").trim();
  if (!s) {
    return { valid: false, error: "Phone number is required." };
  }
  const digitsOnly = s.replace(/\D/g, "");
  if (digitsOnly.length < MIN_DIGITS) {
    return { valid: false, error: `Enter at least ${MIN_DIGITS} digits (e.g. 5551234567 or +1 555 123 4567).` };
  }
  if (digitsOnly.length > MAX_DIGITS) {
    return { valid: false, error: `Phone number cannot exceed ${MAX_DIGITS} digits.` };
  }
  if (!/^\d+$/.test(digitsOnly)) {
    return { valid: false, error: "Phone number can only contain digits and optional +, spaces, dashes, or parentheses." };
  }
  return { valid: true };
}
