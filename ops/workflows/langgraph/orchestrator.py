import operator
from typing import Annotated, List, Dict, Any, Union, TypedDict, Optional
from langgraph.graph import StateGraph, END
from shared.contracts.schemas import AnomalySignal, DiagnosisReport, RemediationPlan, ExecutionResult, Severity

# Define the state for the SHCIA Orchestrator
class AgentState(TypedDict):
    correlation_id: str
    incident_severity: Severity
    anomaly_signals: List[AnomalySignal]
    diagnosis: Optional[DiagnosisReport]
    remediation_plan: Optional[RemediationPlan]
    execution_result: Optional[ExecutionResult]
    history: Annotated[List[str], operator.add]
    confidence: float
    is_escalated: bool

def observer_node(state: AgentState) -> AgentState:
    """Collects anomaly signals and initializes the incident state."""
    print(f"--- OBSERVER: Processing anomaly signal for correlation {state['correlation_id']} ---")
    # In a real scenario, this would call the Observer Agent service
    return {"history": ["Anomaly detected and signals correlated"]}

def diagnosis_node(state: AgentState) -> AgentState:
    """Performs root cause analysis based on anomaly signals."""
    print(f"--- DIAGNOSIS: Performing causal reasoning for {state['correlation_id']} ---")
    # Logic to call Diagnosis Agent LLM
    # if state['confidence'] < 0.6: ...
    return {"history": ["Root cause identified: OOM kills on payment-service"]}

def planner_node(state: AgentState) -> AgentState:
    """Generates a safe remediation plan with rollback strategies."""
    print(f"--- PLANNER: Generating remediation plan for {state['correlation_id']} ---")
    # Logic to call Planner Agent
    return {"history": ["Remediation plan generated: rollback deployment with canary"]}

def execution_node(state: AgentState) -> AgentState:
    """Executes the plan via safe infrastructure mutation."""
    print(f"--- EXECUTION: Running remediation plan for {state['correlation_id']} ---")
    # Logic to call Execution Agent (Temporal activity or API)
    return {"history": ["Remediation executed successfully, monitoring results"]}

def safety_gate(state: AgentState) -> str:
    """Decision logic for routing between agents based on confidence."""
    if state["is_escalated"]:
        return "human_intervention"
    if state["confidence"] < 0.8:
        return "require_approval"
    return "auto_execute"

# Build the LangGraph
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("observer", observer_node)
workflow.add_node("diagnosis", diagnosis_node)
workflow.add_node("planner", planner_node)
workflow.add_node("execution", execution_node)

# Add Edges
workflow.set_entry_point("observer")
workflow.add_edge("observer", "diagnosis")
workflow.add_edge("diagnosis", "planner")

# Conditional reasoning for execution
workflow.add_conditional_edges(
    "planner",
    safety_gate,
    {
        "auto_execute": "execution",
        "require_approval": END, # Pause for human
        "human_intervention": END # Full stop
    }
)

workflow.add_edge("execution", END)

# Compile the graph
shcia_orchestrator = workflow.compile()

if __name__ == "__main__":
    # Example invocation
    initial_state = {
        "correlation_id": "incident_abc123",
        "incident_severity": Severity.CRITICAL,
        "anomaly_signals": [],
        "diagnosis": None,
        "remediation_plan": None,
        "execution_result": None,
        "history": [],
        "confidence": 0.95,
        "is_escalated": False
    }
    
    # Run the orchestrator
    for output in shcia_orchestrator.stream(initial_state):
        print(output)
