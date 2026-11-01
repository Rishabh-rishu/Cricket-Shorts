"""
Professional Cricket Shorts Script Generator
Structures high-retention 30-45s scripts:
- Hook (0-3s): Curiosity-driven opener
- Story (3-28s): Fast-paced, conversational sports documentary narrative
- Surprise (28-38s): Unexpected detail / climax
- CTA (38-42s): Comment-trigger question
"""

from typing import Dict, Any
import re


HOOK_TEMPLATES = [
    "क्रिकेट इतिहास का एक ऐसा अनोखा नियम, जिसके बारे में 99% फैंस नहीं जानते!",
    "क्या आप जानते हैं क्रिकेट में एक ऐसा नियम भी है जो पूरा मैच पलट सकता है?",
    "क्रिकेट का यह रिकॉर्ड सुनकर आप पूरी तरह हैरान रह जाएंगे!",
    "क्या आपको पता है इस दिग्गज खिलाड़ी का यह रिकॉर्ड आज तक कोई नहीं तोड़ पाया?",
    "क्रिकेट के मैदान पर हुई यह घटना इतिहास में केवल एक ही बार घटी है!",
    "इस चौंकाने वाले क्रिकेट रिकॉर्ड के पीछे का सच बहुत कम लोग जानते हैं!"
]

CTA_TEMPLATES = [
    "क्या आप इस हैरान कर देने वाले फैक्ट के बारे में पहले जानते थे? कमेंट्स में जरूर बताएं और ऐसे ही अनसुने क्रिकेट फैक्ट्स के लिए सब्सक्राइब करें!",
    "क्या आपके हिसाब से क्रिकेट में यह नियम सही है? अपनी राय कमेंट्स में लिखें और चैनल को अभी सब्सक्राइब करें!",
    "क्रिकेट का कौन सा अनसुना रिकॉर्ड आपको सबसे ज्यादा चौंकाता है? कमेंट्स में बताएं और सब्सक्राइब करना न भूलें!"
]


class ScriptGenerator:
    @classmethod
    def generate(cls, fact_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Creates a structured, timed Hindi script for a YouTube Short based on the verified fact.
        """
        topic = fact_data.get("topic", "")
        category = fact_data.get("category", "")
        main_fact = fact_data.get("main_fact", "")

        # Select dynamic Hook based on category
        if "rules" in category.lower():
            hook = "क्रिकेट के नियमों की किताब में एक ऐसा गुप्त नियम छुपा है, जिसके बारे में 99% फैंस नहीं जानते!"
        elif "ipl" in category.lower():
            hook = "IPL इतिहास का एक ऐसा अनसुना रिकॉर्ड, जिस पर यकीन करना नामुमकिन लगता है!"
        elif "world cup" in category.lower():
            hook = "वर्ल्ड कप के इतिहास का यह सबसे बड़ा उलटफेर आपको हैरान कर देगा!"
        elif "legendary" in category.lower():
            hook = "क्रिकेट के इस महानतम खिलाड़ी का एक ऐसा सच, जिसे जानकर आपके होश उड़ जाएंगे!"
        else:
            hook = "क्रिकेट इतिहास का यह हैरान कर देने वाला सच बहुत कम लोग जानते हैं!"

        # Build Main Story
        # Clean and expand main_fact for spoken Hindi cadence
        cleaned_fact = main_fact.strip()
        story = f"बात दरअसल यह है कि {cleaned_fact}"

        # Build Surprise element
        if "helmet" in main_fact.lower() or "हेलमेट" in main_fact:
            surprise = "यानी अगर फील्डर का रखा हुआ हेलमेट गेंद से छू भी जाए, तो अंपायर तुरंत हाथ उठाकर 5 रन पेनल्टी दे देता है और गेंद तुरंत डेड हो जाती है."
        elif "timed out" in main_fact.lower() or "टाइम आउट" in main_fact:
            surprise = "मैथ्यूज के हेलमेट का स्ट्रैप टूट गया था, लेकिन ICC नियमों के अनुसार 2 मिनट का समय खत्म होते ही विपक्षी कप्तान ने अपील की और अंपायर को आउट देना पड़ा."
        elif "गावस्कर" in main_fact or "gavaskar" in main_fact.lower():
            surprise = "पूरे 60 ओवर बल्लेबाजी करने के बाद भी भारत यह मुकाबला 202 रनों के भारी अंतर से हार गया था, जो आज भी वर्ल्ड कप का सबसे रहस्यमयी मैच माना जाता है."
        elif "सचिन" in main_fact or "tendulkar" in main_fact.lower():
            surprise = "उस दिन जावेद मियांदाद मैदान छोड़कर चले गए थे, और सिर्फ 14 साल के सचिन तेंदुलकर इमरान खान की कप्तानी में पाकिस्तान के लिए फील्डिंग कर रहे थे."
        elif "रोहित" in main_fact or "rohit" in main_fact.lower():
            surprise = "रोहित शर्मा ने केवल 2 ओवरों में सिर्फ 6 रन देकर 4 विकेट चटकाए थे, और उस साल डेक्कन चार्जर्स ने IPL का खिताब भी जीता था."
        elif "धोनी" in main_fact or "dhoni" in main_fact.lower():
            surprise = "धोनी ने सेना देशों यानी साउथ अफ्रीका, इंग्लैंड, न्यूजीलैंड और ऑस्ट्रेलिया में कई यादगार पारियां खेलीं, लेकिन 90 टेस्ट मैचों में उनका कोई टेस्ट शतक वहां नहीं लगा."
        elif "बुमराह" in main_fact or "bumrah" in main_fact.lower():
            surprise = "स्टुअर्ट ब्रॉड वही गेंदबाज हैं जिनके ओवर में युवराज सिंह ने 6 छक्के जड़े थे, और 15 साल बाद बुमराह ने उनके खिलाफ एक ओवर में 35 रन कूट दिए."
        else:
            surprise = "क्रिकेट के रिकॉर्ड्स में ऐसी घटनाएं दशकों में सिर्फ एक बार देखने को मिलती हैं."

        # Select CTA
        cta = CTA_TEMPLATES[hash(topic) % len(CTA_TEMPLATES)]

        # Combine into complete script with natural pauses
        full_script = f"{hook} {story} {surprise} {cta}"

        # Clean multiple spaces
        full_script = re.sub(r'\s+', ' ', full_script).strip()

        return {
            "hook": hook,
            "story": story,
            "surprise": surprise,
            "cta": cta,
            "full_script": full_script,
            "word_count": len(full_script.split()),
            "estimated_duration_sec": round(len(full_script.split()) / 2.8, 1) # At ~165 wpm (1.2x)
        }
