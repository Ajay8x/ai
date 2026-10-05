"""
AJAX AI - Intent & Action Router
Evaluates incoming queries, determines execution route (Direct Tool vs LLM Brain vs Predefined),
executes tools safely, and returns finalized responses.
"""

from typing import Dict, Any, Optional, Tuple
from ai.neural.intent_classifier import intent_classifier
from ai.llm.factory import llm_brain
from tools.registry import registry
from core.context import context_manager
from core.logger import ajax_logger
from database.crud import add_message, add_training_example

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
        4. Response assembly and persistence.
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
            return {
                "response": resp_text,
                "intent": intent,
                "confidence": confidence,
                "tool_called": None,
                "tool_result": None
            }

        # Step 3: LLM Brain Reasoning + Tool Calling
        messages = context_manager.build_context(conversation_id, query)
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

            final_text = "\n".join(executed_summaries)
            if llm_resp.content:
                final_text = f"{llm_resp.content}\n\n{final_text}"
                
            add_message(conversation_id, "assistant", final_text)
            return {
                "response": final_text,
                "intent": intent,
                "confidence": confidence,
                "tool_called": [tc.function_name for tc, _ in tool_outputs],
                "tool_result": [r.to_dict() for _, r in tool_outputs],
                "needs_confirmation": needs_confirm
            }

        # Pure Conversational LLM Response
        resp_text = llm_resp.content or "I processed your request."
        add_message(conversation_id, "assistant", resp_text)
        return {
            "response": resp_text,
            "intent": intent,
            "confidence": confidence,
            "tool_called": None,
            "tool_result": None
        }

router = RequestRouter()
