# Runbook: Automated Deployment Rollback

## Trigger Condition
- **Threshold**: `http_request_duration_seconds` (P99) > 1.0s or `error_rate` > 5% for 3 consecutive minutes.
- **Correlation**: Anomaly detected within 15 minutes of a successful `helm upgrade` or `kubectl apply`.

## Automated Action
1. **Diagnosis**: `DiagnosisAgent` identifies the OOM/Latency spike following a recent deployment.
2. **Planning**: `PlannerAgent` generates a `rollback_deployment` strategy.
3. **Execution**:
    - `kubectl patch` to scale up healthy replicas (if available) as a safety buffer.
    - `helm rollback` to the last known-good revision.
    - 5-minute bake-time for Canary pods.
    - Full promotion if metrics stabilize.

## Rollback Procedure (Manual Bypass)
If the automated rollback fails or hangs:
1. `kubectl rollout list history deployment/<service-name>`
2. `kubectl rollout undo deployment/<service-name> --to-revision=<stable-id>`
3. Verify pod state: `kubectl get pods -l app=<service-name>`
4. Check logs: `kubectl logs -f deployment/<service-name>`

## Escalation Path
- **Confidence < 80%**: `SHCIA` will not act automatically. Alert `on-call-sre`.
- **System-wide Failure**: If multiple AZs are impacted, SHCIA enters `READ-ONLY` mode. Manually check AWS CloudHealth.
- **Budget Exceeded**: If the operation costs > $500, intervention requires a Senior SRE.
