"""
AJAX AI - LLM Factory & Multi-Tier Fallback Manager
Selects and cascades across configured LLM providers with offline fallback support.
"""

import os
from typing import Optional, List, Dict, Any
from ai.llm.base import BaseLLMProvider, LLMResponse, ToolCall
from ai.llm.openai_provider import OpenAICompatibleProvider
from ai.llm.ollama_provider import OllamaProvider
from config.config_loader import config
from core.logger import ajax_logger, error_logger

def generate_offline_code(query: str) -> Optional[str]:
    """Generates structured, clean markdown code snippets for common programming queries."""
    import re
    q = query.lower()
    
    # 1. Java Hello World & Basics
    if "java" in q and ("hello" in q or "starter" in q or "basic" in q or "simple" in q):
        return (
            "Here is the simple **Java Hello World** program:\n\n"
            "```java\n"
            "// HelloWorld.java\n"
            "public class HelloWorld {\n"
            "    public static void main(String[] args) {\n"
            "        System.out.println(\"Hello, World!\");\n"
            "    }\n"
            "}\n"
            "```\n\n"
            "### How to Compile and Run:\n"
            "1. Save this code in a file named `HelloWorld.java`\n"
            "2. Open your terminal or command prompt in that directory\n"
            "3. Compile the Java file:\n"
            "   ```bash\n"
            "   javac HelloWorld.java\n"
            "   ```\n"
            "4. Run the compiled application:\n"
            "   ```bash\n"
            "   java HelloWorld\n"
            "   ```\n\n"
            "### Key Concepts Explained:\n"
            "- `public class HelloWorld`: In Java, all code must reside inside a class. The class name must match the `.java` filename.\n"
            "- `public static void main(String[] args)`: The main entry point where Java execution begins.\n"
            "- `System.out.println(...)`: Standard Java method to print text followed by a new line to the console."
        )

    # 2. Python Hello World
    if "python" in q and ("hello" in q or "starter" in q or "basic" in q or "simple" in q):
        return (
            "Here is the simple **Python Hello World** program:\n\n"
            "```python\n"
            "# main.py\n"
            "print(\"Hello, World!\")\n"
            "```\n\n"
            "### How to Run:\n"
            "```bash\n"
            "python main.py\n"
            "```\n\n"
            "### Explanation:\n"
            "- `print(...)`: Built-in Python function that outputs the given text directly to the console."
        )

    # 3. C++ Hello World
    if ("c++" in q or "cpp" in q) and ("hello" in q or "basic" in q or "simple" in q):
        return (
            "Here is the simple **C++ Hello World** program:\n\n"
            "```cpp\n"
            "#include <iostream>\n\n"
            "int main() {\n"
            "    std::cout << \"Hello, World!\" << std::endl;\n"
            "    return 0;\n"
            "}\n"
            "```\n\n"
            "### How to Compile & Run:\n"
            "```bash\n"
            "g++ HelloWorld.cpp -o HelloWorld\n"
            "./HelloWorld\n"
            "```"
        )

    # 4. C Hello World
    if re.search(r'\bc\b', q) and ("hello" in q or "basic" in q or "simple" in q):
        return (
            "Here is the simple **C Hello World** program:\n\n"
            "```c\n"
            "#include <stdio.h>\n\n"
            "int main() {\n"
            "    printf(\"Hello, World!\\n\");\n"
            "    return 0;\n"
            "}\n"
            "```\n\n"
            "### How to Compile & Run:\n"
            "```bash\n"
            "gcc hello.c -o hello\n"
            "./hello\n"
            "```"
        )

    # 5. JavaScript / Node.js
    if ("javascript" in q or "js" in q or "node" in q) and ("hello" in q or "basic" in q or "simple" in q):
        return (
            "Here is the simple **JavaScript Hello World**:\n\n"
            "```javascript\n"
            "// index.js\n"
            "console.log(\"Hello, World!\");\n"
            "```\n\n"
            "### How to Run:\n"
            "Run in Node.js:\n"
            "```bash\n"
            "node index.js\n"
            "```\n"
            "Or open Developer Tools Console in any web browser (`F12`)."
        )

    # 6. HTML5 Template
    if "html" in q:
        return (
            "Here is a modern, responsive **HTML5 starter template**:\n\n"
            "```html\n"
            "<!DOCTYPE html>\n"
            "<html lang=\"en\">\n"
            "<head>\n"
            "    <meta charset=\"UTF-8\">\n"
            "    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
            "    <title>Hello World</title>\n"
            "    <style>\n"
            "        body {\n"
            "            font-family: Arial, sans-serif;\n"
            "            display: grid;\n"
            "            place-items: center;\n"
            "            height: 100vh;\n"
            "            margin: 0;\n"
            "            background: #0f172a;\n"
            "            color: #f8fafc;\n"
            "        }\n"
            "    </style>\n"
            "</head>\n"
            "<body>\n"
            "    <h1>Hello, World!</h1>\n"
            "</body>\n"
            "</html>\n"
            "```"
        )

    return None

class LocalRuleBasedFallbackProvider(BaseLLMProvider):
    """Offline fallback intelligence when cloud LLMs and local engines are unreachable."""
    def generate(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False
    ) -> LLMResponse:
        user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                user_msg = m.get("content", "").strip()
                break
                
        user_lower = user_msg.lower()

        # 1. Math calculation fallback
        from tools.calculator_tool import CalculatorTool
        calc = CalculatorTool()
        calc_res = calc.execute(expression=user_msg)
        if calc_res.success:
            return LLMResponse(
                content=str(calc_res.output),
                tool_calls=[],
                model="local_math_engine",
                provider="local_rule_engine",
                tokens_used=1
            )

        import re

        # 2. Code Generation & Programming Requests
        is_coding = bool(
            re.search(r'\b(code|program|coding|script|class|method|function|syntax|algorithm|hello\s+world|snippet)\b', user_lower)
            or re.search(r'\b(java|python|c\+\+|cpp|c#|javascript|js|html|css|sql|rust|golang|php|swift|kotlin)\b', user_lower)
        )
        if is_coding:
            code_resp = generate_offline_code(user_msg)
            if code_resp:
                return LLMResponse(
                    content=code_resp,
                    tool_calls=[],
                    model="code_generator_engine",
                    provider="local_code_engine",
                    tokens_used=len(code_resp.split())
                )
            # Try DuckDuckGo search for programming examples
            try:
                from duckduckgo_search import DDGS
                with DDGS(timeout=4) as ddgs:
                    results = list(ddgs.text(user_msg + " code example", max_results=2))
                    if results:
                        snippets = [r.get("body", "").strip() for r in results if r.get("body")]
                        if snippets:
                            resp_content = f"Here is the code reference for **{user_msg}**:\n\n" + "\n\n".join(snippets[:2])
                            return LLMResponse(
                                content=resp_content,
                                tool_calls=[],
                                model="code_search_engine",
                                provider="duckduckgo_code",
                                tokens_used=len(resp_content.split())
                            )
            except Exception:
                pass

        # 3. Conversational greetings (ONLY if query is strictly a greeting, not a multi-word instruction)
        is_pure_greeting = (
            user_lower in ["hello", "hi", "hey", "namaste", "namashkar", "pranam", "hey ajax", "hello ajax", "hi ajax", "good morning", "good evening", "good afternoon"]
            or (len(user_lower.split()) <= 3 and any(user_lower.startswith(w) or user_lower.endswith(w) for w in ["hello", "hi", "hey", "namaste"]) and not is_coding)
        )
        if is_pure_greeting:
            if any(w in user_lower for w in ["good morning", "shubh prabhat"]):
                resp = "Good morning! Hope you have a productive day ahead. How can I assist you today?"
            elif any(w in user_lower for w in ["good afternoon", "good evening", "shubh sandhya"]):
                resp = "Good evening! How can I assist you today?"
            else:
                resp = "Namaste! I am AJAX AI. How can I help you today?"
        elif any(re.search(r'\b' + re.escape(w) + r'\b', user_lower) for w in ["who are you", "kya ho", "your name", "who created you"]):
            resp = "I am AJAX (Adaptive Intelligence & Autonomous eXecution), your autonomous personal AI assistant created by Ajay Singh."
        elif any(re.search(r'\b' + re.escape(w) + r'\b', user_lower) for w in ["how are you", "kaise ho"]):
            resp = "I am running smoothly with optimal performance and sub-second response speed! How can I assist you?"
        elif any(re.search(r'\b' + re.escape(w) + r'\b', user_lower) for w in ["help", "madad", "kya kar sakte ho", "what can you do"]) and len(user_lower.split()) <= 4:
            resp = "I can control your PC (open/close apps, volume, battery, screenshots), solve math, generate code, search Wikipedia and web, set timers/alarms, and remember your preferences."
        else:
            resp = ""
            # Check user uploaded docs in RAG vector store if present
            try:
                from ai.rag.store import rag_store
                if rag_store.documents:
                    rag_results = rag_store.query(user_msg, top_k=2)
                    if rag_results:
                        chunks = [d.get("chunk", "") for d in rag_results]
                        resp = "\n\n".join(chunks)
            except Exception:
                pass

            if not resp:
                from core.language import normalize_multilingual_query
                norm_q, core_topic = normalize_multilingual_query(user_msg)
                target_search = core_topic or norm_q or user_lower

                # 1. Try Wikipedia query on normalized core topic
                try:
                    from tools.web_tools import WikipediaTool
                    wiki_res = WikipediaTool().execute(query=target_search, sentences=4)
                    if wiki_res.success and wiki_res.output:
                        resp = str(wiki_res.output)
                    elif norm_q and norm_q != target_search:
                        wiki_res2 = WikipediaTool().execute(query=norm_q, sentences=4)
                        if wiki_res2.success and wiki_res2.output:
                            resp = str(wiki_res2.output)
                except Exception:
                    pass

            # 2. Try live DuckDuckGo web search
            if not resp:
                try:
                    from duckduckgo_search import DDGS
                    search_term = target_search or norm_q or user_msg
                    with DDGS(timeout=4) as ddgs:
                        results = list(ddgs.text(search_term, max_results=2))
                        if results:
                            snippets = [r.get("body", "").strip() for r in results if r.get("body")]
                            if snippets:
                                resp = "\n\n".join(snippets[:2])
                except Exception:
                    pass

            # 3. Built-in factual knowledge base fallback
            if not resp:
                KNOWLEDGE_BASE = {
                    "banana": "A banana is an elongated, edible fruit produced by several kinds of large herbaceous flowering plants in the genus Musa. It is rich in potassium, dietary fiber, vitamin C, and vitamin B6, and is one of the most widely consumed fruits globally.",
                    "apple": "An apple is a sweet, edible fruit produced by an apple tree (Malus domestica). It contains antioxidants, fiber, and vitamin C, and comes in many cultivars like Red Delicious, Gala, and Fuji.",
                    "mango": "Mango is an edible stone fruit produced by the tropical tree Mangifera indica. Often called the 'king of fruits', it is celebrated for its sweet, tropical flavor and high vitamin A and C content.",
                    "python": "Python is a high-level, interpreted programming language created by Guido van Rossum. It is renowned for its readable syntax, extensive standard libraries, and dominant role in AI, data science, web development, and automation.",
                    "computer": "A computer is an electronic machine that processes data, performs calculations, and executes instructions according to stored programs.",
                    "internet": "The Internet is a global system of interconnected computer networks that communicate via standard Internet Protocols (TCP/IP) to link billions of devices worldwide."
                }
                if core_topic in KNOWLEDGE_BASE:
                    resp = KNOWLEDGE_BASE[core_topic]
                else:
                    resp = f"I processed your query ('{user_msg}'). I am AJAX AI, your cloud-native autonomous assistant powered by MongoDB Atlas, live web search, document intelligence, and neural NLP."

            
        return LLMResponse(
            content=resp,
            tool_calls=[],
            model="chat_assistant_engine",
            provider="conversational_engine",
            tokens_used=len(resp.split())
        )

def get_llm_provider() -> BaseLLMProvider:
    """Instantiate the primary configured LLM provider with auto-detection."""
    provider_name = config.llm.provider.lower()
    
    # Priority 1: Explicit Groq / Free Fast Cloud LLM
    if (provider_name == "groq" or (not config.llm.api_key and config.llm.groq_api_key)) and config.llm.groq_api_key:
        return OpenAICompatibleProvider(
            api_key=config.llm.groq_api_key,
            base_url="https://api.groq.com/openai/v1",
            model=config.llm.model or "llama-3.3-70b-versatile",
            provider_name="groq"
        )
    # Priority 2: OpenAI
    elif (provider_name in ["openai", "chatgpt"] or config.llm.api_key) and config.llm.api_key:
        return OpenAICompatibleProvider(
            api_key=config.llm.api_key,
            base_url="https://api.openai.com/v1",
            model=config.llm.model if config.llm.model and "gpt" in config.llm.model else "gpt-4o-mini",
            provider_name="openai"
        )
    # Priority 3: DeepSeek
    elif (provider_name == "deepseek" or config.llm.deepseek_api_key) and config.llm.deepseek_api_key:
        return OpenAICompatibleProvider(
            api_key=config.llm.deepseek_api_key,
            base_url="https://api.deepseek.com/v1",
            model=config.llm.model or "deepseek-chat",
            provider_name="deepseek"
        )
    # Priority 4: OpenRouter
    elif (provider_name == "openrouter" or config.llm.openrouter_api_key) and config.llm.openrouter_api_key:
        return OpenAICompatibleProvider(
            api_key=config.llm.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
            model=config.llm.model or "meta-llama/llama-3.3-70b-instruct",
            provider_name="openrouter"
        )
    # Priority 5: Ollama
    elif provider_name == "ollama":
        return OllamaProvider(
            base_url=config.llm.ollama_base_url,
            model=config.llm.model or "llama3:latest"
        )
    # Priority 6: Local PyTorch / Transformers
    elif provider_name in ["qwen3.5-9b", "qwen3.5", "qwen9b", "qwen-9b", "qwen", "local_hf", "transformers"]:
        base_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        model_path = config.llm.local_model_path or os.path.join(base_root, "models", "qwen3.5-9b")
        if not os.path.isabs(model_path):
            model_path = os.path.join(base_root, model_path)
        from ai.llm.local_hf_provider import LocalHuggingFaceProvider
        return LocalHuggingFaceProvider(
            model_path=model_path,
            device="auto"
        )
    elif provider_name in ["llamafile", "qwen3-4b", "qwen3", "thinking"]:
        from ai.llm.llamafile_provider import LlamafileProvider
        model_path = config.llm.local_model_path or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "qwen3-4b-thinking-2507.Q4_K_M.gguf")
        return LlamafileProvider(model_path=model_path)
    elif provider_name in ["gguf", "llama_cpp"]:
        from ai.llm.gguf_provider import GGUFProvider
        model_path = config.llm.local_model_path or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "qwen3-4b-thinking-2507.Q4_K_M.gguf")
        return GGUFProvider(model_path=model_path)
    else:
        # Check if local GGUF model exists
        base_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        gguf_path = os.path.join(base_root, "qwen3-4b-thinking-2507.Q4_K_M.gguf")
        if os.path.exists(gguf_path):
            from ai.llm.llamafile_provider import LlamafileProvider
            return LlamafileProvider(model_path=gguf_path)
        
        # Fallback to conversational response engine
        return LocalRuleBasedFallbackProvider()

import time

class ResilientLLMBrain:
    """Wrapper that tries primary provider, then secondary, then local fallback with auto-recovery."""
    def __init__(self):
        self.primary = get_llm_provider()
        self.fallback = LocalRuleBasedFallbackProvider()
        self._primary_disabled = False
        self._last_failure_time = 0.0
        self._retry_cooldown_seconds = 60.0

    def generate(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> LLMResponse:
        now = time.time()
        # Auto-retry primary provider if cooldown period has elapsed
        if self._primary_disabled and (now - self._last_failure_time > self._retry_cooldown_seconds):
            ajax_logger.info("Cooldown elapsed: probing primary LLM provider again...")
            self._primary_disabled = False

        if not self._primary_disabled:
            try:
                return self.primary.generate(messages, tools=tools, temperature=temperature, max_tokens=max_tokens)
            except Exception as e:
                error_logger.warning(f"Primary LLM unavailable ({e}). Switching to local fallback for {int(self._retry_cooldown_seconds)}s.")
                self._primary_disabled = True
                self._last_failure_time = now

        return self.fallback.generate(messages, tools=tools, temperature=temperature, max_tokens=max_tokens)

    def stream_generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048
    ):
        """Yield real-time text chunks, falling back to simulated smooth token delivery on local engine."""
        now = time.time()
        if self._primary_disabled and (now - self._last_failure_time > self._retry_cooldown_seconds):
            ajax_logger.info("Cooldown elapsed: probing primary LLM provider again...")
            self._primary_disabled = False

        if not self._primary_disabled:
            try:
                if hasattr(self.primary, "stream_generate"):
                    for chunk in self.primary.stream_generate(messages, temperature=temperature, max_tokens=max_tokens):
                        yield chunk
                    return
            except Exception as e:
                error_logger.warning(f"Streaming failed ({e}), falling back to local engine.")
                self._primary_disabled = True
                self._last_failure_time = now

        # Fallback local generation
        resp = self.fallback.generate(messages, temperature=temperature, max_tokens=max_tokens)
        text = resp.content or ""
        import re
        parts = re.split(r'(\s+)', text)
        for p in parts:
            if p:
                yield p


llm_brain = ResilientLLMBrain()
