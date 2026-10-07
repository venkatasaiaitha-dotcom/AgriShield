#!/usr/bin/env python3
"""
Enrich data/i18n.json with loans, weather resources, step-by-step guidance,
and AI chatbot dialogues across all 6 languages.
"""

import json
import os

filepath = os.path.join(os.path.dirname(__file__), "data", "i18n.json")
with open(filepath, "r", encoding="utf-8") as f:
    data = json.load(f)

ui_additions = {
    "ta": {
        "weather_title": "வானிலை & செயற்கைக்கோள் வளங்கள்",
        "weather_subtitle": "சென்டினல்-1 ரேடார் ஈரப்பதம், மழை முன்னறிவிப்பு & பயிர் ஆலோசனைகள்",
        "chatbot_title": "அக்ரிஷீல்ட் AI உதவியாளர் (Chatbot)",
        "chatbot_subtitle": "பயிர் நலம், வானிலை, இழப்பீடு மற்றும் பயிர் கடன்கள் பற்றி கேளுங்கள்",
        "loan_portal_title": "பயிர் கடன் & பேரிடர் நிவாரண போர்டல்",
        "apply_loan_btn": "📝 உடனே கடன் / நிவாரணத்திற்கு விண்ணப்பிக்கவும்",
        "damage_mapping_title": "எந்த பாதிப்பிற்கு எந்த கடன் / நிவாரணம் கிடைக்கும்?",
        "requirements_title": "தேவையான ஆவணங்கள் & தகுதிகள்",
        "where_apply_title": "எங்கே விண்ணப்பிக்க வேண்டும்?",
        "first_step_title": "விவசாயி எடுக்க வேண்டிய முதல் நடவடிக்கை (First Step)",
        "loan_app_modal_title": "பயிர் கடன் / பேரிடர் நிவாரண விண்ணப்பம்",
        "satellite_proof_attached": "செயற்கைக்கோள் சேத அறிக்கை தானாக இணைக்கப்பட்டுள்ளது",
        "submit_application": "விண்ணப்பத்தைச் சமர்ப்பிக்கவும்",
        "application_success": "விண்ணப்பம் வெற்றிகரமாகப் பதிவு செய்யப்பட்டது!",
        "chat_placeholder": "பயிர் நலம், மழை, கடன் பற்றி தமிழில் தட்டச்சு செய்யவும் அல்லது பேசவும்...",
        "suggestion_title": "இன்றைய பயிர் ஆலோசனை:"
    },
    "hi": {
        "weather_title": "मौसम और उपग्रह संसाधन",
        "weather_subtitle": "सेंटिनल-1 रडार मिट्टी की नमी, वर्षा पूर्वानुमान और कृषि सलाह",
        "chatbot_title": "एग्रीशील्ड AI सहायक (Chatbot)",
        "chatbot_subtitle": "फसल स्वास्थ्य, मौसम, क्षति और कृषि ऋण के बारे में पूछें",
        "loan_portal_title": "कृषि ऋण एवं आपदा राहत पोर्टल",
        "apply_loan_btn": "📝 तुरंत ऋण / राहत के लिए आवेदन करें",
        "damage_mapping_title": "किस नुकसान पर कौन सा ऋण / राहत मिलेगी?",
        "requirements_title": "आवश्यक दस्तावेज और पात्रता",
        "where_apply_title": "आवेदन कहाँ करें?",
        "first_step_title": "किसान को सबसे पहला कदम क्या उठाना चाहिए?",
        "loan_app_modal_title": "कृषि ऋण / आपदा राहत आवेदन फॉर्म",
        "satellite_proof_attached": "उपग्रह क्षति सत्यापन रिपोर्ट स्वतः संलग्न",
        "submit_application": "आवेदन जमा करें",
        "application_success": "आवेदन सफलतापूर्वक दर्ज कर लिया गया!",
        "chat_placeholder": "फसल, बारिश, ऋण के बारे में हिन्दी में पूछें...",
        "suggestion_title": "आज की फसल सलाह:"
    },
    "te": {
        "weather_title": "వాతావరణం & ఉపగ్రహ వనరులు",
        "weather_subtitle": "సెంటినెల్-1 రాడార్ తేమ, వర్షపాత సూచన మరియు పంట సూచనలు",
        "chatbot_title": "అగ్రిషీల్డ్ AI సహాయకుడు (Chatbot)",
        "chatbot_subtitle": "పంట ఆరోగ్యం, వాతావరణం మరియు వ్యవసాయ రుణాల గురించి అడగండి",
        "loan_portal_title": "పంట రుణాలు & విపత్తు సహాయ పోర్టల్",
        "apply_loan_btn": "📝 వెంటనే రుణం / సహాయం కోసం దరఖాస్తు చేయండి",
        "damage_mapping_title": "ఏ నష్టానికి ఏ రుణం వర్తిస్తుంది?",
        "requirements_title": "అవసరమైన పత్రాలు & అర్హతలు",
        "where_apply_title": "ఎక్కడ దరఖాస్తు చేయాలి?",
        "first_step_title": "రైతు తీసుకోవలసిన మొదటి చర్య (First Step)",
        "loan_app_modal_title": "పంట రుణం / విపత్తు సహాయ దరఖాస్తు",
        "satellite_proof_attached": "ఉపగ్రహ నష్ట నివేదిక ఆటోమేటిక్‌గా జతచేయబడింది",
        "submit_application": "దరఖాస్తు సమర్పించండి",
        "application_success": "దరఖాస్తు విజయవంతంగా నమోదైంది!",
        "chat_placeholder": "పంట, వర్షం, రుణాల గురించి తెలుగులో అడగండి...",
        "suggestion_title": "నేటి పంట సలహా:"
    },
    "kn": {
        "weather_title": "ಹವಾಮಾನ ಮತ್ತು ಉಪಗ್ರಹ ಸಂಪನ್ಮೂಲಗಳು",
        "weather_subtitle": "ಸೆಂಟಿನೆಲ್-1 ರಾಡಾರ್ ತೇವಾಂಶ, ಮಳೆ ಮುನ್ಸೂಚನೆ ಮತ್ತು ಕೃಷಿ ಸಲಹೆಗಳು",
        "chatbot_title": "ಅಗ್ರಿಶೀಲ್ಡ್ AI ಸಹಾಯಕ (Chatbot)",
        "chatbot_subtitle": "ಬೆಳೆ ಆರೋಗ್ಯ, ಹವಾಮಾನ ಮತ್ತು ಕೃಷಿ ಸಾಲಗಳ ಬಗ್ಗೆ ಕೇಳಿ",
        "loan_portal_title": "ಬೆಳೆ ಸಾಲ ಮತ್ತು ವಿಪತ್ತು ಪರಿಹಾರ ಪೋರ್ಟಲ್",
        "apply_loan_btn": "📝 ತಕ್ಷಣವೇ ಸಾಲ / ಪರಿಹಾರಕ್ಕೆ ಅರ್ಜಿ ಸಲ್ಲಿಸಿ",
        "damage_mapping_title": "ಯಾವ ಹಾನಿಗೆ ಯಾವ ಸಾಲ ಲಭ್ಯವಿದೆ?",
        "requirements_title": "ಅಗತ್ಯವಿರುವ ದಾಖಲೆಗಳು ಮತ್ತು ಅರ್ಹತೆ",
        "where_apply_title": "ಎಲ್ಲಿ ಅರ್ಜಿ ಸಲ್ಲಿಸಬೇಕು?",
        "first_step_title": "ರೈತರು ತೆಗೆದುಕೊಳ್ಳಬೇಕಾದ ಮೊದಲ ಹೆಜ್ಜೆ",
        "loan_app_modal_title": "ಕೃಷಿ ಸಾಲ / ಪರಿಹಾರ ಅರ್ಜಿ ನಮೂನೆ",
        "satellite_proof_attached": "ಉಪಗ್ರಹ ಹಾನಿ ವರದಿ ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಲಗತ್ತಿಸಲಾಗಿದೆ",
        "submit_application": "ಅರ್ಜಿ ಸಲ್ಲಿಸಿ",
        "application_success": "ಅರ್ಜಿಯನ್ನು ಯಶಸ್ವಿಯಾಗಿ ಸಲ್ಲಿಸಲಾಗಿದೆ!",
        "chat_placeholder": "ಬೆಳೆ, ಮಳೆ, ಸಾಲದ ಬಗ್ಗೆ ಕನ್ನಡದಲ್ಲಿ ಕೇಳಿ...",
        "suggestion_title": "ಇಂದಿನ ಬೆಳೆ ಸಲಹೆ:"
    },
    "ml": {
        "weather_title": "കാലാവസ്ഥയും ഉപഗ്രഹ വിഭവങ്ങളും",
        "weather_subtitle": "സെന്റിനൽ-1 റഡാർ ഈർപ്പം, മഴ പ്രവചനം, കാർഷിക നിർദ്ദേശങ്ങൾ",
        "chatbot_title": "അഗ്രിഷീൽഡ് AI സഹായി (Chatbot)",
        "chatbot_subtitle": "വിള ആരോഗ്യം, കാലാവസ്ഥ, വായ്പകൾ എന്നിവയെക്കുറിച്ച് ചോദിക്കുക",
        "loan_portal_title": "വിള വായ്പയും ദുരന്ത നിവാരണ പോർട്ടലും",
        "apply_loan_btn": "📝 ഉടൻ വായ്പയ്ക്ക് / ആശ്വാസത്തിന് അപേക്ഷിക്കുക",
        "damage_mapping_title": "ഏത് നാശനഷ്ടത്തിന് ഏത് വായ്പ ലഭിക്കും?",
        "requirements_title": "ആവശ്യമായ രേഖകളും യോഗ്യതകളും",
        "where_apply_title": "എവിടെ അപേക്ഷിക്കണം?",
        "first_step_title": "കർഷകൻ ആദ്യം ചെയ്യേണ്ട നടപടി",
        "loan_app_modal_title": "വിള വായ്പ / ആശ്വാസ അപേക്ഷാ ഫോം",
        "satellite_proof_attached": "ഉപഗ്രഹ നാശനഷ്ട റിപ്പോർട്ട് സ്വമേധയാ ചേർത്തു",
        "submit_application": "അപേക്ഷ സമർപ്പിക്കുക",
        "application_success": "അപേക്ഷ വിജയകരമായി സമർപ്പിച്ചു!",
        "chat_placeholder": "വിള, മഴ, വായ്പ എന്നിവയെക്കുറിച്ച് മലയാളത്തിൽ ചോദിക്കൂ...",
        "suggestion_title": "ഇന്നത്തെ കാർഷിക നിർദ്ദേശം:"
    },
    "en": {
        "weather_title": "Weather & Satellite Resources",
        "weather_subtitle": "Sentinel-1 Radar Moisture, Rainfall Forecast & Agro-Meteorological Advisories",
        "chatbot_title": "AgriShield AI Assistant",
        "chatbot_subtitle": "Ask questions to analyze crop health, weather, and farm credit decisions",
        "loan_portal_title": "Crop Loans & Disaster Relief Portal",
        "apply_loan_btn": "📝 Apply for Loan / Relief Now",
        "damage_mapping_title": "For Which Damage What Loan Applies?",
        "requirements_title": "Required Documents & Eligibility",
        "where_apply_title": "Where to Apply?",
        "first_step_title": "First Step You Must Take",
        "loan_app_modal_title": "Agricultural Credit & Relief Application",
        "satellite_proof_attached": "Satellite Damage Verification Report Auto-Attached",
        "submit_application": "Submit Application",
        "application_success": "Application Successfully Registered!",
        "chat_placeholder": "Ask about crop health, rain, flood, or loans...",
        "suggestion_title": "Today's Agronomy Suggestion:"
    }
}

# New Intent definitions
new_intents = {
    "loan_advice": {
        "keywords": ["loan", "credit", "kcc", "relief", "money", "scheme", "apply", "subsidy", "கடன்", "நிவாரணம்", "லோன்", "ऋण", "कर्ज", "రుణం", "సహాయం", "ಸಾಲ", "ಪರಿಹಾರ", "വായ്പ", "ആശ്വാസം"],
        "answers": {
            "plot_1": "Farmer Murugan: For your 78% flood damage, you are eligible for the PMFBY Flood Mid-Season Claim (up to ₹30,000/acre grant) and KCC Emergency Debt Rescheduling for 3-5 years. First step: Download the AgriShield Satellite Report and submit it at Punnainallur PACCS society within 72 hours.",
            "plot_2": "Farmer Lakshmi: For your 30% partial flood impact, you qualify for the KCC Emergency Working Capital Top-Up (₹40,000) and PMFBY partial yield claim. First step: Request a joint inspection endorsement with your AgriShield report at Kallaperambur Cooperative Bank.",
            "plot_3": "Farmer Selvam: Because your crop is 100% healthy, you qualify for the Standard Kisan Credit Card (KCC) Crop Loan up to ₹3,00,000 at 4% subsidized interest or Agriculture Infrastructure Fund (AIF) for solar pumps. First step: Apply online on JanSamarth portal or visit SBI Vallam branch."
        }
    },
    "loan_requirements": {
        "keywords": ["documents", "requirement", "papers", "patta", "aadhaar", "ஆவணங்கள்", "தேவை", "பட்டா", "दस्तावेज", "कागजात", "పత్రాలు", "పాస్ బుక్", "ದಾಖಲೆಗಳು", "രേഖകൾ"],
        "answers": {
            "plot_1": "Documents required: 1. Aadhaar Card, 2. Land Patta / Chitta / Adangal, 3. Bank Passbook copy, 4. AgriShield Satellite Damage Report PDF, and 5. Sowing enrollment receipt.",
            "plot_2": "Documents required: 1. Aadhaar Card, 2. Land Patta / Chitta / Adangal, 3. Bank Passbook copy, 4. AgriShield Satellite Damage Report PDF, and 5. Sowing enrollment receipt.",
            "plot_3": "Documents required: 1. Aadhaar Card, 2. Land Patta / Chitta / Adangal, 3. Bank Passbook copy, 4. AgriShield Satellite Damage Report PDF, and 5. Sowing enrollment receipt."
        }
    },
    "first_step": {
        "keywords": ["first step", "what to do first", "procedure", "முதல் படி", "முதலில் என்ன", "पहला कदम", "మొదటి అడుగు", "ಮೊದಲ ಹೆಜ್ಜೆ", "ആദ്യ പടി"],
        "answers": {
            "plot_1": "FIRST STEP: 1. Click 'Download Claim PDF' to get your satellite proof. 2. Notify your Village Administrative Officer (VAO) within 72 hours. 3. Click 'Apply for Loan' to register your claim instantly.",
            "plot_2": "FIRST STEP: 1. Open field drainage channels. 2. Download your AgriShield satellite report. 3. File a partial claim with your local cooperative bank.",
            "plot_3": "FIRST STEP: 1. Maintain scheduled irrigation for 3 more days. 2. Drain field 10 days before harvest. 3. Apply for seasonal KCC credit for the upcoming cycle."
        }
    },
    "weather_advice": {
        "keywords": ["weather", "forecast", "rain", "temperature", "humidity", "வானிலை", "மழை", "வெப்பநிலை", "मौसम", "बारिश", "వాతావరణం", "వర్షం", "ಹವಾಮಾನ", "ಮಳೆ", "കാലാവസ്ഥ", "മഴ"],
        "answers": {
            "plot_1": "Weather update: Northeast monsoon rain recorded 210mm with 94% humidity. Satellite shows high soil saturation. Sluices must remain open to flush standing floodwater.",
            "plot_2": "Weather update: 210mm monsoon storm passed. Humidity 94%. Drainage is functioning well. Plan for 1% Potassium Chloride foliar spray once water drops below 2cm.",
            "plot_3": "Weather update: Clear skies, temperature 29°C, humidity 72%, rainfall 10mm. Ideal grain-filling weather. No adverse meteorological risk detected."
        }
    }
}

# Update language dictionaries
for lang, additions in ui_additions.items():
    if lang in data["languages"]:
        data["languages"][lang]["ui"].update(additions)
        # Add quick buttons for loans and weather
        data["languages"][lang]["quick_buttons"]["loan_info"] = {
            "label": "கடன் & நிவாரணம்" if lang=="ta" else ("ऋण व राहत" if lang=="hi" else ("పంట రుణాలు" if lang=="te" else ("ಬೆಳೆ ಸಾಲ" if lang=="kn" else ("വിള വായ്പ" if lang=="ml" else "Loans & Relief")))),
            "icon": "🏦",
            "question": "எனக்கு என்ன கடன் கிடைக்கும்?" if lang=="ta" else ("मुझे कौन सा ऋण मिल सकता है?" if lang=="hi" else ("నాకు ఏ రుణం వస్తుంది?" if lang=="te" else ("ನನಗೆ ಯಾವ ಸಾಲ ಸಿಗುತ್ತದೆ?" if lang=="kn" else ("എനിക്ക് എന്ത് വായ്പ ലഭിക്കും?" if lang=="ml" else "What loan can I get for my crop?"))))
        }
        data["languages"][lang]["quick_buttons"]["weather_info"] = {
            "label": "வானிலை தகவல்" if lang=="ta" else ("मौसम पूर्वानुमान" if lang=="hi" else ("వాతావరణ సమాచారం" if lang=="te" else ("ಹವಾಮಾನ ಮಾಹಿತಿ" if lang=="kn" else ("കാലാവസ്ഥ വിവരം" if lang=="ml" else "Weather Info")))),
            "icon": "🌦️",
            "question": "இன்றைய வானிலை எப்படி உள்ளது?" if lang=="ta" else ("आज का मौसम कैसा है?" if lang=="hi" else ("ఈ రోజు వాతావరణం ఎలా ఉంది?" if lang=="te" else ("ಇಂದಿನ ಹವಾಮಾನ ಹೇಗಿದೆ?" if lang=="kn" else ("ഇന്നത്തെ കാലാവസ്ഥ എങ്ങനെയുണ്ട്?" if lang=="ml" else "What is the weather and satellite status?"))))
        }
        # Add new intents
        for intent_name, intent_obj in new_intents.items():
            data["languages"][lang]["intents"][intent_name] = intent_obj

with open(filepath, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Updated data/i18n.json successfully with loan, weather, and AI chatbot data!")
