from prometheus_client import Counter, Histogram, Gauge, start_http_server, CollectorRegistry
from prometheus_client.core import GaugeMetricFamily
import psutil
import time

registry = CollectorRegistry()

request_counter = Counter(
    "agent_request_total",
    "Total number of requests",
    ["request_id", "user_id", "status"],
    registry=registry
)

token_counter = Counter(
    "agent_token_consumption",
    "Token consumption",
    ["model", "type"],
    registry=registry
)

request_latency = Histogram(
    "agent_request_latency_seconds",
    "Request latency distribution",
    ["module", "status"],
    registry=registry,
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30, 60]
)

module_latency = Histogram(
    "agent_module_latency_seconds",
    "Module latency distribution",
    ["module", "status"],
    registry=registry
)

model_error_rate = Counter(
    "agent_model_errors_total",
    "Model error count",
    ["model", "error_type"],
    registry=registry
)

tool_call_counter = Counter(
    "agent_tool_calls_total",
    "Tool call count",
    ["tool_name", "status"],
    registry=registry
)

memory_usage = Gauge(
    "agent_memory_usage_bytes",
    "Memory usage in bytes",
    registry=registry
)

cpu_usage = Gauge(
    "agent_cpu_usage_percent",
    "CPU usage percent",
    registry=registry
)

service_health = Gauge(
    "agent_service_health",
    "Service health status (1=healthy, 0=unhealthy)",
    registry=registry
)

class ResourceMetricsCollector:
    def collect(self):
        mem = psutil.virtual_memory()
        yield GaugeMetricFamily("agent_memory_total_bytes", "Total memory", value=mem.total)
        yield GaugeMetricFamily("agent_memory_available_bytes", "Available memory", value=mem.available)
        yield GaugeMetricFamily("agent_cpu_cores", "CPU cores", value=psutil.cpu_count())

registry.register(ResourceMetricsCollector())

def record_request(request_id: str, user_id: str, status: str, latency: float):
    request_counter.labels(request_id, user_id, status).inc()
    request_latency.labels("total", status).observe(latency)

def record_module_latency(module: str, latency: float, status: str = "success"):
    module_latency.labels(module, status).observe(latency)

def record_token_consumption(model: str, input_tokens: int, output_tokens: int):
    token_counter.labels(model, "input").inc(input_tokens)
    token_counter.labels(model, "output").inc(output_tokens)

def record_tool_call(tool_name: str, success: bool):
    status = "success" if success else "error"
    tool_call_counter.labels(tool_name, status).inc()

def record_model_error(model: str, error_type: str):
    model_error_rate.labels(model, error_type).inc()

def update_resource_metrics():
    memory_usage.set(psutil.virtual_memory().used)
    cpu_usage.set(psutil.cpu_percent())

def start_metrics_server(port: int = 8000):
    start_http_server(port, registry=registry)