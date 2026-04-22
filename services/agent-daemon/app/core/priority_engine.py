from typing import Dict, Any, List

class PriorityEngine:
    def arbitrate(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """Convert raw snapshot into ranked priority buckets."""
        buckets = {
            "CRITICAL": [],
            "HIGH": [],
            "MEDIUM": [],
            "LOW": []
        }
        
        # 1. Calendar Analysis
        for meeting in snapshot.get("upcoming_meetings", []):
            mins = meeting.get("time_until_minutes", 999)
            if mins <= 30:
                buckets["CRITICAL"].append(f"Meeting '{meeting.get('title')}' in {mins} min")
            elif mins <= 120:
                buckets["HIGH"].append(f"Meeting '{meeting.get('title')}' in {mins} min")
            else:
                buckets["LOW"].append(f"Meeting '{meeting.get('title')}' later today")
                
        # 2. Email Analysis
        for kw in snapshot.get("urgent_keywords_detected", []):
            if kw.lower() in ["recruiter", "hr", "urgent", "asap"]:
                buckets["HIGH"].append(f"Urgent/Important keyword detected: {kw}")
            else:
                buckets["MEDIUM"].append(f"Keyword detected: {kw}")
                
        unread = snapshot.get("unread_emails", 0)
        if unread > 20:
            buckets["HIGH"].append(f"High email volume: {unread} unread")
        elif unread > 5:
            buckets["MEDIUM"].append(f"Moderate email volume: {unread} unread")
        elif unread > 0:
            buckets["LOW"].append(f"Low email volume: {unread} unread")

        # System signals
        sys_signals = snapshot.get("system_signals", {})
        if sys_signals.get("calendar_pressure") == "high":
            buckets["CRITICAL"].append("calendar_conflict")
            
        return buckets

    def filter_for_llm(self, buckets: Dict[str, Any]) -> Dict[str, Any]:
        """ONLY CRITICAL + HIGH + MEDIUM logic"""
        filtered = {k: v for k, v in buckets.items() if k in ["CRITICAL", "HIGH", "MEDIUM"] and len(v) > 0}
        return filtered

priority_engine = PriorityEngine()
