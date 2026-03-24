from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class PayloadType(str, Enum):
    ANOMALY_SIGNAL = "anomaly_signal"
    DIAGNOSIS_REPORT = "diagnosis_report"
    REMEDIATION_PLAN = "remediation_plan"
    EXECUTION_RESULT = "execution_result"

class MessageEnvelope(BaseModel):
    message_id: str = Field(default_factory=lambda: f"msg_{uuid.uuid4()}")
    trace_id: str = Field(default_factory=lambda: f"trace_{uuid.uuid4()}") # OpenTelemetry Correlation
    source_agent: str
    target_agent: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: str
    payload_type: PayloadType
    payload: Dict[str, Any]
    priority: Severity = Severity.LOW
    ttl: str = "300s"

class AnomalySignal(BaseModel):
    signal_id: str = Field(default_factory=lambda: f"sig_{uuid.uuid4()}")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    severity: Severity
    service: str
    namespace: str
    cluster: str
    metric: str
    observed_value: float
    baseline_value: float
    deviation_sigma: float
    correlated_signals: List[str] = []
    context: Dict[str, Any] = {
        "recent_deployments": [],
        "active_incidents": [],
        "affected_endpoints": []
    }

class Evidence(BaseModel):
    signal: str
    weight: float
    reasoning: str

class DiagnosisReport(BaseModel):
    diagnosis_id: str = Field(default_factory=lambda: f"diag_{uuid.uuid4()}")
    root_cause_hypothesis: str
    confidence: float
    evidence: List[Evidence]
    affected_services: List[str]
    blast_radius: str
    recommended_actions: List[str]
    escalation_required: bool = False

class PlanStep(BaseModel):
    order: int
    action: str
    target: str
    params: Dict[str, Any]
    timeout: str
    success_criteria: str
    rollback_action: str

class RemediationPlan(BaseModel):
    plan_id: str = Field(default_factory=lambda: f"plan_{uuid.uuid4()}")
    diagnosis_id: str
    confidence: float
    strategy: str
    pre_conditions: List[str]
    steps: List[PlanStep]
    post_conditions: List[str]
    rollback_triggers: List[str]
    estimated_recovery_time: str
    sla_impact: str
    requires_approval: bool = False
    budget_impact: str = "$0"

class ExecutionStepResult(BaseModel):
    step: int
    action: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    before_state: Dict[str, Any]
    after_state: Dict[str, Any]
    duration_ms: int
    result: str # "success" | "failure"
    verification: str

class ExecutionResult(BaseModel):
    execution_id: str = Field(default_factory=lambda: f"exec_{uuid.uuid4()}")
    plan_id: str
    outcome: str # "fully_remediated" | "partially_remediated" | "failed" | "rolled_back"
    steps: List[ExecutionStepResult]
    final_verification: str
    incident_duration_seconds: int
