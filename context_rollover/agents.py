"""Compatibility workers and coordinator for deterministic task evaluation."""
import uuid
from typing import Dict, Any, List, Optional
from .models import FrontierPayload, AgentTelemetryAlert, ExecutionStatus
from .engine import FrontierDomainEngine


class EventJournalVerifierAgent:
    """Specialized Sub-Agent 1: Primary Parameter & Integrity Auditor."""
    def audit(self, payload: FrontierPayload) -> List[AgentTelemetryAlert]:
        alerts = []
        res = FrontierDomainEngine.evaluate_primary_parameter(payload.primary_metric)
        if res:
            alerts.append(AgentTelemetryAlert(
                alert_id=str(uuid.uuid4())[:8],
                origin_agent="EventJournalVerifierAgent",
                status=ExecutionStatus.ELEVATED_RISK,
                summary=res["summary"],
                technical_details=res["details"],
                actionable_remediation=res["remediation"],
            ))
        return alerts


class StateDeltaCompressorAgent:
    """Specialized Sub-Agent 2: Critical Kinetics & Security Safeguard."""
    def audit(self, payload: FrontierPayload) -> List[AgentTelemetryAlert]:
        alerts = []
        res = FrontierDomainEngine.evaluate_secondary_kinetics(payload.secondary_metric, payload.is_critical_flag)
        if res:
            alerts.append(AgentTelemetryAlert(
                alert_id=str(uuid.uuid4())[:8],
                origin_agent="StateDeltaCompressorAgent",
                status=ExecutionStatus.CRITICAL_INTERVENTION if payload.is_critical_flag else ExecutionStatus.ELEVATED_RISK,
                summary=res["summary"],
                technical_details=res["details"],
                actionable_remediation=res["remediation"],
            ))
        return alerts


class RolloverTriggerAgent:
    """Specialized Sub-Agent 3: Protocol Conformance & Anomaly Triager."""
    def audit(self, payload: FrontierPayload) -> List[AgentTelemetryAlert]:
        alerts = []
        res = FrontierDomainEngine.audit_specification_conformance(payload.status_descriptor, payload.attributes)
        if res:
            alerts.append(AgentTelemetryAlert(
                alert_id=str(uuid.uuid4())[:8],
                origin_agent="RolloverTriggerAgent",
                status=ExecutionStatus.ELEVATED_RISK,
                summary=res["summary"],
                technical_details=res["details"],
                actionable_remediation=res["remediation"],
            ))
        return alerts


class StateCheckpointerCoordinator:
    """Coordinate the deterministic compatibility workers."""
    def __init__(self):
        self.sub_1 = EventJournalVerifierAgent()
        self.sub_2 = StateDeltaCompressorAgent()
        self.sub_3 = RolloverTriggerAgent()
        self.execution_ledger: Dict[str, Dict[str, Any]] = {}

    def process(self, payload: FrontierPayload) -> Dict[str, Any]:
        all_alerts: List[AgentTelemetryAlert] = []
        all_alerts.extend(self.sub_1.audit(payload))
        all_alerts.extend(self.sub_2.audit(payload))
        all_alerts.extend(self.sub_3.audit(payload))

        crit_count = sum(1 for a in all_alerts if a.status == ExecutionStatus.CRITICAL_INTERVENTION)
        warn_count = sum(1 for a in all_alerts if a.status == ExecutionStatus.ELEVATED_RISK)

        if crit_count > 0:
            status = ExecutionStatus.CRITICAL_INTERVENTION
        elif warn_count > 0:
            status = ExecutionStatus.ELEVATED_RISK
        else:
            status = ExecutionStatus.NOMINAL

        dossier = {
            "system": "context-rollover-checkpoint-agent",
            "domain": "Autonomous Context Management & State Engines",
            "task_id": payload.task_id,
            "target_identifier": payload.target_identifier,
            "overall_status": status.value,
            "total_alerts": len(all_alerts),
            "critical_count": crit_count,
            "warning_count": warn_count,
            "alerts": [a.to_dict() for a in all_alerts],
            "standard_specification": "Built-in deterministic evaluation rules",
            "consensus_summary": f"Consensus evaluation completed across 3 sub-agents with status [{status.value}].",
        }

        self.execution_ledger[payload.task_id] = dossier
        return dossier

    def query_supervisory_chat(self, query: str) -> str:
        q = query.strip().lower()
        if "status" in q or "ledger" in q:
            return f"Context Rollover Checkpoint Agent currently holds {len(self.execution_ledger)} task result(s) in process memory."
        elif "standard" in q or "spec" in q:
            return "Active runtime operating strictly according to Built-in deterministic evaluation rules specifications."
        else:
            return f"Context Rollover Checkpoint Agent compatibility coordinator is ready."
