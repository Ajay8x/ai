"""
AJAX AI - Entity and Relationship Extractor
Extracts named entities and semantic relationships (Knowledge Triples)
using LLM structured extraction with a resilient rule-based/regex fallback engine.
"""

import re
import json
from typing import List, Dict, Any, Tuple
from core.logger import ajax_logger


COMMON_RELATION_PATTERNS = [
    r'(?P<src>[A-Z][A-Za-z0-9_\s]{1,30}?)\s+(?:is|was|are|were)\s+(?:a|an|the)?\s*(?P<rel>developed by|created by|founded by|invented by|acquired by|part of|subset of)\s+(?P<tgt>[A-Z][A-Za-z0-9_\s]{1,30})',
    r'(?P<src>[A-Z][A-Za-z0-9_\s]{1,30}?)\s+(?P<rel>developed|created|founded|invented|collaborates with|partnered with|acquired|owns|uses|operates|produces|released|published|discovered)\s+(?:a|an|the)?\s*(?P<tgt>[A-Z][A-Za-z0-9_\s]{1,30})',
    r'(?P<src>[A-Z][A-Za-z0-9_\s]{1,30}?)\s+(?:is|was)\s+(?P<rel>located in|based in|headquartered in)\s+(?P<tgt>[A-Z][A-Za-z0-9_\s]{1,30})',
    r'(?P<src>[A-Z][A-Za-z0-9_\s]{1,30}?)\s+(?P<rel>works on|researches|focuses on)\s+(?P<tgt>[A-Z][A-Za-z0-9_\s]{1,30})',
]

STOP_ENTITIES = {
    "the", "a", "an", "this", "that", "these", "those", "it", "they", "we", "you", "i",
    "there", "here", "what", "which", "who", "whom", "whose", "how", "why", "when", "where"
}


class EntityExtractor:
    """
    Extracts Entities and Relationships for the Knowledge Graph.
    """

    @staticmethod
    def _clean_entity(name: str) -> str:
        clean = re.sub(r'^[^\w]+|[^\w]+$', '', name.strip())
        # Strip trailing prepositions/clauses like 'in London', 'to solve...', 'at DeepMind'
        parts = re.split(r'\s+(?:in|at|to|for|with|by|on|from|that|which)\s+', clean, flags=re.IGNORECASE)
        if parts and parts[0].strip():
            clean = parts[0].strip()
        return clean.strip()

    @classmethod
    def extract_heuristic(cls, text: str) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
        """
        Fast rule-based extraction for zero-cost, instant analysis and offline fallback.
        """
        if not text:
            return [], []

        entities_found = {}
        relations_found = []

        # 1. Extract relationships via syntactic regex patterns
        for pattern in COMMON_RELATION_PATTERNS:
            for match in re.finditer(pattern, text):
                src = cls._clean_entity(match.group("src"))
                tgt = cls._clean_entity(match.group("tgt"))
                rel_val = match.group("rel") if "rel" in match.groupdict() else "RELATES_TO"
                rel = (rel_val or "RELATES_TO").strip().upper().replace(" ", "_")

                if src and tgt and src.lower() not in STOP_ENTITIES and tgt.lower() not in STOP_ENTITIES:
                    if src.lower() != tgt.lower():
                        entities_found[src] = {"name": src, "type": "CONCEPT"}
                        entities_found[tgt] = {"name": tgt, "type": "CONCEPT"}
                        relations_found.append({
                            "source": src,
                            "relation": rel,
                            "target": tgt
                        })

        # 2. Extract capitalized noun/proper noun phrases
        capitalized_phrases = re.findall(r'\b[A-Z][a-zA-Z0-9]*(?:\s+[A-Z][a-zA-Z0-9]*)*\b', text)
        for phrase in capitalized_phrases:
            phrase = cls._clean_entity(phrase)
            if len(phrase) > 2 and phrase.lower() not in STOP_ENTITIES and len(phrase.split()) <= 4:
                if phrase not in entities_found:
                    entities_found[phrase] = {"name": phrase, "type": "ENTITY"}

        return list(entities_found.values()), relations_found

    @classmethod
    def extract_with_llm(cls, text: str, llm_engine=None) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
        """
        High-fidelity information extraction using LLM structured generation.
        """
        if not text:
            return [], []

        if llm_engine is None:
            try:
                from ai.llm.factory import llm_brain
                llm_engine = llm_brain
            except Exception:
                return cls.extract_heuristic(text)

        prompt = f"""Extract key knowledge graph entities and relationships from the text below.
Return strictly valid JSON with no markdown formatting or commentary:
{{
  "entities": [
    {{"name": "EntityName", "type": "PERSON|ORGANIZATION|TECHNOLOGY|CONCEPT|LOCATION|PRODUCT"}}
  ],
  "relations": [
    {{"source": "SourceEntity", "relation": "RELATION_TYPE", "target": "TargetEntity"}}
  ]
}}

Text:
\"\"\"{text[:1500]}\"\"\""""

        try:
            messages = [{"role": "user", "content": prompt}]
            response = llm_engine.generate(messages, temperature=0.1, max_tokens=1000)
            content = (response.content or "").strip()

            # Clean JSON code blocks if present
            content = re.sub(r'^```json\s*', '', content)
            content = re.sub(r'^```\s*', '', content)
            content = re.sub(r'\s*```$', '', content)
            
            data = json.loads(content)
            raw_entities = data.get("entities", [])
            raw_relations = data.get("relations", [])

            # Format and sanitize
            entities = []
            for e in raw_entities:
                name = cls._clean_entity(e.get("name", ""))
                if name and name.lower() not in STOP_ENTITIES:
                    entities.append({"name": name, "type": e.get("type", "CONCEPT")})

            relations = []
            for r in raw_relations:
                src = cls._clean_entity(r.get("source", ""))
                tgt = cls._clean_entity(r.get("target", ""))
                rel = r.get("relation", "RELATES_TO").strip().upper().replace(" ", "_")
                if src and tgt and src.lower() != tgt.lower():
                    relations.append({"source": src, "relation": rel, "target": tgt})

            if entities or relations:
                return entities, relations
        except Exception as e:
            ajax_logger.debug(f"LLM Entity Extraction failed ({e}), using heuristic extractor.")

        # Fallback to heuristic
        return cls.extract_heuristic(text)

    @classmethod
    def extract_from_query(cls, query: str) -> List[str]:
        """
        Identifies entity candidates directly inside the user's search query.
        """
        # Look for capitalized tokens or key phrases
        cleaned = re.sub(r'[^\w\s]', ' ', query)
        tokens = cleaned.split()
        candidates = []

        # Multi-word capitalization or capitalized words
        for match in re.finditer(r'\b[A-Z][a-zA-Z0-9]*(?:\s+[A-Z][a-zA-Z0-9]*)*\b', query):
            ent = cls._clean_entity(match.group(0))
            if ent and ent.lower() not in STOP_ENTITIES:
                candidates.append(ent)

        # Also add significant non-stopword tokens as single-term entity seeds
        stopwords = {
            "what", "is", "the", "relation", "between", "who", "where", "how", "and",
            "kya", "hai", "ka", "ke", "ki", "aur", "mein", "se", "batao", "sambandh"
        }
        for t in tokens:
            t_clean = t.strip()
            if len(t_clean) > 3 and t_clean.lower() not in stopwords:
                if t_clean not in candidates and t_clean.title() not in candidates:
                    candidates.append(t_clean)

        return list(dict.fromkeys(candidates))


entity_extractor = EntityExtractor()
