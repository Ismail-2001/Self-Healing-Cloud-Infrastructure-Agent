import os
import json
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from shcia_contracts.schemas import DiagnosisReport, MessageEnvelope, PayloadType, Evidence, AnomalySignal
from shcia_core.base_agent import BaseAgent, METRIC_ERRORS_TOTAL
import uuid

class DiagnosisAgent(BaseAgent):
    def __init__(self, name: str = "diagnosis-agent"):
        super().__init__(name, port=8080)
        self.planner_endpoint = os.getenv("PLANNER_URL", "http://planner-agent:8080")
        self.model = ChatOpenAI(model="gpt-4", temperature=0)
        self.parser = PydanticOutputParser(pydantic_object=DiagnosisReport)

    def is_ready(self) -> bool:
        return True # Add logic to check for service dependency graph connectivity

    def handle_message(self, envelope: MessageEnvelope) -> Dict[str, Any]:
        """Handles incoming anomaly signals."""
        if envelope.payload_type == PayloadType.ANOMALY_SIGNAL:
            signal = AnomalySignal(**envelope.payload)
            self.logger.info(f"Diagnosing anomaly signal: {signal.signal_id} on {signal.service}")
            return self.diagnose_with_ai(signal, envelope.correlation_id)
        return {"error": "Invalid payload type"}

    def fetch_service_topology(self, service: str) -> Dict[str, Any]:
        """Fetches dependency graph from Istio/K8s/OpenTelemetry."""
        # This would be a real API call to Istio or Jaeger
        return {
            "service": service,
            "upstream": ["api-gateway"],
            "downstream": ["payment-db", "notification-service"],
            "recent_changes": [
                {"timestamp": "2025-01-15T10:15:00Z", "type": "deployment", "service": service, "commit": "abc123"}
            ]
        }

    def diagnose_with_ai(self, signal: AnomalySignal, correlation_id: str) -> Dict[str, Any]:
        """Core causal reasoning logic using LLM."""
        topology = self.fetch_service_topology(signal.service)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert SRE. Perform root cause analysis (RCA) on the following anomaly signal."),
            ("human", (
                "Anomaly Signal: {signal_json}\n\n"
                "Service Topology & Recent Changes: {topology_json}\n\n"
                "Review the timeline. If an anomaly started shortly after a deployment, prioritize that hypothesis. "
                "Consider resource exhaustion, dependency failures, and traffic spikes.\n\n"
                "{format_instructions}"
            ))
        ])
        
        chain = prompt | self.model | self.parser
        
        try:
            report: DiagnosisReport = chain.invoke({
                "signal_json": json.dumps(signal.dict()),
                "topology_json": json.dumps(topology),
                "format_instructions": self.parser.get_format_instructions()
            })
            
            self.log_decision("diagnose_ai", "success", {"diagnosis_id": report.diagnosis_id, "confidence": report.confidence})
            self.emit_report(report, correlation_id)
            return report.dict()
        except Exception as e:
            self.logger.error(f"AI diagnosis failed: {e}")
            METRIC_ERRORS_TOTAL.labels(agent=self.name, error_type="ai_diagnosis_error").inc()
            return {"error": "AI diagnosis failed", "details": str(e)}

    def emit_report(self, report: DiagnosisReport, correlation_id: str):
        """Sends diagnosis report to the Planner Agent."""
        envelope = MessageEnvelope(
            source_agent=self.name,
            target_agent="planner-agent",
            correlation_id=correlation_id,
            payload_type=PayloadType.DIAGNOSIS_REPORT,
            payload=report.dict(),
            priority="high"
        )
        try:
            self.logger.info(f"Emitting report to Planner Agent: {report.diagnosis_id}")
            # response = requests.post(f"{self.planner_endpoint}/webhook", json=envelope.dict())
            self.log_decision("emit_report", "success", {"diagnosis_id": report.diagnosis_id, "mock": True})
        except Exception as e:
            self.logger.error(f"Failed to emit report: {e}")
            self.log_decision("emit_report", "failure", {"error": str(e)})

if __name__ == "__main__":
    agent = DiagnosisAgent()
    agent.run()
