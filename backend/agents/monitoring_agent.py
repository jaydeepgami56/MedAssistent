"""
Monitoring Agent - Vital sign monitoring with MEWS scoring and anomaly detection.

Implements Modified Early Warning Score (MEWS) calculation for patient deterioration
detection, trend analysis, and auto-alerting for critical values. Maintains 6-hour
rolling window for vital sign tracking.
"""

import logging
from typing import AsyncIterator
from datetime import datetime, timedelta
from anthropic import Anthropic

from backend.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

# DISCLAIMER - MUST be included in ALL outputs
DISCLAIMER = "AI-assisted vital sign monitoring — requires clinician verification"


class MonitoringAgent(BaseAgent):
    """
    Monitoring Agent for patient vital sign tracking.

    Provides MEWS scoring, vital sign tracking, anomaly detection, and auto-alerting
    for patient deterioration. Uses time-series analysis and Claude for clinical context.
    """

    def __init__(self, anthropic_api_key: str):
        """
        Initialize Monitoring Agent.

        Args:
            anthropic_api_key: Anthropic API key for Claude reasoning
        """
        super().__init__(
            agent_id="monitoring",
            name="Monitoring Agent",
            skills=[
                "vital_tracking",
                "mews_score",
                "anomaly_detection",
                "alert_gen"
            ],
            models_used=["Time-series ML", "Claude API"],
            color="#a855f7",  # Purple
            icon="📊",
            status="Active",
            queue=0
        )

        self.anthropic_client = Anthropic(api_key=anthropic_api_key)

        # In-memory storage for vital signs (6-hour rolling window)
        # Format: {patient_id: [{timestamp, hr, bp_sys, bp_dia, spo2, temp, rr, mews}, ...]}
        self._vital_history: dict[str, list[dict]] = {}

    async def execute_skill(self, skill_name: str, params: dict) -> dict:
        """
        Execute monitoring skill with given parameters.

        Args:
            skill_name: Name of skill to execute
            params: Skill parameters

        Returns:
            dict: Skill execution result

        Raises:
            ValueError: If skill_name not in self.skills
        """
        if skill_name not in self.skills:
            raise ValueError(f"Unknown skill: {skill_name}. Valid skills: {self.skills}")

        if skill_name == "vital_tracking":
            return await self._vital_tracking(params)
        elif skill_name == "mews_score":
            return await self._mews_score(params)
        elif skill_name == "anomaly_detection":
            return await self._anomaly_detection(params)
        elif skill_name == "alert_gen":
            return await self._alert_gen(params)
        else:
            raise ValueError(f"Skill not implemented: {skill_name}")

    async def _mews_score(self, params: dict) -> dict:
        """
        Calculate Modified Early Warning Score (MEWS).

        Args:
            params: dict with keys:
                - hr (int): Heart rate in bpm
                - bp_sys (int): Systolic blood pressure in mmHg
                - spo2 (int): Oxygen saturation in %
                - temp (float): Temperature in Celsius
                - rr (int): Respiratory rate in breaths/min

        Returns:
            dict with keys:
                - mews_total (int): Total MEWS score (0-14)
                - component_scores (dict): Individual component scores
                - alert_level (str): Normal (0-2), Increased (3-4), Critical (5+)
                - details (str): Interpretation of scores
                - recommendations (str): Clinical actions based on MEWS
                - spo2_alert (bool): True if SpO2 < 90%
                - disclaimer (str): Safety disclaimer
        """
        # Extract vital signs
        hr = params.get("hr", 80)
        bp_sys = params.get("bp_sys", 120)
        spo2 = params.get("spo2", 98)
        temp = params.get("temp", 37.0)
        rr = params.get("rr", 16)

        # Calculate individual MEWS component scores
        component_scores = {
            "hr_score": self._calculate_hr_score(hr),
            "bp_score": self._calculate_bp_score(bp_sys),
            "rr_score": self._calculate_rr_score(rr),
            "temp_score": self._calculate_temp_score(temp)
        }

        # Calculate total MEWS
        mews_total = sum(component_scores.values())

        # Determine alert level
        if mews_total >= 5:
            alert_level = "Critical"
        elif mews_total >= 3:
            alert_level = "Increased concern"
        else:
            alert_level = "Normal"

        # Check SpO2 threshold (< 90% = immediate alert)
        spo2_alert = spo2 < 90

        # Build detailed interpretation
        details = self._build_mews_interpretation(
            hr=hr,
            bp_sys=bp_sys,
            spo2=spo2,
            temp=temp,
            rr=rr,
            component_scores=component_scores
        )

        # Generate recommendations
        recommendations = self._generate_mews_recommendations(
            mews_total=mews_total,
            alert_level=alert_level,
            spo2_alert=spo2_alert
        )

        result = {
            "mews_total": mews_total,
            "component_scores": component_scores,
            "alert_level": alert_level,
            "details": details,
            "recommendations": recommendations,
            "spo2_alert": spo2_alert,
            "vitals": {
                "hr": hr,
                "bp_sys": bp_sys,
                "spo2": spo2,
                "temp": temp,
                "rr": rr
            },
            "disclaimer": DISCLAIMER
        }

        # Log audit trail
        self.log_audit(
            request=f"MEWS calculation: HR={hr}, BP={bp_sys}, RR={rr}, Temp={temp}",
            model="MEWS Algorithm",
            confidence=1.0,  # MEWS is deterministic
            action=f"MEWS={mews_total} ({alert_level})"
        )

        return result

    def _calculate_hr_score(self, hr: int) -> int:
        """Calculate MEWS score for heart rate."""
        if hr < 40 or hr > 130:
            return 3
        elif (41 <= hr <= 50) or (111 <= hr <= 130):
            return 2
        elif 101 <= hr <= 110:
            return 1
        else:  # 51-100
            return 0

    def _calculate_bp_score(self, bp_sys: int) -> int:
        """Calculate MEWS score for systolic blood pressure."""
        if bp_sys < 70:
            return 3
        elif 71 <= bp_sys <= 80:
            return 2
        elif bp_sys > 200:
            return 2
        elif 81 <= bp_sys <= 100:
            return 1
        else:  # 101-199
            return 0

    def _calculate_rr_score(self, rr: int) -> int:
        """Calculate MEWS score for respiratory rate."""
        if rr < 9:
            return 2
        elif rr > 29:
            return 3
        elif 21 <= rr <= 29:
            return 2
        elif 15 <= rr <= 20:
            return 1
        else:  # 9-14
            return 0

    def _calculate_temp_score(self, temp: float) -> int:
        """Calculate MEWS score for temperature."""
        if temp < 35.0:
            return 2
        elif temp > 38.5:
            return 2
        else:  # 35.0-38.4
            return 0

    def _build_mews_interpretation(
        self,
        hr: int,
        bp_sys: int,
        spo2: int,
        temp: float,
        rr: int,
        component_scores: dict
    ) -> str:
        """Build detailed interpretation of MEWS components."""
        details = []

        # Heart Rate
        hr_score = component_scores["hr_score"]
        if hr_score == 3:
            details.append(f"HR: {hr} bpm ({hr_score} points) — Severe tachycardia or bradycardia")
        elif hr_score == 2:
            details.append(f"HR: {hr} bpm ({hr_score} points) — Moderate tachycardia or bradycardia")
        elif hr_score == 1:
            details.append(f"HR: {hr} bpm ({hr_score} point) — Mild tachycardia")
        else:
            details.append(f"HR: {hr} bpm ({hr_score} points) — Normal")

        # Blood Pressure
        bp_score = component_scores["bp_score"]
        if bp_score == 3:
            details.append(f"BP: {bp_sys} mmHg ({bp_score} points) — Severe hypotension")
        elif bp_score == 2:
            if bp_sys > 200:
                details.append(f"BP: {bp_sys} mmHg ({bp_score} points) — Severe hypertension")
            else:
                details.append(f"BP: {bp_sys} mmHg ({bp_score} points) — Moderate hypotension")
        elif bp_score == 1:
            details.append(f"BP: {bp_sys} mmHg ({bp_score} point) — Mild hypotension")
        else:
            details.append(f"BP: {bp_sys} mmHg ({bp_score} points) — Normal")

        # Respiratory Rate
        rr_score = component_scores["rr_score"]
        if rr_score == 3:
            details.append(f"RR: {rr} /min ({rr_score} points) — Severe tachypnea")
        elif rr_score == 2:
            if rr < 9:
                details.append(f"RR: {rr} /min ({rr_score} points) — Bradypnea")
            else:
                details.append(f"RR: {rr} /min ({rr_score} points) — Moderate tachypnea")
        elif rr_score == 1:
            details.append(f"RR: {rr} /min ({rr_score} point) — Mild tachypnea")
        else:
            details.append(f"RR: {rr} /min ({rr_score} points) — Normal")

        # Temperature
        temp_score = component_scores["temp_score"]
        if temp_score == 2:
            if temp < 35.0:
                details.append(f"Temp: {temp}°C ({temp_score} points) — Hypothermic")
            else:
                details.append(f"Temp: {temp}°C ({temp_score} points) — Febrile")
        else:
            details.append(f"Temp: {temp}°C ({temp_score} points) — Normal")

        # SpO2
        if spo2 < 90:
            details.append(f"SpO2: {spo2}% — CRITICAL ALERT (below 90% threshold)")
        elif spo2 < 92:
            details.append(f"SpO2: {spo2}% — Warning (below 92%)")
        else:
            details.append(f"SpO2: {spo2}% — Normal")

        return "\n".join(details)

    def _generate_mews_recommendations(
        self,
        mews_total: int,
        alert_level: str,
        spo2_alert: bool
    ) -> str:
        """Generate clinical recommendations based on MEWS score."""
        recommendations = []

        if mews_total >= 5:
            recommendations.append("CRITICAL: MEWS ≥ 5 — Immediate medical review required")
            recommendations.append("AUTOMATIC ESCALATION: Attending physician notification")
            recommendations.append("Action: Bedside assessment within 15 minutes")
            recommendations.append("Increase monitoring frequency to every 15 minutes")
        elif mews_total >= 3:
            recommendations.append("INCREASED CONCERN: MEWS 3-4 — Notify nurse")
            recommendations.append("Increase monitoring frequency to every 30 minutes")
            recommendations.append("Consider senior review if no improvement")
        else:
            recommendations.append("NORMAL: MEWS 0-2 — Routine monitoring")
            recommendations.append("Continue standard monitoring frequency")

        if spo2_alert:
            recommendations.append("CRITICAL: SpO2 < 90% — Immediate intervention required")
            recommendations.append("Apply supplemental oxygen and reassess")
            recommendations.append("Consider ABG and chest imaging")

        return "\n".join(recommendations)

    async def _vital_tracking(self, params: dict) -> dict:
        """
        Store vital signs and maintain 6-hour rolling window.

        Args:
            params: dict with keys:
                - patient_id (str): Patient identifier
                - hr, bp_sys, bp_dia, spo2, temp, rr: Vital signs
                - timestamp (str, optional): ISO format timestamp

        Returns:
            dict with stored vitals and trend analysis
        """
        patient_id = params.get("patient_id", "unknown")
        timestamp_str = params.get("timestamp")

        if timestamp_str:
            timestamp = datetime.fromisoformat(timestamp_str)
        else:
            timestamp = datetime.utcnow()

        # Calculate MEWS for this reading
        mews_result = await self._mews_score(params)

        # Create vital reading record
        reading = {
            "timestamp": timestamp.isoformat(),
            "hr": params.get("hr"),
            "bp_sys": params.get("bp_sys"),
            "bp_dia": params.get("bp_dia"),
            "spo2": params.get("spo2"),
            "temp": params.get("temp"),
            "rr": params.get("rr"),
            "mews": mews_result["mews_total"]
        }

        # Initialize patient history if needed
        if patient_id not in self._vital_history:
            self._vital_history[patient_id] = []

        # Add reading
        self._vital_history[patient_id].append(reading)

        # Prune readings older than 6 hours
        cutoff_time = timestamp - timedelta(hours=6)
        self._vital_history[patient_id] = [
            r for r in self._vital_history[patient_id]
            if datetime.fromisoformat(r["timestamp"]) >= cutoff_time
        ]

        # Calculate trends
        trend_analysis = self._analyze_trends(patient_id)

        result = {
            "stored": True,
            "reading": reading,
            "history_count": len(self._vital_history[patient_id]),
            "window": "6 hours",
            "trend_analysis": trend_analysis,
            "mews_score": mews_result["mews_total"],
            "alert_level": mews_result["alert_level"],
            "disclaimer": DISCLAIMER
        }

        # Log audit trail
        self.log_audit(
            request=f"Vital tracking for patient {patient_id}",
            model="Time-series tracking",
            confidence=1.0,
            action=f"Stored reading (MEWS={mews_result['mews_total']})"
        )

        return result

    def _analyze_trends(self, patient_id: str) -> dict:
        """
        Analyze vital sign trends over 6-hour window.

        Args:
            patient_id: Patient identifier

        Returns:
            dict with trend analysis (improving, stable, deteriorating)
        """
        history = self._vital_history.get(patient_id, [])

        if len(history) < 2:
            return {
                "trend": "insufficient_data",
                "message": "Need at least 2 readings for trend analysis"
            }

        # Sort by timestamp
        sorted_history = sorted(history, key=lambda r: r["timestamp"])

        # Compare MEWS scores over time
        mews_scores = [r["mews"] for r in sorted_history]
        first_half_avg = sum(mews_scores[:len(mews_scores)//2]) / (len(mews_scores)//2)
        second_half_avg = sum(mews_scores[len(mews_scores)//2:]) / (len(mews_scores) - len(mews_scores)//2)

        # Determine trend
        if second_half_avg < first_half_avg - 0.5:
            trend = "improving"
        elif second_half_avg > first_half_avg + 0.5:
            trend = "deteriorating"
        else:
            trend = "stable"

        # Get latest vital ranges
        latest_vitals = sorted_history[-3:] if len(sorted_history) >= 3 else sorted_history

        hr_trend = self._calculate_vital_trend([r["hr"] for r in latest_vitals if r["hr"]])
        bp_trend = self._calculate_vital_trend([r["bp_sys"] for r in latest_vitals if r["bp_sys"]])
        rr_trend = self._calculate_vital_trend([r["rr"] for r in latest_vitals if r["rr"]])

        return {
            "trend": trend,
            "mews_first_half_avg": round(first_half_avg, 1),
            "mews_second_half_avg": round(second_half_avg, 1),
            "vital_trends": {
                "hr": hr_trend,
                "bp_sys": bp_trend,
                "rr": rr_trend
            },
            "readings_count": len(history)
        }

    def _calculate_vital_trend(self, values: list) -> str:
        """Calculate trend for a single vital sign."""
        if len(values) < 2:
            return "stable"

        # Simple linear trend
        if values[-1] > values[0] * 1.1:
            return "increasing"
        elif values[-1] < values[0] * 0.9:
            return "decreasing"
        else:
            return "stable"

    async def _anomaly_detection(self, params: dict) -> dict:
        """
        Detect anomalies in vital signs.

        Args:
            params: dict with patient_id and current vitals

        Returns:
            dict with detected anomalies
        """
        patient_id = params.get("patient_id", "unknown")
        current_vitals = {
            "hr": params.get("hr"),
            "bp_sys": params.get("bp_sys"),
            "spo2": params.get("spo2"),
            "temp": params.get("temp"),
            "rr": params.get("rr")
        }

        history = self._vital_history.get(patient_id, [])

        if len(history) < 3:
            return {
                "anomalies_detected": False,
                "message": "Insufficient baseline data (need at least 3 readings)",
                "disclaimer": DISCLAIMER
            }

        # Calculate baseline (mean of previous readings)
        baseline = {
            "hr": sum(r["hr"] for r in history if r["hr"]) / len([r for r in history if r["hr"]]),
            "bp_sys": sum(r["bp_sys"] for r in history if r["bp_sys"]) / len([r for r in history if r["bp_sys"]]),
            "spo2": sum(r["spo2"] for r in history if r["spo2"]) / len([r for r in history if r["spo2"]]),
            "temp": sum(r["temp"] for r in history if r["temp"]) / len([r for r in history if r["temp"]]),
            "rr": sum(r["rr"] for r in history if r["rr"]) / len([r for r in history if r["rr"]])
        }

        # Detect anomalies (sudden changes from baseline)
        anomalies = []

        # HR deviation > 20% or > 20 bpm
        if current_vitals["hr"]:
            hr_change = abs(current_vitals["hr"] - baseline["hr"])
            if hr_change > 20 or hr_change / baseline["hr"] > 0.20:
                anomalies.append(f"HR: {current_vitals['hr']} bpm (baseline: {baseline['hr']:.1f}) — Sudden change detected")

        # BP deviation > 20 mmHg
        if current_vitals["bp_sys"]:
            bp_change = abs(current_vitals["bp_sys"] - baseline["bp_sys"])
            if bp_change > 20:
                anomalies.append(f"BP: {current_vitals['bp_sys']} mmHg (baseline: {baseline['bp_sys']:.1f}) — Sudden change detected")

        # SpO2 drop > 3%
        if current_vitals["spo2"]:
            spo2_change = baseline["spo2"] - current_vitals["spo2"]
            if spo2_change > 3:
                anomalies.append(f"SpO2: {current_vitals['spo2']}% (baseline: {baseline['spo2']:.1f}%) — Sudden drop detected")

        # Temp change > 0.8°C
        if current_vitals["temp"]:
            temp_change = abs(current_vitals["temp"] - baseline["temp"])
            if temp_change > 0.8:
                anomalies.append(f"Temp: {current_vitals['temp']}°C (baseline: {baseline['temp']:.1f}°C) — Sudden change detected")

        # RR deviation > 5/min
        if current_vitals["rr"]:
            rr_change = abs(current_vitals["rr"] - baseline["rr"])
            if rr_change > 5:
                anomalies.append(f"RR: {current_vitals['rr']}/min (baseline: {baseline['rr']:.1f}/min) — Sudden change detected")

        result = {
            "anomalies_detected": len(anomalies) > 0,
            "anomalies": anomalies,
            "baseline": {k: round(v, 1) for k, v in baseline.items()},
            "current": current_vitals,
            "recommendation": "Escalate to clinical review" if anomalies else "Continue routine monitoring",
            "disclaimer": DISCLAIMER
        }

        # Log audit trail
        self.log_audit(
            request=f"Anomaly detection for patient {patient_id}",
            model="Time-series anomaly detection",
            confidence=0.85,
            action=f"{len(anomalies)} anomalies detected"
        )

        return result

    async def _alert_gen(self, params: dict) -> dict:
        """
        Generate alerts based on MEWS score and SpO2.

        Args:
            params: dict with mews_total, spo2, and patient info

        Returns:
            dict with alert details
        """
        mews_total = params.get("mews_total")
        spo2 = params.get("spo2")
        patient_id = params.get("patient_id", "unknown")

        # If MEWS not provided, calculate it
        if mews_total is None:
            mews_result = await self._mews_score(params)
            mews_total = mews_result["mews_total"]

        alerts = []
        alert_level = "NONE"
        requires_notification = False
        notify_roles = []

        # MEWS >= 5 = Critical alert
        if mews_total >= 5:
            alert_level = "CRITICAL"
            requires_notification = True
            notify_roles = ["Attending Physician", "Charge Nurse", "Rapid Response Team"]
            alerts.append({
                "type": "MEWS_CRITICAL",
                "severity": "critical",
                "message": f"MEWS score {mews_total} (Critical threshold)",
                "action": "Immediate bedside assessment required"
            })

        # MEWS 3-4 = Increased concern
        elif mews_total >= 3:
            alert_level = "WARNING"
            requires_notification = True
            notify_roles = ["Charge Nurse"]
            alerts.append({
                "type": "MEWS_WARNING",
                "severity": "warning",
                "message": f"MEWS score {mews_total} (Increased concern)",
                "action": "Increase monitoring frequency"
            })

        # SpO2 < 90% = Immediate critical alert
        if spo2 is not None and spo2 < 90:
            alert_level = "CRITICAL"
            requires_notification = True
            if "Attending Physician" not in notify_roles:
                notify_roles.append("Attending Physician")
            if "Respiratory Therapy" not in notify_roles:
                notify_roles.append("Respiratory Therapy")

            alerts.append({
                "type": "SPO2_CRITICAL",
                "severity": "critical",
                "message": f"SpO2 {spo2}% (below 90% threshold)",
                "action": "Immediate oxygen therapy and clinical review"
            })

        result = {
            "alert_level": alert_level,
            "requires_notification": requires_notification,
            "notify_roles": notify_roles,
            "alerts": alerts,
            "patient_id": patient_id,
            "mews_total": mews_total,
            "timestamp": datetime.utcnow().isoformat(),
            "disclaimer": DISCLAIMER
        }

        # Log audit trail
        self.log_audit(
            request=f"Alert generation for patient {patient_id}",
            model="MEWS Alert Algorithm",
            confidence=1.0,
            action=f"{alert_level} alert generated"
        )

        return result

    async def chat(self, message: str, context: dict) -> AsyncIterator[str]:
        """
        Stream chat responses about vital sign monitoring.

        Args:
            message: User message
            context: Conversation context

        Yields:
            str: Response tokens
        """
        # Build monitoring-specific system prompt
        system_prompt = f"""You are a vital sign monitoring specialist for the MedAssist AI platform.

Your role:
- Calculate MEWS (Modified Early Warning Score) from vital signs
- Track vital sign trends over time
- Detect anomalies and patient deterioration
- Generate alerts for critical values (MEWS ≥ 5, SpO2 < 90%)
- NEVER provide definitive diagnoses
- ALWAYS include disclaimer: "{DISCLAIMER}"

Context:
- Current patient: {context.get('patient_id', 'Unknown')}
- Recent vitals: {context.get('recent_vitals', 'None')}

Respond concisely and professionally."""

        # Stream response from Claude
        with self.anthropic_client.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": message}]
        ) as stream:
            for text in stream.text_stream:
                yield text

        # Yield disclaimer at the end
        yield f"\n\n{DISCLAIMER}"


# Global agent instance
_monitoring_agent = None


def init_monitoring_agent(anthropic_api_key: str) -> None:
    """
    Initialize global Monitoring Agent.

    Args:
        anthropic_api_key: Anthropic API key for Claude
    """
    global _monitoring_agent
    try:
        _monitoring_agent = MonitoringAgent(anthropic_api_key)
        logger.info("Monitoring Agent initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Monitoring Agent: {e}")
        _monitoring_agent = None


def get_monitoring_agent():
    """
    Get the global Monitoring Agent instance.

    Returns:
        MonitoringAgent or None if not initialized
    """
    return _monitoring_agent
