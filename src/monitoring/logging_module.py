import logging
import json
from datetime import datetime
import hashlib

LOG_LEVEL = logging.INFO

class StructuredFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "request_id": getattr(record, "request_id", "N/A"),
            "session_id": getattr(record, "session_id", "N/A"),
            "user_id": getattr(record, "user_id", "N/A"),
            "module": getattr(record, "module", "N/A"),
            "message": record.getMessage(),
            "details": getattr(record, "details", {}),
            "trace_id": getattr(record, "trace_id", "N/A"),
            "span_id": getattr(record, "span_id", "N/A"),
        }
        return json.dumps(log_entry, ensure_ascii=False)

logger = logging.getLogger("eleina-agent")
logger.setLevel(LOG_LEVEL)

for handler in logger.handlers[:]:
    logger.removeHandler(handler)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(StructuredFormatter())
logger.addHandler(stream_handler)

def init_logging(log_file: str = None):
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(StructuredFormatter())
        logger.addHandler(file_handler)

def log_user_input(request_id: str, session_id: str, user_id: str, input_text: str):
    logger.info("User input received", extra={
        "request_id": request_id,
        "session_id": session_id,
        "user_id": user_id,
        "module": "input",
        "details": {
            "input_length": len(input_text),
            "input_hash": hashlib.md5(input_text.encode()).hexdigest()
        }
    })

def log_security_check(request_id: str, result: str, reason: str = ""):
    logger.info(f"Security check: {result}", extra={
        "request_id": request_id,
        "module": "security",
        "details": {"result": result, "reason": reason}
    })

def log_intent_recognition(request_id: str, intent: str, confidence: float, slots: dict):
    logger.info(f"Intent recognized: {intent}", extra={
        "request_id": request_id,
        "module": "intent",
        "details": {"intent": intent, "confidence": confidence, "slots": slots}
    })

def log_rag_retrieval(request_id: str, doc_count: int, latency: float, sources: list):
    logger.info(f"RAG retrieval completed: {doc_count} docs", extra={
        "request_id": request_id,
        "module": "rag",
        "details": {"doc_count": doc_count, "latency_ms": latency, "sources": sources}
    })

def log_tool_call(request_id: str, tool_name: str, params: dict, result: dict, success: bool):
    logger.info(f"Tool call: {tool_name} {'succeeded' if success else 'failed'}", extra={
        "request_id": request_id,
        "module": "tool",
        "details": {
            "tool_name": tool_name,
            "params": params,
            "success": success,
            "result_summary": str(result)[:200]
        }
    })

def log_model_inference(request_id: str, model: str, input_tokens: int, output_tokens: int, latency: float):
    logger.info("Model inference completed", extra={
        "request_id": request_id,
        "module": "model",
        "details": {
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "latency_ms": latency
        }
    })

def log_output(request_id: str, content: str, tokens: int):
    logger.info("Response generated", extra={
        "request_id": request_id,
        "module": "output",
        "details": {"content_length": len(content), "tokens": tokens}
    })

def log_error(request_id: str, module: str, error: Exception, context: dict = None):
    logger.error(f"Error in {module}: {str(error)}", extra={
        "request_id": request_id,
        "module": module,
        "details": {"error_type": type(error).__name__, "context": context or {}}
    })