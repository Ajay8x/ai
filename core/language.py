"""
AJAX AI - Multilingual Normalizer & Language Intelligence
Enables understanding across English, Hinglish, and Hindi (Devanagari & Romanized).
Transliterates phonetic Devanagari to English and extracts clean core queries.
"""

import re
from typing import Tuple, Dict

# Common phonetic Devanagari to English mapping
PHONETIC_DEVANAGARI_WORDS: Dict[str, str] = {
    "व्हाट": "what",
    "वाट": "what",
    "व्हाय": "why",
    "व्हेन": "when",
    "व्हेयर": "where",
    "हाउ": "how",
    "हू": "who",
    "हु": "who",
    "इस": "is",
    "आर": "are",
    "एम": "am",
    "दी": "the",
    "द": "the",
    "ए": "a",
    "एन": "an",
    "ऑफ": "of",
    "फॉर": "for",
    "टू": "to",
    "इन": "in",
    "ऑन": "on",
    "विद": "with",
    
    # Common topics & objects
    "बनाना": "banana",
    "केला": "banana",
    "एप्पल": "apple",
    "सेब": "apple",
    "मैंगो": "mango",
    "आम": "mango",
    "ऑरेंज": "orange",
    "संतरा": "orange",
    "कंप्यूटर": "computer",
    "इंटरनेट": "internet",
    "मोबाइल": "mobile",
    "फोन": "phone",
    "पायथन": "python",
    "जावा": "java",
    "गूगल": "google",
    "यूट्यूब": "youtube",
    "क्रोम": "chrome",
    "फेसबुक": "facebook",
    "इंस्टाग्राम": "instagram",
    "ट्विटर": "twitter",
    "व्हाट्सएप": "whatsapp",
    "वेदर": "weather",
    "मौसम": "weather",
    "टाइम": "time",
    "समय": "time",
    "घड़ी": "clock",
    "तारीख": "date",
    "दिन": "day",
    "न्यूज": "news",
    "खबर": "news",
    "कैलकुलेट": "calculate",
    "सर्च": "search",
    "खोजो": "search",
    "ओपन": "open",
    "खोलो": "open",
    "क्लोज": "close",
    "बंद": "close",
    "करो": "do",
    "प्ले": "play",
    "चलाओ": "play",
    "गाना": "song",
    "म्यूजिक": "music",
    "वीडियो": "video",
    "हेल्प": "help",
    "मदद": "help",
}

# Devanagari character to Latin transliteration
CONSONANTS = {
    'क': 'k', 'ख': 'kh', 'ग': 'g', 'घ': 'gh', 'ङ': 'ng',
    'च': 'ch', 'छ': 'chh', 'ज': 'j', 'झ': 'jh', 'ञ': 'ny',
    'ट': 't', 'ठ': 'th', 'ड': 'd', 'ढ': 'dh', 'ण': 'n',
    'त': 't', 'थ': 'th', 'द': 'd', 'ध': 'dh', 'न': 'n',
    'प': 'p', 'फ': 'f', 'ब': 'b', 'भ': 'bh', 'म': 'm',
    'य': 'y', 'र': 'r', 'ल': 'l', 'व': 'v', 'श': 'sh',
    'ष': 'sh', 'स': 's', 'ह': 'h', 'क्ष': 'ksh', 'त्र': 'tr', 'ज्ञ': 'gy'
}

VOWELS = {
    'अ': 'a', 'आ': 'aa', 'इ': 'i', 'ई': 'ee', 'उ': 'u', 'ऊ': 'oo',
    'ऋ': 'ri', 'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au',
    'ऑ': 'o', 'ऍ': 'e'
}

MATRAS = {
    'ा': 'a', 'ि': 'i', 'ी': 'ee', 'ु': 'u', 'ू': 'oo',
    'ृ': 'ri', 'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au',
    'ॉ': 'o', 'ॅ': 'e', 'ं': 'n', 'ँ': 'n', 'ः': 'h', '्': ''
}

def transliterate_devanagari_to_roman(text: str) -> str:
    """Converts Devanagari text to readable phonetic Roman/English text."""
    # First check word-level dictionary
    words = text.split()
    translated_words = []
    for w in words:
        clean_w = re.sub(r'[^\u0900-\u097F]', '', w)
        if clean_w in PHONETIC_DEVANAGARI_WORDS:
            translated_words.append(PHONETIC_DEVANAGARI_WORDS[clean_w])
        else:
            # Character level transliteration
            roman = ""
            i = 0
            n = len(w)
            while i < n:
                ch = w[i]
                if ch in VOWELS:
                    roman += VOWELS[ch]
                elif ch in CONSONANTS:
                    c_sound = CONSONANTS[ch]
                    # Check next character for matra or halant
                    if i + 1 < n and w[i + 1] in MATRAS:
                        roman += c_sound + MATRAS[w[i + 1]]
                        i += 1
                    elif i + 1 < n and w[i + 1] == '्': # Halant (half consonant)
                        roman += c_sound
                        i += 1
                    else:
                        roman += c_sound + ('a' if i + 1 < n and w[i + 1] in CONSONANTS else '')
                elif ch in MATRAS:
                    roman += MATRAS[ch]
                else:
                    roman += ch
                i += 1
            translated_words.append(roman)
    return " ".join(translated_words)

def normalize_multilingual_query(query: str) -> Tuple[str, str]:
    """
    Normalizes any multilingual query (English, Hinglish, Devanagari Hindi).
    Returns (cleaned_english_query, core_topic).
    
    Example:
    'व्हाट इस बनाना' -> ('what is banana', 'banana')
    'kela kya hota hai' -> ('what is banana', 'banana')
    'give me simple code java hello world' -> ('give me simple code java hello world', '')
    """
    q = query.strip()
    is_devanagari = bool(re.search(r'[\u0900-\u097F]', q))
    
    if is_devanagari:
        # Transliterate to Roman
        roman_q = transliterate_devanagari_to_roman(q)
    else:
        roman_q = q

    roman_lower = roman_q.lower().strip()
    
    # Check if this was phrased as an interrogative or definition question
    is_question = bool(
        re.search(r'\b(what is|what are|who is|who was|where is|why is|how does|how to|explain|tell me about|define|meaning of)\b', roman_lower)
        or re.search(r'\b(kya hai|kya hota|kya hoti|kya hote|kise kehte|kisko bolte|ke bare me|ke bare mein|samjhao)\b', roman_lower)
    )

    # Strip common question prefixes
    cleaned = re.sub(
        r'^(what is|what are|who is|who was|where is|why is|how does|how to|explain|tell me about|define|meaning of|kya hai|kya hota hai|kya hoti hai|kya hote hain|batao|samjhao)\s+',
        '',
        roman_lower
    ).strip()

    # Strip common question suffixes
    cleaned = re.sub(
        r'\s+(kya hai|kya hota hai|kya hoti hai|kya hote hain|kise kehte hain|kisko bolte hain|batao|bataiye|samjhao|ke bare me|ke bare mein|batao na|explain karo|bata sakta hai)$',
        '',
        cleaned
    ).strip()

    # Core topic mapping (e.g. kela -> banana, seb -> apple)
    TOPIC_SYNONYMS = {
        "kela": "banana",
        "seb": "apple",
        "aam": "mango",
        "santara": "orange",
        "paani": "water",
        "dharti": "earth",
        "suraj": "sun",
        "chand": "moon",
        "mausam": "weather",
        "samay": "time"
    }
    
    core_topic = TOPIC_SYNONYMS.get(cleaned, cleaned if len(cleaned.split()) <= 3 else "")
    
    # Only prefix 'what is' if query was genuinely an informational question or a single-topic lookup
    if is_question or (len(roman_lower.split()) <= 2 and core_topic and core_topic in TOPIC_SYNONYMS.values()):
        english_query = f"what is {core_topic}" if core_topic else roman_lower
    else:
        english_query = roman_lower

    return english_query, core_topic

language_normalizer = normalize_multilingual_query
