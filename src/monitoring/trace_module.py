from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from contextvars import ContextVar
import time

trace.set_tracer_provider(
    TracerProvider(resource=Resource.create({SERVICE_NAME: "eleina-agent"}))
)
tracer = trace.get_tracer("eleina-agent")

current_span = ContextVar("current_span", default=None)

jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=6831,
)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

def start_span(name: str, **attributes):
    span = tracer.start_span(name)
    for key, value in attributes.items():
        span.set_attribute(key, value)
    current_span.set(span)
    return span

def end_span(span=None, status_code="OK", error_msg=""):
    span = span or current_span.get()
    if span:
        if status_code != "OK":
            span.set_attribute("error", True)
            span.set_attribute("error_message", error_msg)
        span.end()

def trace_decorator(operation_name: str):
    def decorator(func):
        def wrapper(*args, **kwargs):
            with tracer.start_as_current_span(operation_name) as span:
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("status", "success")
                    return result
                except Exception as e:
                    span.set_attribute("status", "error")
                    span.set_attribute("error_message", str(e))
                    raise
        return wrapper
    return decorator

class TraceTimer:
    def __init__(self, module_name: str, request_id: str = None):
        self.module_name = module_name
        self.request_id = request_id
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.span = start_span(self.module_name, request_id=self.request_id)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.time() - self.start_time
        self.span.set_attribute("duration_ms", int(elapsed * 1000))
        if exc_type:
            end_span(self.span, "ERROR", str(exc_val))
        else:
            end_span(self.span)