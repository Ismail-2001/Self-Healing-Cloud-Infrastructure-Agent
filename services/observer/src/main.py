import os
import time
import json
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
from shcia_contracts.schemas import AnomalySignal, Severity, MessageEnvelope, PayloadType
from shcia_core.base_agent import BaseAgent
import uuid

# Configuration for polling
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus-server:9090")
POLLING_INTERVAL = int(os.getenv("POLLING_INTERVAL", 60))

class ObserverAgent(BaseAgent):
    def __init__(self, name: str = "observer-agent"):
        super().__init__(name, port=8080)
        self.diagnose_endpoint = os.getenv("DIAGNOSIS_URL", "http://diagnosis-agent:8080")

    def handle_message(self, envelope: MessageEnvelope) -> Dict[str, Any]:
        """Handles external signals or events if any (e.g., config changes)."""
        return {"status": "received", "message": "Observer Agent does not typically handle inbound signals."}

    def collect_metrics(self) -> List[Dict[str, Any]]:
        """Polled by the main loop to fetch metrics from Prometheus/CloudWatch."""
        self.logger.info(f"Polling metrics from {PROMETHEUS_URL}...")
        # Placeholder for real Prometheus API call
        # Mocking an anomaly for demonstration
        mock_anomaly = {
            "metric": "http_request_duration_seconds",
            "service": "payment-service",
            "observed_value": 2.3,
            "baseline_value": 0.15,
            "deviation_sigma": 4.2
        }
        return [mock_anomaly]

    def detect_anomalies(self, metrics: List[Dict[str, Any]]) -> List[AnomalySignal]:
        """Correlates and filters anomalies based on adaptive thresholds."""
        signals = []
        for metric in metrics:
            if metric["observed_value"] > (metric["baseline_value"] * 3): # Simple 3x baseline threshold for Demo
                signal = AnomalySignal(
                    severity=Severity.CRITICAL,
                    service=metric["service"],
                    namespace="production",
                    cluster="eks-prod-us-east-1",
                    metric=metric["metric"],
                    observed_value=metric["observed_value"],
                    baseline_value=metric["baseline_value"],
                    deviation_sigma=metric["deviation_sigma"],
                    context={"active_incidents": []}
                )
                signals.append(signal)
        return signals

    def emit_signal(self, signal: AnomalySignal):
        """Sends anomaly signal to the Diagnosis Agent."""
        envelope = MessageEnvelope(
            source_agent=self.name,
            target_agent="diagnosis-agent",
            correlation_id=f"incident_{uuid.uuid4()}",
            payload_type=PayloadType.ANOMALY_SIGNAL,
            payload=signal.dict(),
            priority=signal.severity
        )
        try:
            self.logger.info(f"Emitting signal to Diagnosis Agent: {signal.signal_id}")
            # response = requests.post(f"{self.diagnose_endpoint}/webhook", json=envelope.dict())
            # self.log_decision("emit_signal", "success" if response.status_code == 200 else "failure", {"signal_id": signal.signal_id})
            self.log_decision("emit_signal", "success", {"signal_id": signal.signal_id, "mock": True})
        except Exception as e:
            self.logger.error(f"Failed to emit signal: {e}")
            self.log_decision("emit_signal", "failure", {"error": str(e)})

    def run_polling_loop(self):
        """Main operational loop of the Observer Agent."""
        self.logger.info("Starting polling loop...")
        while True:
            try:
                metrics = self.collect_metrics()
                signals = self.detect_anomalies(metrics)
                for signal in signals:
                    self.emit_signal(signal)
            except Exception as e:
                self.logger.error(f"Error in polling loop: {e}")
            time.sleep(POLLING_INTERVAL)

if __name__ == "__main__":
    agent = ObserverAgent()
    # Start polling loop in a separate thread
    threading.Thread(target=agent.run_polling_loop, daemon=True).start()
    agent.run()
