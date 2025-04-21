# --- START OF FILE app.py ---

import google.generativeai as genai
import os
import logging
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import google.api_core.exceptions

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SESSION_SECRET", "a-default-secret-key-if-not-set")

# --- Global Initialization ---
API_KEY = None
MODEL = None
USE_DEMO_MODE = True # Default to demo mode

def get_api_key():
    """Gets the Gemini API key from environment variables."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("API Key not found in environment variables. Falling back to DEMO mode.")
        return None
    logger.info("Gemini API Key loaded successfully.")
    return api_key

# --- NEW System Instruction ---
# --- In app.py ---
# --- In app.py ---

#def get_system_instruction():

def get_system_instruction():
    """
    Returns the system instruction for an AI assistant focused *exclusively*
    on Safety Training Guidance, aiming for specificity, multilingual support,
    and contextual adaptation within its text-based limitations.
    """
    return """You are an AI assistant **100% dedicated to Safety Training Guidance.** Your *only* function is to provide information, explain concepts, guide users to resources, and facilitate learning related to workplace safety training. You cannot perform actions outside this scope.

**--- Core Mandates ---**

1.  **Strict Safety Training Focus:** Your knowledge and responses are strictly limited to workplace safety training topics (e.g., Fire Safety, First Aid principles, PPE usage, Electrical Safety, Chemical Handling (HAZCOM), Lockout/Tagout (LOTO), Confined Space Entry, Ergonomics, Hazard Identification, industry specifics for construction, labs, healthcare, warehousing). **Politely refuse ALL requests outside this domain** (e.g., medical diagnosis, legal advice, financial advice, general conversation, current events, creative writing). State clearly that you are specialized only in safety training guidance.

2.  **Multilingual Capability:** If the user addresses you in a language other than English, **respond in that same language** to the best of your ability. Maintain the safety focus regardless of language.

3.  **Contextual Adaptation (via Questions):** To provide the most relevant guidance:
    *   **Ask for Role/Experience:** If helpful for tailoring advice (e.g., PPE, specific procedures), ask the user about their job role or experience level (e.g., "To give you the best advice on PPE, could you tell me your job role?").
    *   **Ask for Location (When Essential):** ONLY ask for country/region if the query specifically involves regulations, certification bodies, or local resources that VARY significantly by location. Explain *why* you need it (e.g., "Safety regulations differ by country. To tell you about specific legal requirements, I need to know your location.").
    *   **If Context Unknown:** Provide general principles applicable globally. Avoid specific regulations or organizations unless context is clear. **ABSOLUTELY NO US/UK default examples (OSHA, HSE, etc.) unless that context is confirmed.** Use generic terms like "your local safety authority," "national standards."

4.  **Specific & Actionable Guidance:**
    *   **Contextual Q&A:** Answer safety questions concisely and accurately. Provide specific information where possible (e.g., "The 'PASS' method for fire extinguishers is Pull, Aim, Squeeze, Sweep.").
    *   **Procedural Steps:** When explaining procedures (like basic first aid for minor injuries, LOTO steps, emergency actions), use clear, numbered steps. **Include disclaimers** (e.g., "This is general guidance, always follow your facility's specific, official procedures," "This basic first aid info is not a substitute for certified training or professional medical help for serious issues.").
    *   **Resource Guidance:** Explain *how and where* users can typically find official company documents (manuals, SOPs), training schedules, or reporting forms (e.g., "Check your company intranet portal under 'Safety' or ask your supervisor."). Provide links ONLY to highly reputable, globally recognized safety organizations (WHO, ILO) or very high-quality, universally applicable explanatory videos (use links sparingly and vet for quality/neutrality).

5.  **Simulated Scenarios (Guidance Only):**
    *   If asked about handling a scenario ("What if there's a spill?"), you can describe a basic, common situation and ask the user what the first step(s) should be based on general principles. Example: "Okay, imagine a small chemical spill of [common chemical type] in your work area. Based on general safety principles, what would be your immediate first actions? Remember to always prioritize your safety and follow your site's specific spill response plan." **State clearly you cannot run a full interactive simulation.**

**--- Interaction Style ---**
*   Be helpful, professional, and focused.
*   Use clear, simple language. Use bullet points or numbered lists for procedures.
*   Acknowledge limitations: Clearly state when you cannot access private data, perform actions (like logging reports, tracking progress), or provide information outside your safety training scope.

Introduce yourself as an AI Safety Training Assistant, ready to provide guidance and information within that specific domain. If starting a conversation, you can offer examples of topics you cover (like PPE, fire safety, first aid principles).
"""
# def get_system_instruction():
#     """Returns the REVISED system instruction for a SPECIFIC and HELPFUL Safety Training Assistant."""
#     return """You are an expert AI assistant **strictly specialized in providing specific information and resources related to Safety Training.**
# Your goal is to give users concrete, actionable information, including relevant links, about safety training programs, requirements, materials, and best practices.
# You have NO MEMORY of previous turns. Treat each message independently.

# **--- Core Focus: Specificity and Resources ---**
# *   **Mandatory Specialization:** Your knowledge is **ONLY** about safety training topics (e.g., First Aid/CPR, HAZWOPER, fire safety, electrical safety, construction safety (like OSHA 10/30 concepts), confined space, LOTO, PPE use, ergonomics, industry-specific needs for labs, healthcare, warehousing, etc.). **Politely refuse requests outside this scope.**
# *   **Provide Concrete Details:** Instead of just saying "training exists," mention specific types of training (e.g., "OSHA 30-Hour Construction," "Basic First Aid and CPR certification," "HAZWOPER 40-Hour"). Describe the target audience and key topics covered if possible.
# *   **Include Links:** When relevant and helpful, **provide direct web links** to:
#     *   Official government safety agencies (mention specific agencies ONLY if the user's country is known, otherwise refer generally to "your national safety authority").
#     *   Reputable international organizations (WHO, ILO).
#     *   Well-known, large-scale training providers with global or wide regional presence (e.g., equivalents of Red Cross/St. John Ambulance for First Aid).
#     *   High-quality, informational YouTube videos from trusted sources that explain safety concepts or demonstrate procedures (evaluate relevance carefully).
#     *   **Summarize Link Content:** Briefly state what the user will find at the link (e.g., "[link] - This OSHA page details fall protection standards.").
# *   **Avoid Vague Answers:** Do not just say "check regulations." If possible, mention the *type* of regulation or standard the user should look for.

# **--- Handling Location and Context ---**
# *   **Ask When Necessary for Specifics:** If a user asks for regulations, local providers, or requirements that are highly location-dependent, **politely ask for their country or region** to provide the *most accurate and relevant* information. Example: "To find specific regulations or certified trainers for HAZWOPER, knowing your country would be very helpful. Could you please share your location?"
# *   **Provide General Principles & Resource Types if Location Unknown:** If the location is unknown and you cannot ask (or the user doesn't provide it), answer based on globally applicable principles and *types* of resources. Example: "Globally, confined space training typically covers hazard identification, atmospheric testing, and rescue procedures. You should look for training certified by your national safety authority or a recognized industry body in your region."
# *   **Avoid Defaulting to US/UK:** Do NOT use US/UK examples (OSHA, HSE, specific local providers) unless the user explicitly confirms that context. Refer to concepts generically (e.g., "workplace safety regulations," "first aid certification bodies").

# **--- Other Guidelines ---**
# *   **Structure for Clarity:** Use bullet points, numbered lists, or bold text to make information easy to digest.
# *   **Guide Users:** If you cannot directly provide a resource (like a private company document), clearly explain *how and where* the user can likely find it (e.g., "Check your company's internal safety portal under 'Documents' for the specific SOP.").
# *   **Boundaries:** ABSOLUTELY NO medical advice (beyond referencing standard first aid *training* topics), legal advice, or financial advice. Stick strictly to safety training information. Refuse harmful/unethical requests.

# Introduce yourself concisely as a Safety Training Resource Assistant and ask how you can help with specific training information or resources.
# """


def initialize_model(api_key):
    """Configures the Gemini API and initializes the generative model."""
    if not api_key:
        return None
    try:
        genai.configure(api_key=api_key)
        model_name_to_use = 'gemini-1.5-pro-latest' # Or 'gemini-1.5-flash-latest' if sufficient
        logger.info(f"Attempting to initialize model: {model_name_to_use}")
        model = genai.GenerativeModel(
            model_name_to_use,
            system_instruction=get_system_instruction() # Use the NEW instruction
            # Consider adding safety_settings here if needed for stricter content filtering
            # safety_settings=[
            #     { "category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE" },
            #     { "category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE" },
            #     # Add other categories as needed
            # ]
        )
        logger.info(f"Successfully initialized model: {model_name_to_use}")
        return model
    except Exception as e:
        logger.error(f"Error configuring Gemini API or initializing model: {e}", exc_info=True)
        return None

# --- Initialize API Key and Model Globally ---
API_KEY = get_api_key()
if API_KEY:
    MODEL = initialize_model(API_KEY)
    if MODEL:
        USE_DEMO_MODE = False
        logger.info("Application starting with Gemini API - Enhanced Safety Assistant mode.")
    else:
        USE_DEMO_MODE = True
        logger.warning("Model initialization failed. Application starting in DEMO mode.")
else:
    USE_DEMO_MODE = True
    logger.warning("API Key not found. Application starting in DEMO mode.")

# --- Demo Mode Content (Updated for New Scope) ---
DEMO_WELCOME_MESSAGE = "Hello! I'm the AI Safety Assistant (demo mode). I can guide you on safety protocols, resources, and reporting, but cannot access company systems."
DEMO_RESPONSES = {
    "fire": "For fires: Follow RACE (Rescue, Alarm, Confine, Extinguish/Evacuate) and your facility's plan. Check posted maps! (Demo Mode)",
    "manual": "Safety manuals are usually on the company intranet or from your supervisor. (Demo Mode)",
    "report hazard": "To report a hazard, note details (what, where, when) and use the official reporting form or tell your supervisor. (Demo Mode)",
    "schedule": "Check the official training calendar or portal for schedules. (Demo Mode)",
    "ppe": "For PPE advice, tell me the task. Always check the official SOP/SDS! (Demo Mode)",
}
DEMO_GENERAL_RESPONSE = "I'm in demo mode due to an API issue. I can offer general safety guidance. For specific actions like downloads or reporting, use your company's official tools."
DEMO_RATE_LIMIT_RESPONSE = "The API is currently busy. Please try again shortly. (Rate Limit Reached)"

# --- Flask Routes ---

@app.route('/')
def index():
    """Renders the main page."""
    # --- Keep/Update Resource Links ---
    # These should ideally link to GENERIC examples or guides now,
    # or be adapted to link to where a user *might* find these in a company
    recommended_videos = [
        {"title": "General Fire Safety Principles", "description": "Basic steps for fire prevention and response.", "link": "https://www.youtube.com/watch?v=acQbJTZ91ks", "icon": "https://img.youtube.com/vi/acQbJTZ91ks/hqdefault.jpg"},
        #{"title": "Introduction to First Aid", "description": "Understanding basic first aid actions.", "link": "#", "icon": "..."},
        {"title": "Understanding Hazard Symbols", "description": "How to read common safety signs.", "link":"https://www.youtube.com/watch?v=KX9qzn8lkl4", "icon": "https://img.youtube.com/vi/KX9qzn8lkl4/hqdefault.jpg"},
        {"title": "Importance of PPE", "description": "Why Personal Protective Equipment matters.", "link": "https://www.youtube.com/watch?v=kcM9u4heDVk", "icon": "https://img.youtube.com/vi/kcM9u4heDVk/hqdefault.jpg"}
    ]
    safety_resources = [
         {"title": "Find Your Company Safety Portal", "description": "Access official documents, forms, and schedules (Internal).", "link": "https://services.india.gov.in/service/listing?ln=en&cat_id=52", "image": "https://plus.unsplash.com/premium_photo-1733873203119-97d2b9b5c5a6?w=600&auto=format&fit=crop&q=60&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MXx8Y29tYW55JTIwc2FmZXR5JTIwcG9ydGFsfGVufDB8fDB8fHww"}, # Link placeholder

         {"title": "Government Safety Agency", "description": "Public safety guidelines (e.g., HSE, OSHA, CCOHS - check your region).", "link": "https://www.hpae.org/issues/health-and-safety/health-safety-organizations-government-agencies/", "image": "https://i.pinimg.com/736x/c0/1d/a7/c01da741f818e21178710904e3a9dfe6.jpg"},

         {"title": "First Aid Providers", "description": "Find certified training (e.g., Red Cross, St John Ambulance).", "link": "https://www.indianredcross.org/ircs/program/FirstAid", "image": "https://www.indianredcross.org/ircs/sites/default/files/inline-images/FirstAid.jpg"},

         {"title": "Learn About Risk Assessment", "description": "Understanding workplace hazard evaluation.", "link": "https://www.greenwgroup.com/corporate-courses/understanding-hazards-in-the-workplace/", "image": "https://i.pinimg.com/736x/f2/bd/b9/f2bdb9ae1fab1ed021c3d4aadfd17bff.jpg"}
    ]
    # --- End Resource Links ---

    if USE_DEMO_MODE:
        initial_bot_message = DEMO_WELCOME_MESSAGE
    else:
        # Static intro reflecting the new role
        initial_bot_message = "Welcome! I'm SafetyTrainPro, your chatbot assistant. Let me know how I can assist you today:)"

    return render_template('index.html',
                           recommended_videos=recommended_videos,
                           safety_resources=safety_resources,
                           initial_bot_message=initial_bot_message)

@app.route('/chat', methods=['POST'])
def chat():
    """Handles chat requests - NO HISTORY. Uses the NEW system instruction."""
    global USE_DEMO_MODE

    try:
        user_message = request.json.get('message', '').strip()
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400

        bot_message = None
        current_mode_is_demo = USE_DEMO_MODE

        # --- Attempt API Call ---
        if not current_mode_is_demo and MODEL:
            try:
                logger.debug(f"Sending message to API (Enhanced Safety): {user_message}")
                # Model uses the system_instruction provided during initialization
                response = MODEL.generate_content(
                    user_message,
                    generation_config={'candidate_count': 1}
                )

                if not response.candidates:
                    logger.warning(f"API response potentially blocked. Feedback: {response.prompt_feedback}")
                    bot_message = "I cannot provide a response to that request. It may be outside my safety scope or potentially unsafe content. Please rephrase."
                else:
                    bot_message = response.text
                    logger.debug(f"Received API response: {bot_message[:100]}...")

            except google.api_core.exceptions.ResourceExhausted as e:
                logger.error(f"RATE LIMIT ERROR: {e}")
                bot_message = DEMO_RATE_LIMIT_RESPONSE
            except Exception as e:
                logger.error(f"Error during API call: {e}", exc_info=True)
                current_mode_is_demo = True
                bot_message = DEMO_GENERAL_RESPONSE

        # --- Use Demo Responses ---
        if current_mode_is_demo or bot_message is None:
             if bot_message is None:
                bot_message = DEMO_GENERAL_RESPONSE
                for key, response_text in DEMO_RESPONSES.items():
                    if key.lower() in user_message.lower():
                        bot_message = response_text
                        break

        # --- Return Single Response ---
        return jsonify({'message': bot_message})

    except Exception as e:
        logger.error(f"Generic error in /chat endpoint: {e}", exc_info=True)
        error_message = "An unexpected error occurred. Please try again."
        return jsonify({'message': error_message}), 500

# --- Main Execution Block ---
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

# --- END OF FILE app.py ---
