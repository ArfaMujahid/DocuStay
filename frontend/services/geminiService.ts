
import { GoogleGenAI, Type } from "@google/genai";

const SYSTEM_PROMPT = `
You are DocuStay AI, a legal-tech assistant that handles user authentication and onboarding for a property protection platform. Your role is to guide both Property Owners and Guests through secure registration and verification.

## Your Purpose
Help users register and verify their identity on the DocuStay platform. You handle two types of users:
1. Property Owners - People who own properties and want to protect them from squatters
2. Guests/Clients - People who will be staying at properties temporarily

## Authentication Rules
- All users must provide valid information
- Email and phone must be verified
- Property owners must prove property ownership
- Guests are invited by property owners (they cannot self-register without invitation)

## You Must Always
- Validate all input data strictly according to requested rules
- Check for required fields
- Return clear error messages for invalid data in the specific validation object
- Generate secure 6-digit verification codes
- Track verification status
- Never store raw passwords (indicate hashing required)

## Response Format
Always respond in valid JSON format with:
- status: "success" | "error" | "pending"
- message: Human readable message
- validation: Object containing per-field validation results
- data: Relevant data object
- next_step: What the user should do next
`;

// Initialize GoogleGenAI strictly with the environment variable as per requirements.
const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });

export const callGemini = async (promptName: string, inputData: any) => {
  const model = 'gemini-3-flash-preview';
  
  let userPrompt = '';
  switch (promptName) {
    case 'owner_registration':
      userPrompt = `Process property owner registration with the following data:

**Input Data:**
- Full Name: ${inputData.full_name}
- Email: ${inputData.email}
- Phone: ${inputData.phone}
- Password: ${inputData.password}
- Confirm Password: ${inputData.confirm_password}
- Country: ${inputData.country}
- State: ${inputData.state}
- City: ${inputData.city}
- Agreed to Terms: ${inputData.terms_agreed}
- Agreed to Privacy Policy: ${inputData.privacy_agreed}

**Validation Rules:**
1. Full name must be at least 2 words.
2. Email must be a valid format.
3. Phone must be a valid US format (for US users).
4. Password must be minimum 8 characters with 1 uppercase, 1 lowercase, 1 number, and 1 special character.
5. Passwords must match.
6. Both terms and privacy must be agreed (true).
7. State must be a valid US state (e.g., NY, FL, CA, TX, WA).

**Process this registration and return exactly this structure:**
{
  "status": "success|error",
  "message": "",
  "validation": {
    "full_name": {"valid": true/false, "error": ""},
    "email": {"valid": true/false, "error": ""},
    "phone": {"valid": true/false, "error": ""},
    "password": {"valid": true/false, "error": ""},
    "password_match": {"valid": true/false, "error": ""},
    "terms": {"valid": true/false, "error": ""},
    "privacy": {"valid": true/false, "error": ""}
  },
  "data": {
    "user_id": "OWNER_ID_RANDOM",
    "user_type": "PROPERTY_OWNER",
    "email_verification_code": "123456",
    "phone_verification_code": "654321",
    "verification_expires_at": "timestamp",
    "account_status": "PENDING_VERIFICATION"
  },
  "next_step": "Verify email and phone"
}`;
      break;

    case 'owner_verify_contact':
      userPrompt = `Verify property owner's email or phone with the following data:
      Input Data: ${JSON.stringify(inputData)}
      
      Rules:
      1. Code must match exactly.
      2. Code must not be expired (valid for 10 minutes).
      3. Max 3 attempts.`;
      break;

    case 'owner_add_property':
      userPrompt = `Process property addition:
      Input Data: ${JSON.stringify(inputData)}
      
      Determine jurisdiction rules and max safe stay.`;
      break;

    case 'owner_invite_guest':
      userPrompt = `Process guest invitation:
      Input Data: ${JSON.stringify(inputData)}
      
      Calculate stay duration and risk level.`;
      break;

    case 'user_login':
      userPrompt = `Process login:
      Input Data: ${JSON.stringify(inputData)}
      Return success if credentials valid.`;
      break;

    default:
      userPrompt = `Process request for ${promptName} with data: ${JSON.stringify(inputData)}`;
  }

  try {
    const response = await ai.models.generateContent({
      model,
      contents: userPrompt,
      config: {
        systemInstruction: SYSTEM_PROMPT,
        responseMimeType: "application/json",
      },
    });

    const text = response.text || "{}";
    return JSON.parse(text);
  } catch (error) {
    console.error("Gemini API Error:", error);
    return { 
      status: "error", 
      message: "The DocuStay logic engine encountered an error. Please check your internet connection.",
      validation: {}
    };
  }
};
