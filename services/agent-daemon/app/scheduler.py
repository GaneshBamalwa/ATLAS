import asyncio
import logging
from typing import List, Dict, Any
from app.snapshot import build_context_snapshot
from app.decision import evaluate_snapshot
from app.notification import notifier
from app.core.priority_engine import priority_engine
from app.core.personalization_engine import personalization_engine
from app.core.behavioral_memory import behavioral_memory
from app.core.rejection_predictor import rejection_predictor
from app.core.llm_output_firewall import llm_output_firewall

logger = logging.getLogger(__name__)

class SchedulerEngine:
    def __init__(self):
        self.is_running = False
        self.active_users: List[str] = ["admin@example.com"]
        self.last_decisions: Dict[str, List[Dict[str, Any]]] = {}

    def set_active_users(self, user_ids: List[str]):
        self.active_users = user_ids

    async def start(self):
        if self.is_running:
            return
        self.is_running = True
        logger.info("PID Scheduler started.")
        asyncio.create_task(self.light_cycle())
        asyncio.create_task(self.deep_cycle())

    async def stop(self):
        self.is_running = False
        logger.info("PID Scheduler stopped.")

    async def light_cycle(self):
        while self.is_running:
            await asyncio.sleep(60)

    async def deep_cycle(self):
        await asyncio.sleep(10)
        
        while self.is_running:
            logger.info("Running deep cycle...")
            for user_id in self.active_users:
                try:
                    # 1. Fetch raw context
                    snapshot = await build_context_snapshot(user_id)
                    
                    # 2. Priority Engine filters raw context
                    priority_buckets = priority_engine.arbitrate(snapshot)
                    filtered_snapshot = priority_engine.filter_for_llm(priority_buckets)
                    
                    # 3. Personalization Engine
                    personalization_profile = personalization_engine.evaluate(user_id)
                    
                    # Get Long-Term trends
                    behavior_summary = behavioral_memory.evaluate(user_id)
                    
                    # 4. Rejection Predictor filters pre-LLM candidates
                    predicted_suppressed = list(personalization_profile.get("suppressed_suggestion_types", []))
                    predicted_passive = []
                    
                    candidate_types = ["email_summary", "meeting_preparation", "alert", "reminder"]
                    for c_type in candidate_types:
                        pred = rejection_predictor.predict(c_type, user_id, personalization_profile)
                        if pred["should_suppress"] and c_type not in predicted_suppressed:
                            predicted_suppressed.append(c_type)
                        if pred["passive_downgrade"] and c_type not in predicted_passive:
                            predicted_passive.append(c_type)
                    
                    # Update personalization profile for LLM context
                    personalization_profile["suppressed_suggestion_types"] = predicted_suppressed
                    
                    # 5. Decision Engine (Stateful)
                    if user_id not in self.last_decisions:
                        self.last_decisions[user_id] = []
                    last_decisions_list = self.last_decisions[user_id]
                        
                    decision = await evaluate_snapshot(
                        snapshot=filtered_snapshot,
                        personalization_profile=personalization_profile,
                        behavioral_memory=behavior_summary,
                        last_decisions=last_decisions_list
                    )
                    
                    # 6. POST-LLM FIREWALL validates outputs (CRITICAL STEP)
                    raw_suggestions = decision.get("suggestions", [])
                    confidence = decision.get("confidence", 0)
                    
                    firewall_result = llm_output_firewall.validate(
                        user_id=user_id,
                        suggestions=raw_suggestions,
                        confidence=confidence,
                        suppressed_types=predicted_suppressed,
                        passive_downgrade_types=predicted_passive
                    )
                    
                    approved = firewall_result["approved_suggestions"]
                    
                    if approved:
                        # Save stateful history (extend to last 20 config)
                        self.last_decisions[user_id].extend(approved)
                        self.last_decisions[user_id] = self.last_decisions[user_id][-20:]
                        
                        # 7. Global duplicate & feedback aware Notification push
                        await notifier.push_suggestions(user_id, approved)
                        
                except Exception as e:
                    logger.error(f"Deep cycle error for {user_id}: {e}")
                    
            await asyncio.sleep(600)

scheduler = SchedulerEngine()
