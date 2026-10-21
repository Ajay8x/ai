import os
import json
import datetime
from typing import Dict, Any, Optional, Tuple
from ai.neural.intent_classifier import intent_classifier
from ai.llm.factory import llm_brain
from tools.registry import registry
from core.context import context_manager
from core.logger import ajax_logger
from database.crud import add_message, add_training_example
from database.db import is_mongo_active, get_mongo_db

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
QA_LOG_JSONL = os.path.join(DATA_DIR, "qa_history.jsonl")
QA_LOG_TXT = os.path.join(DATA_DIR, "saved_qa.txt")

def auto_extract_and_save_facts(query: str):
    """Detects personal details / user facts and saves them to SQLite memories automatically."""
    q_clean = query.strip()
    import re
    # 1. Names: e.g. 'mera naam Ajay hai', 'my name is Ajay'
    name_match = re.search(r'(?:mera naam|my name is)\s+([A-Za-z\u0900-\u097F]+)', q_clean, re.IGNORECASE)
    if name_match:
        from database.crud import save_memory
        save_memory("user_name", name_match.group(1).title(), category="user_profile", source="auto_extract")
        return

    # 2. Remember notes: e.g. 'remember that meeting is at 5pm', 'yaad rakhna ki kal exam hai'
    rem_match = re.search(r'(?:remember that|yaad rakhna ki|yaad rakho ki)\s+(.+)', q_clean, re.IGNORECASE)
    if rem_match:
        from database.crud import save_memory
        fact = rem_match.group(1).strip()
        save_memory("note", fact, category="user_note", source="auto_extract")
        return

    # 3. Location: e.g. 'i live in Mumbai', 'main Delhi me rehta hoon'
    loc_match = re.search(r'(?:i live in\s+([A-Za-z\u0900-\u097F]+)|main\s+([A-Za-z\u0900-\u097F]+)\s+me\s+rehta\s+hoon)', q_clean, re.IGNORECASE)
    if loc_match:
        from database.crud import save_memory
        loc = loc_match.group(1) or loc_match.group(2)
        if loc:
            save_memory("location", loc.strip().title(), category="user_profile", source="auto_extract")
            return

    # 4. Favorites: e.g. 'my favorite color is blue', 'mera favorite food biryani hai'
    fav_match = re.search(r'(?:my favorite\s+([a-zA-Z]+)\s+is\s+([a-zA-Z0-9\s]+)|mera favorite\s+([a-zA-Z]+)\s+([a-zA-Z0-9\s]+)\s+hai|mujhe\s+([a-zA-Z0-9\s]+)\s+pasand\s+hai)', q_clean, re.IGNORECASE)
    if fav_match:
        from database.crud import save_memory
        if fav_match.group(1) and fav_match.group(2):
            save_memory(f"favorite_{fav_match.group(1).lower().strip()}", fav_match.group(2).strip(), category="user_preference", source="auto_extract")
        elif fav_match.group(3) and fav_match.group(4):
            save_memory(f"favorite_{fav_match.group(3).lower().strip()}", fav_match.group(4).strip(), category="user_preference", source="auto_extract")
        elif fav_match.group(5):
            save_memory("favorite_item", fav_match.group(5).strip(), category="user_preference", source="auto_extract")

def record_qa_interaction(query: str, response: str, intent: str, modality: str = "text", tool: Optional[str] = None):
    """Automatically saves and appends every Q&A pair to MongoDB Atlas (cloud) or local files (fallback)."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    record = {
        "timestamp": timestamp,
        "query": query,
        "response": response,
        "intent": intent,
        "tool": tool,
        "modality": modality
    }

    # 1. Primary: Save directly to MongoDB Atlas collection
    if is_mongo_active():
        try:
            db = get_mongo_db()
            db.qa_history.insert_one(record)
        except Exception as e:
            ajax_logger.error(f"Failed writing QA interaction to MongoDB: {e}")
    else:
        # Fallback to local files only if not MongoDB
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(QA_LOG_JSONL, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception as e:
            ajax_logger.warning(f"Local qa_history.jsonl notice: {e}")

    # 2. Auto-extract personal facts into long-term memories (persisted in MongoDB)
    try:
        auto_extract_and_save_facts(query)
    except Exception as e:
        ajax_logger.warning(f"Memory auto-extraction notice: {e}")


def _execute_live_web_search(query: str, norm_query: str = "", core_topic: str = "") -> str:
    """Executes live web search across DuckDuckGo and Wikipedia, assembling formatted markdown."""
    import re
    import urllib.parse
    target = core_topic or norm_query or query
    clean_target = re.sub(r'^(search for|search|google|web search|look up|kya hai|batao)\s+', '', target, flags=re.IGNORECASE).strip() or target

    sections = []
    # 1. Wikipedia Overview
    try:
        from tools.web_tools import WikipediaTool
        wiki_res = WikipediaTool().execute(query=clean_target, sentences=4)
        if wiki_res.success and wiki_res.output:
            sections.append(f"### 📚 Wikipedia Overview\n{wiki_res.output}")
    except Exception:
        pass

    # 2. DuckDuckGo Live Web Search
    try:
        from duckduckgo_search import DDGS
        with DDGS(timeout=5) as ddgs:
            results = list(ddgs.text(clean_target, max_results=3))
            if results:
                web_snippets = []
                for idx, r in enumerate(results, 1):
                    title = r.get("title", f"Result {idx}")
                    body = r.get("body", "")
                    href = r.get("href", "")
                    if href:
                        web_snippets.append(f"{idx}. **[{title}]({href})**\n   {body}")
                    else:
                        web_snippets.append(f"{idx}. **{title}**\n   {body}")
                if web_snippets:
                    sections.append("### 🌐 Live Internet Results (DuckDuckGo)\n" + "\n\n".join(web_snippets))
    except Exception as e:
        ajax_logger.warning(f"Live DuckDuckGo search notice: {e}")

    encoded_q = urllib.parse.quote(clean_target or query)
    if sections:
        return f"**Web Search Results for '{query}'**:\n\n" + "\n\n".join(sections) + f"\n\n🔍 *More results on: [DuckDuckGo](https://duckduckgo.com/?q={encoded_q}) | [Google](https://www.google.com/search?q={encoded_q})*"
    else:
        return f"I searched the web for **'{query}'**, but could not retrieve live snippets at this moment.\n\nDirect Search Link: [DuckDuckGo Search: {query}](https://duckduckgo.com/?q={encoded_q})"

class RequestRouter:
    def process_query(
        self,
        query: str,
        conversation_id: str,
        modality: str = "text",
        confirmed_by_user: bool = False,
        web_search: bool = False,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Main query orchestration pipeline:
        1. Classify intent & confidence.
        2. High Confidence Direct Tool Execution (Instant zero-latency execution).
        3. LLM Brain with Tool Calling.
        4. Response assembly and permanent persistence.
        """
        ajax_logger.info(f"Incoming Request [{modality}]: '{query}' (web_search={web_search})")
        add_message(conversation_id, "user", query, modality=modality)

        # Step 1: Multilingual Normalization & Intent Classification
        from core.language import normalize_multilingual_query
        norm_query, core_topic = normalize_multilingual_query(query)

        # Explicit Web Search Mode Activated by User
        if web_search:
            resp_text = _execute_live_web_search(query, norm_query, core_topic)
            add_message(conversation_id, "assistant", resp_text)
            record_qa_interaction(query, resp_text, "SEARCH_WEB", modality=modality, tool="search_web")
            return {
                "response": resp_text,
                "intent": "SEARCH_WEB",
                "confidence": 1.0,
                "tool_called": "search_web",
                "tool_result": {"success": True, "output": resp_text},
                "needs_confirmation": False
            }

        prediction = intent_classifier.predict(query)
        if prediction["confidence"] < 0.8 and norm_query != query.lower():
            norm_pred = intent_classifier.predict(norm_query)
            if norm_pred["confidence"] > prediction["confidence"]:
                prediction = norm_pred

        intent = prediction["intent"]
        confidence = prediction["confidence"]
        direct_tool = prediction.get("tool")
        entities = prediction.get("entities", {})

        ajax_logger.info(f"Intent Predicted: {intent} (Confidence: {confidence}) | Normalized: '{norm_query}'")

        # Save as candidate for continuous learning
        add_training_example(raw_text=query, intent=intent, entities=entities, confidence=confidence, source=modality)

        # Step 2: High confidence fast path
        if confidence >= 0.85 and direct_tool:
            tool_obj = registry.get_tool(direct_tool)
            if tool_obj:
                ajax_logger.info(f"Executing Direct Tool: '{direct_tool}' with entities: {entities}")
                tool_result = registry.execute_tool(direct_tool, parameters=entities, confirmed_by_user=confirmed_by_user)
                
                if tool_result.metadata.get("confirmation_needed"):
                    resp_text = tool_result.error or "Confirmation required."
                elif tool_result.success:
                    resp_text = str(tool_result.output)
                else:
                    resp_text = f"Action failed: {tool_result.error}"

                add_message(conversation_id, "assistant", resp_text)
                record_qa_interaction(query, resp_text, intent, modality=modality, tool=direct_tool)
                return {
                    "response": resp_text,
                    "intent": intent,
                    "confidence": confidence,
                    "tool_called": direct_tool,
                    "tool_result": tool_result.to_dict(),
                    "needs_confirmation": tool_result.metadata.get("confirmation_needed", False)
                }
        
        if confidence >= 0.90 and prediction.get("predefined_response"):
            resp_text = prediction["predefined_response"]
            add_message(conversation_id, "assistant", resp_text)
            record_qa_interaction(query, resp_text, intent, modality=modality)
            return {
                "response": resp_text,
                "intent": intent,
                "confidence": confidence,
                "tool_called": None,
                "tool_result": None
            }

        # Step 3: LLM Brain Reasoning + Tool Calling
        effective_query = norm_query if (norm_query and norm_query != query.lower().strip()) else query
        messages = context_manager.build_context(conversation_id, effective_query, language=language)
        
        # If user is asking a conversational / factual / wiki question, generate written text directly without tool overhead
        q_lower = query.lower().strip()
        norm_lower = norm_query.lower().strip()
        question_words = ["what is", "what are", "who is", "who was", "where is", "why is", "why do", "how to", "how does", "explain", "define", "tell me about", "kya", "kaun", "kahan", "batao"]
        is_direct_question = (
            any(q_lower.startswith(qw) or f" {qw} " in f" {q_lower} " for qw in question_words)
            or any(norm_lower.startswith(qw) or f" {qw} " in f" {norm_lower} " for qw in question_words)
            or intent in ["SEARCH_WIKIPEDIA", "GENERAL_CHAT"]
        )
        
        if is_direct_question:
            llm_resp = llm_brain.generate(messages, tools=None, max_tokens=250)
        else:
            tool_schemas = registry.get_schemas()
            llm_resp = llm_brain.generate(messages, tools=tool_schemas)


        # If LLM triggered tool calls
        if llm_resp.tool_calls:
            tool_outputs = []
            for tc in llm_resp.tool_calls:
                ajax_logger.info(f"LLM Tool Call: {tc.function_name} with args: {tc.arguments}")
                res = registry.execute_tool(tc.function_name, parameters=tc.arguments, confirmed_by_user=confirmed_by_user)
                tool_outputs.append((tc, res))

            # Assemble clean final answer
            executed_summaries = []
            needs_confirm = False
            for tc, res in tool_outputs:
                if res.metadata.get("confirmation_needed"):
                    needs_confirm = True
                    executed_summaries.append(res.error)
                elif res.success:
                    executed_summaries.append(str(res.output))
                else:
                    executed_summaries.append(f"Error ({tc.function_name}): {res.error}")

            # If tool execution succeeded, check if it was an accidental 'Opened...' message on a factual question
            all_successful = all(res.success for _, res in tool_outputs)
            combined_summary = "\n\n".join(executed_summaries)
            
            # If the user asked a question (what is, who is, define, etc.) and tool just gave a browser open message
            is_question = any(q_word in query.lower() for q_word in ["what", "who", "where", "why", "how", "explain", "define", "tell me", "kya", "kaun", "kahan", "batao"])
            has_browser_open = "opened " in combined_summary.lower() and "browser" in combined_summary.lower()
            
            if all_successful and not (is_question and has_browser_open):
                final_text = combined_summary
                if llm_resp.content and llm_resp.content not in final_text:
                    final_text = f"{llm_resp.content}\n\n{final_text}"
            else:
                # Synthesize / Generate complete written explanation in chat
                synth_messages = [
                    {"role": "system", "content": "You are AJAX AI. Write a complete, informative, well-structured explanation in response to the user question. Explain what it is, its purpose, key features, and examples in clear natural language (Hindi/English). Do NOT mention opening links or browsers."},
                    {"role": "user", "content": query}
                ]
                try:
                    synth_resp = llm_brain.generate(synth_messages, max_tokens=350)
                    final_text = synth_resp.content.strip() if synth_resp.content else combined_summary
                except Exception:
                    final_text = combined_summary
                
            add_message(conversation_id, "assistant", final_text)
            tool_names = [tc.function_name for tc, _ in tool_outputs]
            record_qa_interaction(query, final_text, intent, modality=modality, tool=",".join(tool_names))
            return {
                "response": final_text,
                "intent": intent,
                "confidence": confidence,
                "tool_called": tool_names,
                "tool_result": [r.to_dict() for _, r in tool_outputs],
                "needs_confirmation": needs_confirm
            }

        # Pure Conversational LLM Response
        resp_text = llm_resp.content or "I processed your request."
        add_message(conversation_id, "assistant", resp_text)
        record_qa_interaction(query, resp_text, intent, modality=modality)
        return {
            "response": resp_text,
            "intent": intent,
            "confidence": confidence,
            "tool_called": None,
            "tool_result": None
        }

    def process_query_stream(
        self,
        query: str,
        conversation_id: str,
        modality: str = "text",
        confirmed_by_user: bool = False,
        web_search: bool = False,
        language: str = "en"
    ):
        """
        Streaming query pipeline:
        Yields Server-Sent Events (SSE) data lines with {type, token, metadata}.
        Guarantees full 5-way auto-persistence after response finishes.
        """
        ajax_logger.info(f"Incoming Stream Request [{modality}]: '{query}' (web_search={web_search})")
        add_message(conversation_id, "user", query, modality=modality)

        # Multilingual Normalization & Intent Classification
        from core.language import normalize_multilingual_query
        norm_query, core_topic = normalize_multilingual_query(query)

        # Explicit Web Search Mode Activated by User
        if web_search:
            yield f"data: {json.dumps({'type': 'meta', 'intent': 'SEARCH_WEB', 'confidence': 1.0, 'tool': 'search_web'})}\n\n"
            resp_text = _execute_live_web_search(query, norm_query, core_topic)
            add_message(conversation_id, "assistant", resp_text)
            record_qa_interaction(query, resp_text, "SEARCH_WEB", modality=modality, tool="search_web")

            import re
            parts = re.split(r'(\s+)', resp_text)
            for p in parts:
                if p:
                    yield f"data: {json.dumps({'type': 'token', 'token': p})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'response': resp_text, 'tool': 'search_web', 'intent': 'SEARCH_WEB'})}\n\n"
            return

        prediction = intent_classifier.predict(query)
        if prediction["confidence"] < 0.8 and norm_query != query.lower():
            norm_pred = intent_classifier.predict(norm_query)
            if norm_pred["confidence"] > prediction["confidence"]:
                prediction = norm_pred

        intent = prediction["intent"]
        confidence = prediction["confidence"]
        direct_tool = prediction.get("tool")
        entities = prediction.get("entities", {})

        add_training_example(raw_text=query, intent=intent, entities=entities, confidence=confidence, source=modality)

        # Notify intent metadata
        yield f"data: {json.dumps({'type': 'meta', 'intent': intent, 'confidence': confidence, 'tool': direct_tool})}\n\n"

        # Fast direct tool execution
        if confidence >= 0.85 and direct_tool:
            tool_obj = registry.get_tool(direct_tool)
            if tool_obj:
                tool_res = registry.execute_tool(direct_tool, parameters=entities, confirmed_by_user=confirmed_by_user)
                if tool_res.metadata.get("confirmation_needed"):
                    resp_text = tool_res.error or "Confirmation required."
                elif tool_res.success:
                    resp_text = str(tool_res.output)
                else:
                    resp_text = f"Action failed: {tool_res.error}"

                add_message(conversation_id, "assistant", resp_text)
                record_qa_interaction(query, resp_text, intent, modality=modality, tool=direct_tool)
                yield f"data: {json.dumps({'type': 'token', 'token': resp_text, 'tool': direct_tool})}\n\n"
                yield f"data: {json.dumps({'type': 'done', 'response': resp_text, 'tool': direct_tool, 'intent': intent})}\n\n"
                return

        if confidence >= 0.90 and prediction.get("predefined_response"):
            resp_text = prediction["predefined_response"]
            add_message(conversation_id, "assistant", resp_text)
            record_qa_interaction(query, resp_text, intent, modality=modality)
            yield f"data: {json.dumps({'type': 'token', 'token': resp_text})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'response': resp_text, 'intent': intent})}\n\n"
            return

        # Streaming LLM Response
        effective_query = norm_query if (norm_query and norm_query != query.lower().strip()) else query
        messages = context_manager.build_context(conversation_id, effective_query, language=language)

        full_text = ""
        try:
            for token in llm_brain.stream_generate(messages):
                full_text += token
                yield f"data: {json.dumps({'type': 'token', 'token': token})}\n\n"
        except Exception as e:
            full_text = f"Error generating stream: {e}"
            yield f"data: {json.dumps({'type': 'token', 'token': full_text})}\n\n"

        if not full_text.strip():
            full_text = "I processed your request."
            yield f"data: {json.dumps({'type': 'token', 'token': full_text})}\n\n"

        add_message(conversation_id, "assistant", full_text)
        record_qa_interaction(query, full_text, intent, modality=modality)
        yield f"data: {json.dumps({'type': 'done', 'response': full_text, 'intent': intent})}\n\n"

router = RequestRouter()


