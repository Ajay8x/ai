"""
AJAX AI - Autonomous Agent Planner
Decomposes complex multi-step user tasks, plans tool invocations, and tracks progress with loop safeguards.
"""

from typing import Dict, Any, List, Optional
from ai.llm.factory import llm_brain
from tools.registry import registry
from core.logger import ajax_logger

class AgentPlanner:
    def __init__(self, max_steps: int = 5):
        self.max_steps = max_steps

    def execute_plan(self, task_description: str, conversation_id: str) -> Dict[str, Any]:
        ajax_logger.info(f"Agent Planner initiated for task: '{task_description}'")
        
        steps_executed = []
        current_state = task_description
        
        for step_idx in range(1, self.max_steps + 1):
            prompt = [
                {"role": "system", "content": "You are AJAX Planner. Determine the next single tool action or formulate the final summary."},
                {"role": "user", "content": f"Task: {task_description}\nProgress so far: {steps_executed}\nCurrent goal: What tool to execute next?"}
            ]
            
            tool_schemas = registry.get_schemas()
            resp = llm_brain.generate(prompt, tools=tool_schemas)

            if not resp.tool_calls:
                # Task finished
                final_summary = resp.content or "Task completed."
                return {
                    "success": True,
                    "task": task_description,
                    "steps_count": len(steps_executed),
                    "steps": steps_executed,
                    "summary": final_summary
                }

            # Execute tool call
            tc = resp.tool_calls[0]
            result = registry.execute_tool(tc.function_name, parameters=tc.arguments)
            steps_executed.append({
                "step": step_idx,
                "tool": tc.function_name,
                "args": tc.arguments,
                "success": result.success,
                "output": result.output if result.success else result.error
            })

            if not result.success:
                break

        return {
            "success": True,
            "task": task_description,
            "steps_count": len(steps_executed),
            "steps": steps_executed,
            "summary": "Completed planned actions."
        }

agent_planner = AgentPlanner()
