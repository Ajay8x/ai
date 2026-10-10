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

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
QA_LOG_JSONL = os.path.join(DATA_DIR, "qa_history.jsonl")
QA_LOG_TXT = os.path.join(DATA_DIR, "saved_qa.txt")

def record_qa_interaction(query: str, response: str, intent: str, modality: str = "text", tool: Optional[str] = None):
    """Automatically saves and appends every Q&A pair to file logs and SQLite."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # 1. Append to JSONL for dataset / export
    record = {
        "timestamp": timestamp,
        "query": query,
        "response": response,
        "intent": intent,
        "tool": tool,
        "modality": modality
    }
    try:
        with open(QA_LOG_JSONL, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        ajax_logger.error(f"Failed writing to qa_history.jsonl: {e}")

    # 2. Append to clean human-readable saved_qa.txt
    try:
        with open(QA_LOG_TXT, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] [{intent}]\nQ: {query}\nA: {response}\n" + "-"*50 + "\n")
    except Exception as e:
        ajax_logger.error(f"Failed writing to saved_qa.txt: {e}")

class RequestRouter:
    def process_query(
        self,
        query: str,
        conversation_id: str,
        modality: str = "text",
        confirmed_by_user: bool = False
    ) -> Dict[str, Any]:
        """
        Main query orchestration pipeline:
        1. Classify intent & confidence.
        2. High Confidence Direct Tool Execution (Instant zero-latency execution).
        3. LLM Brain with Tool Calling.
        4. Response assembly and permanent persistence.
        """
        ajax_logger.info(f"Incoming Request [{modality}]: '{query}'")
        add_message(conversation_id, "user", query, modality=modality)

        # Step 1: Neural Intent Classification
        prediction = intent_classifier.predict(query)
        intent = prediction["intent"]
        confidence = prediction["confidence"]
        direct_tool = prediction.get("tool")
        entities = prediction.get("entities", {})

        ajax_logger.info(f"Intent Predicted: {intent} (Confidence: {confidence})")

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
        messages = context_manager.build_context(conversation_id, query)
        
        # If user is asking a conversational / factual / wiki question, generate written text directly without tool overhead
        q_lower = query.lower().strip()
        is_direct_question = (
            any(q_lower.startswith(qw) or f" {qw} " in f" {q_lower} " for qw in ["what is", "what are", "who is", "who was", "where is", "why is", "why do", "how to", "how does", "explain", "define", "tell me about", "kya", "kaun", "kahan", "batao"])
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

router = RequestRouter()

