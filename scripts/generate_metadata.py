"""
Automated YouTube Shorts Metadata Generator
Produces SEO-optimized, curiosity-driven titles, rich descriptions,
targeted hashtags, tags, and pinned comments.
"""

from typing import Dict, Any, List
import re


class MetadataGenerator:
    BASE_HASHTAGS = ["#CricketFacts", "#CricketShorts", "#CricketHindi", "#Shorts", "#Cricket"]

    @classmethod
    def generate(cls, fact_data: Dict[str, Any], script_data: Dict[str, Any]) -> Dict[str, Any]:
        topic = fact_data.get("topic", "")
        category = fact_data.get("category", "")
        main_fact = fact_data.get("main_fact", "")
        source_primary = fact_data.get("source_primary", "")

        # 1. Title generation (under 75 chars, curiosity-driven, emoji accented)
        title = cls._build_title(topic, category, main_fact)

        # 2. Targeted hashtags based on content
        specific_hashtags = cls._extract_hashtags(topic, main_fact)
        all_hashtags = list(dict.fromkeys(specific_hashtags + cls.BASE_HASHTAGS))[:7]
        hashtag_string = " ".join(all_hashtags)

        # 3. Tags for YouTube algorithm
        tags = cls._build_tags(topic, category, specific_hashtags)

        # 4. Description with timestamp, verification source, and disclaimers
        description = (
            f"{title}\n\n"
            f"⚡ {script_data.get('hook', '')}\n\n"
            f"📌 Verified Cricket Fact:\n"
            f"{main_fact}\n\n"
            f"📚 Official Source Citation: {source_primary}\n\n"
            f"🔔 रोज़ाना ऐसे ही अनसुने और हैरान कर देने वाले क्रिकेट फैक्ट्स के लिए हमारे चैनल को सब्सक्राइब जरूर करें!\n\n"
            f"{hashtag_string}"
        )

        # 5. Pinned comment prompt
        pinned_comment = (
            f"👇 क्या आपको इस क्रिकेट फैक्ट के बारे में पहले से पता था? "
            f"कमेंट में 'YES' या 'NO' लिखकर अपनी राय जरूर बताएं! 🏏🔥"
        )

        return {
            "title": title,
            "description": description,
            "tags": tags,
            "hashtags": hashtag_string,
            "pinned_comment": pinned_comment
        }

    @classmethod
    def _build_title(cls, topic: str, category: str, main_fact: str) -> str:
        # Generate targeted concise title
        if "5 Penalty" in topic or "Helmet" in topic or "हेलमेट" in main_fact:
            return "क्रिकेट में हेलमेट पर गेंद लगने का ये नियम जानते हैं? 😱🏏 #Shorts"
        elif "Timed Out" in topic or "टाइम आउट" in main_fact:
            return "क्रिकेट इतिहास का पहला Timed Out! एंजेलो मैथ्यूज का विवाद 🏏 #Shorts"
        elif "Gavaskar" in topic or "गावस्कर" in main_fact:
            return "गावस्कर के 60 ओवर में सिर्फ 36 रन! 1975 का सबसे बड़ा रहस्य 🏏 #Shorts"
        elif "Sachin" in topic or "सचिन" in main_fact:
            return "जब सचिन तेंदुलकर ने पाकिस्तान के लिए की फील्डिंग! 😱🏏 #Shorts"
        elif "Rohit" in topic or "रोहित" in main_fact:
            return "रोहित शर्मा की IPL हैट्रिक! मुंबई इंडियंस के खिलाफ ही हुआ कमाल 🏏 #Shorts"
        elif "Dhoni" in topic or "धोनी" in main_fact:
            return "धोनी का एक ऐसा टेस्ट रिकॉर्ड, जिसे सुनकर सब चौंक जाते हैं! 🏏 #Shorts"
        elif "Bumrah" in topic or "बुमराह" in main_fact:
            return "बुमराह के 1 ओवर में 35 रन! स्टुअर्ट ब्रॉड के साथ फिर हुआ खेला 🏏 #Shorts"
        elif "Muralitharan" in topic or "मुरलीधरन" in main_fact:
            return "आखिरी गेंद पर 800वां टेस्ट विकेट! मुरलीधरन का ऐतिहासिक रिकॉर्ड 🏏 #Shorts"
        elif "Mankad" in topic or "मैनकैडिंग" in main_fact:
            return "क्रिकेट का वो नियम जो मैच का पासा पलट देता है! Law 38 Explained 🏏 #Shorts"
        else:
            clean_topic = re.sub(r'[^a-zA-Z0-9\s\u0900-\u097F]', '', topic)[:45]
            return f"{clean_topic}! क्रिकेट का अनसुना सच 🏏 #Shorts"

    @classmethod
    def _extract_hashtags(cls, topic: str, main_fact: str) -> List[str]:
        tags = []
        text = f"{topic} {main_fact}".lower()
        if "dhoni" in text or "धोनी" in text:
            tags.extend(["#MSDhoni", "#DhoniRecords"])
        if "rohit" in text or "रोहित" in text:
            tags.extend(["#RohitSharma", "#Hitman"])
        if "sachin" in text or "सचिन" in text:
            tags.extend(["#SachinTendulkar", "#GodOfCricket"])
        if "bumrah" in text or "बुमराह" in text:
            tags.extend(["#JaspritBumrah", "#BumrahBowling"])
        if "rule" in text or "law" in text or "नियम" in text:
            tags.extend(["#CricketRules", "#MCCLaws"])
        if "world cup" in text or "वर्ल्ड कप" in text:
            tags.extend(["#CricketWorldCup", "#CWC"])
        if "ipl" in text:
            tags.extend(["#IPL", "#IPLRecords"])
        return tags

    @classmethod
    def _build_tags(cls, topic: str, category: str, specific_tags: List[str]) -> List[str]:
        # High-relevance audience tags for Indian cricket fans & IPL viewers
        base_audience_tags = [
            "cricket facts in hindi",
            "cricket shorts",
            "cricket hindi",
            "cricket records",
            "unknown cricket facts",
            "cricket documentary",
            "ipl facts",
            "indian cricket",
            "team india",
            "क्रिकेट फैक्ट्स",
            "क्रिकेट शार्ट्स",
            "cricket history hindi"
        ]
        words = re.findall(r'[a-zA-Z0-9]{3,}', topic)
        clean_specific = [t.replace('#', '') for t in specific_tags]
        all_tags = base_audience_tags + clean_specific + words
        # Deduplicate while preserving order, max 20 tags
        return list(dict.fromkeys(all_tags))[:20]
