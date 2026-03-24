import os
import json
from enum import Enum
from typing import List, Dict, Any, Optional
from shcia_contracts.schemas import RemediationPlan, MessageEnvelope, PayloadType, PlanStep, DiagnosisReport
from shcia_core.base_agent import BaseAgent
import uuid

class PlannerAgent(BaseAgent):
    def __init__(self, name: str = "planner-agent"):
        super().__init__(name, port=8080)
        self.execution_endpoint = os.getenv("EXECUTION_URL", "http://execution-agent:8080")

    def handle_message(self, envelope: MessageEnvelope) -> Dict[str, Any]:
        """Handles incoming diagnosis reports."""
        if envelope.payload_type == PayloadType.DIAGNOSIS_REPORT:
            report = DiagnosisReport(**envelope.payload)
            self.logger.info(f"Generating plan for diagnosis: {report.diagnosis_id}")
            return self.generate_plan(report, envelope.correlation_id)
        return {"error": "Invalid payload type"}

    def generate_plan(self, report: DiagnosisReport, correlation_id: str) -> Dict[str, Any]:
        """Strategic planning logic for remediation."""
        # Generate safe, validated remediation plans
        steps = [
            PlanStep(
                order=1,
                action="scale_up",
                target=report.affected_services[0],
                params={"replicas": 8},
                timeout="120s",
                success_criteria="8 pods in Ready state",
                rollback_action="scale_down to original count"
            ),
            PlanStep(
                order=2,
                action="rollback_helm_release",
                target=report.affected_services[0],
                params={"revision": "previous"},
                timeout="300s",
                success_criteria="Error rate < 1% on new pods",
                rollback_action="helm rollback to current (requires human intervention)"
            )
        ]

        plan = RemediationPlan(
            diagnosis_id=report.diagnosis_id,
            confidence=report.confidence,
            strategy="rollback_deployment",
            pre_conditions=["Previous deployment image stable", "EKS cluster healthy"],
            steps=steps,
            post_conditions=["Error rate returns to baseline", "P99 latency < 200ms"],
            rollback_triggers=["Error rate increases by > 5%", "Step exceeds timeout"],
            estimated_recovery_time="8 minutes",
            sla_impact="Payment processing degraded for ~3 minutes during rollback"
        )
        
        self.log_decision("generate_plan", "success", {"plan_id": plan.plan_id, "strategy": plan.strategy})
        self.emit_plan(plan, correlation_id)
        return plan.dict()

    def emit_plan(self, plan: RemediationPlan, correlation_id: str):
        """Sends remediation plan to the Execution Agent."""
        envelope = MessageEnvelope(
            source_agent=self.name,
            target_agent="execution-agent",
            correlation_id=correlation_id,
            payload_type=PayloadType.REMEDIATION_PLAN,
            payload=plan.dict(),
            priority="high"
        )
        try:
            self.logger.info(f"Emitting plan to Execution Agent: {plan.plan_id}")
            # response = requests.post(f"{self.execution_endpoint}/webhook", json=envelope.dict())
            self.log_decision("emit_plan", "success", {"plan_id": plan.plan_id, "mock": True})
        except Exception as e:
            self.logger.error(f"Failed to emit plan: {e}")
            self.log_decision("emit_plan", "failure", {"error": str(e)})

if __name__ == "__main__":
    agent = PlannerAgent()
    agent.run()
