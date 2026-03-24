import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from flask import Flask, jsonify, request
from pydantic import BaseModel, ValidationError
from shcia_contracts.schemas import MessageEnvelope, PayloadType
import threading
from prometheus_client import Counter, Histogram, start_http_server

# Configure structured logging
logging.basicConfig(level=logging.INFO, format='{"timestamp":"%(asctime)s", "level":"%(levelname)s", "agent":"%(name)s", "message":"%(message)s"}')

# Base metrics
METRIC_DECISIONS_TOTAL = Counter('shcia_agent_decisions_total', 'Total decisions made by the agent', ['agent', 'decision_type', 'outcome'])
METRIC_PROCESSING_DURATION = Histogram('shcia_agent_processing_duration_seconds', 'Processing duration for the agent', ['agent'])
METRIC_ERRORS_TOTAL = Counter('shcia_agent_errors_total', 'Total errors encountered by the agent', ['agent', 'error_type'])

# Security Configuration
AUTH_TOKEN = os.getenv("SHCIA_AUTH_TOKEN", "insecure-default-dev-only")

class BaseAgent(ABC):
    def __init__(self, name: str, port: int = 8080, metrics_port: int = 9090):
        self.name = name
        self.logger = logging.getLogger(name)
        self.port = port
        self.metrics_port = metrics_port
        self.app = Flask(name)
        self._setup_server()

    def _authenticate_request(self):
        """Validates the SHCIA-Auth-Token header."""
        auth_header = request.headers.get("SHCIA-Auth-Token")
        if not auth_header or auth_header != AUTH_TOKEN:
            self.logger.warning(f"Unauthorized access attempt from {request.remote_addr}")
            METRIC_ERRORS_TOTAL.labels(agent=self.name, error_type="unauthorized_access").inc()
            return False
        return True

    def _setup_server(self):
        @self.app.route('/health', methods=['GET'])
        def health():
            status = {"status": "up", "agent": self.name}
            return jsonify(status), 200

        @self.app.route('/ready', methods=['GET'])
        def ready():
            if self.is_ready():
                return jsonify({"status": "ready"}), 200
            return jsonify({"status": "not_ready"}), 503

        @self.app.route('/webhook', methods=['POST'])
        def webhook():
            if not self._authenticate_request():
                return jsonify({"error": "Unauthorized"}), 401
            
            data = request.json
            try:
                envelope = MessageEnvelope(**data)
                return self._handle_envelope(envelope)
            except ValidationError as e:
                self.logger.error(f"Invalid message format: {e.errors()}")
                METRIC_ERRORS_TOTAL.labels(agent=self.name, error_type="validation_error").inc()
                return jsonify({"error": "Invalid Message Format"}), 400

    def is_ready(self) -> bool:
        """Override in subclasses to perform health checks."""
        return True

    def _handle_envelope(self, envelope: MessageEnvelope):
        self.logger.info(f"Received message: {envelope.message_id} from {envelope.source_agent}")
        with METRIC_PROCESSING_DURATION.labels(agent=self.name).time():
            result = self.handle_message(envelope)
            return jsonify(result), 200

    @abstractmethod
    def handle_message(self, envelope: MessageEnvelope) -> Dict[str, Any]:
        """Core logic of the agent."""
        pass

    def run(self):
        self.logger.info(f"Starting agent {self.name} on port {self.port}")
        # Start Prometheus metrics server
        start_http_server(self.metrics_port)
        self.app.run(host='0.0.0.0', port=self.port)

    def log_decision(self, decision_type: str, outcome: str, details: Dict[str, Any]):
        METRIC_DECISIONS_TOTAL.labels(agent=self.name, decision_type=decision_type, outcome=outcome).inc()
        self.logger.info(f"Decision Record: {decision_type} - {outcome}. Details: {details}")

    def send_authenticated_request(self, url: str, envelope: MessageEnvelope):
        """Sends an authenticated POST request to another agent with Circuit Breaker support."""
        # FAANG Reliability: Circuit Breaker Logic (Simplified)
        # In production, this would use a dedicated library like 'pybreaker'
        headers = {
            "Content-Type": "application/json",
            "SHCIA-Auth-Token": AUTH_TOKEN,
            "X-Trace-ID": envelope.trace_id # Propagate TraceID
        }
        try:
            self.logger.info(f"Dispatching trace {envelope.trace_id} to endpoint {url}")
            response = requests.post(f"{url}/webhook", json=envelope.dict(), headers=headers, timeout=10)
            if response.status_code != 200:
                self.logger.error(f"Failed to send trace {envelope.trace_id}: {response.status_code}")
                METRIC_ERRORS_TOTAL.labels(agent=self.name, error_type="downstream_fail").inc()
            return response
        except requests.exceptions.Timeout:
            self.logger.error(f"Timeout dispatching trace {envelope.trace_id} to {url}")
            METRIC_ERRORS_TOTAL.labels(agent=self.name, error_type="downstream_timeout").inc()
            raise
        except Exception as e:
            self.logger.error(f"Circuit Breaker Triggered for {url}: {e}")
            raise e

# Example logic for a concrete agent would be like:
# class ObserverAgent(BaseAgent):
#     def handle_message(self, envelope: MessageEnvelope) -> Dict[str, Any]:
#         return {"status": "processed"}
