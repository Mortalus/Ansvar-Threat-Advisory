"""
Few-shot learning service that uses ThreatFeedback to improve agent prompts.

This service analyzes user feedback patterns and includes validated examples 
in agent prompts to improve future threat generation quality.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime, timedelta

from app.models.threat_feedback import ThreatFeedback, ValidationAction
from app.models.pipeline import Pipeline

logger = logging.getLogger(__name__)

class FeedbackLearningService:
    """Service for implementing few-shot learning from user feedback."""
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.max_examples = 3  # Number of examples to include in prompts
        self.min_confidence = 3  # Minimum confidence rating for examples
    
    async def get_few_shot_examples(
        self, 
        step_name: str, 
        agent_type: Optional[str] = None,
        example_type: str = "positive"
    ) -> List[Dict[str, Any]]:
        """
        Get few-shot examples for a specific step/agent from user feedback.
        
        Args:
            step_name: Pipeline step name (e.g., 'threat_generation', 'threat_refinement')
            agent_type: Agent type (e.g., 'architectural_risk', 'business_financial')  
            example_type: 'positive' (accepted/highly-rated) or 'negative' (deleted/low-rated)
            
        Returns:
            List of example dictionaries with original and improved content
        """
        
        try:
            # Determine feedback actions based on example type
            if example_type == "positive":
                target_actions = [ValidationAction.ACCEPTED, ValidationAction.EDITED]
                confidence_filter = self.min_confidence
                order_by_confidence = True
            else:
                target_actions = [ValidationAction.DELETED]
                confidence_filter = 1  # Include low confidence for negative examples
                order_by_confidence = False
            
            # Build query to get relevant feedback
            query = select(ThreatFeedback).where(
                ThreatFeedback.action.in_(target_actions)
            )
            
            # Filter by confidence if specified
            if confidence_filter > 1:
                query = query.where(
                    ThreatFeedback.confidence_rating >= confidence_filter
                )
            
            # Order by confidence and recency
            if order_by_confidence:
                query = query.order_by(
                    desc(ThreatFeedback.confidence_rating),
                    desc(ThreatFeedback.feedback_at)
                )
            else:
                query = query.order_by(desc(ThreatFeedback.feedback_at))
            
            # Limit results
            query = query.limit(self.max_examples * 2)  # Get extra to filter better
            
            result = await self.db_session.execute(query)
            feedback_records = result.scalars().all()
            
            # Convert feedback to few-shot examples
            examples = []
            for feedback in feedback_records:
                try:
                    original_threat = json.loads(feedback.original_threat)
                    
                    example = {
                        "original": original_threat,
                        "feedback_action": feedback.action.value,
                        "confidence": feedback.confidence_rating,
                        "feedback_at": feedback.feedback_at.isoformat(),
                        "threat_id": feedback.threat_id
                    }
                    
                    # Add edited content if available
                    if feedback.edited_content and feedback.action == ValidationAction.EDITED:
                        try:
                            example["improved"] = json.loads(feedback.edited_content)
                        except json.JSONDecodeError:
                            example["improved_text"] = feedback.edited_content
                    
                    # Add reasoning if available
                    if feedback.feedback_reason:
                        example["reasoning"] = feedback.feedback_reason
                    
                    examples.append(example)
                    
                    if len(examples) >= self.max_examples:
                        break
                        
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in feedback {feedback.id}: {feedback.original_threat}")
                    continue
            
            logger.info(f"Retrieved {len(examples)} few-shot examples for {step_name}/{agent_type}")
            return examples
            
        except Exception as e:
            logger.error(f"Failed to get few-shot examples: {e}")
            return []
    
    async def enhance_prompt_with_examples(
        self,
        base_prompt: str,
        step_name: str,
        agent_type: Optional[str] = None,
        include_positive: bool = True,
        include_negative: bool = False
    ) -> str:
        """
        Enhance a base prompt with few-shot examples from user feedback.
        
        Args:
            base_prompt: Original system prompt
            step_name: Pipeline step name  
            agent_type: Agent type (if applicable)
            include_positive: Include positive examples (accepted/edited threats)
            include_negative: Include negative examples (deleted/rejected threats)
            
        Returns:
            Enhanced prompt with few-shot examples
        """
        
        enhanced_prompt = base_prompt
        
        try:
            examples_section = []
            
            # Get positive examples
            if include_positive:
                positive_examples = await self.get_few_shot_examples(
                    step_name, agent_type, "positive"
                )
                
                if positive_examples:
                    examples_section.append("\n## POSITIVE EXAMPLES (High-Quality Threats)")
                    examples_section.append("Learn from these user-validated examples:\n")
                    
                    for i, example in enumerate(positive_examples, 1):
                        examples_section.append(f"### Example {i} (Confidence: {example.get('confidence', 'N/A')}/5)")
                        
                        # Show original threat
                        original = example["original"]
                        examples_section.append("**Original Threat:**")
                        examples_section.append(f"- Name: {original.get('Threat Name', 'N/A')}")
                        examples_section.append(f"- Description: {original.get('Description', 'N/A')}")
                        examples_section.append(f"- Component: {original.get('component_name', 'N/A')}")
                        
                        # Show user action and improvements
                        if example["feedback_action"] == "accepted":
                            examples_section.append("**User Action:** ✅ ACCEPTED as high-quality")
                            
                        elif example["feedback_action"] == "edited":
                            examples_section.append("**User Action:** ✏️ EDITED (improvements shown)")
                            if "improved" in example:
                                improved = example["improved"]
                                examples_section.append("**User's Improved Version:**")
                                examples_section.append(f"- Name: {improved.get('Threat Name', 'N/A')}")
                                examples_section.append(f"- Description: {improved.get('Description', 'N/A')}")
                            elif "improved_text" in example:
                                examples_section.append(f"**User's Improvements:** {example['improved_text']}")
                        
                        # Show reasoning if available
                        if example.get("reasoning"):
                            examples_section.append(f"**User Reasoning:** {example['reasoning']}")
                        
                        examples_section.append("")  # Blank line between examples
            
            # Get negative examples  
            if include_negative:
                negative_examples = await self.get_few_shot_examples(
                    step_name, agent_type, "negative"
                )
                
                if negative_examples:
                    examples_section.append("\n## NEGATIVE EXAMPLES (Low-Quality Threats)")
                    examples_section.append("Avoid generating threats like these:\n")
                    
                    for i, example in enumerate(negative_examples, 1):
                        examples_section.append(f"### Rejected Example {i}")
                        
                        original = example["original"] 
                        examples_section.append("**Rejected Threat:**")
                        examples_section.append(f"- Name: {original.get('Threat Name', 'N/A')}")
                        examples_section.append(f"- Description: {original.get('Description', 'N/A')}")
                        examples_section.append("**User Action:** ❌ DELETED (low quality)")
                        
                        if example.get("reasoning"):
                            examples_section.append(f"**Why Rejected:** {example['reasoning']}")
                        
                        examples_section.append("")
            
            # Combine base prompt with examples
            if examples_section:
                enhanced_prompt = base_prompt + "\n\n" + "\n".join(examples_section)
                enhanced_prompt += "\n\n**Remember:** Use these examples to generate similar high-quality threats and avoid the patterns that users rejected."
            
            return enhanced_prompt
            
        except Exception as e:
            logger.error(f"Failed to enhance prompt with examples: {e}")
            return base_prompt  # Return original on failure
    
    async def get_feedback_statistics(self) -> Dict[str, Any]:
        """Get statistics about user feedback patterns."""
        
        try:
            # Total feedback count
            total_feedback = await self.db_session.scalar(
                select(func.count(ThreatFeedback.id))
            )
            
            # Feedback by action type
            action_counts = {}
            for action in ValidationAction:
                count = await self.db_session.scalar(
                    select(func.count(ThreatFeedback.id)).where(
                        ThreatFeedback.action == action
                    )
                )
                action_counts[action.value] = count
            
            # Average confidence rating
            avg_confidence = await self.db_session.scalar(
                select(func.avg(ThreatFeedback.confidence_rating)).where(
                    ThreatFeedback.confidence_rating.isnot(None)
                )
            )
            
            # Recent feedback (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_feedback = await self.db_session.scalar(
                select(func.count(ThreatFeedback.id)).where(
                    ThreatFeedback.feedback_at >= thirty_days_ago
                )
            )
            
            return {
                "total_feedback": total_feedback or 0,
                "action_distribution": action_counts,
                "average_confidence": round(float(avg_confidence or 0), 2),
                "recent_feedback_30d": recent_feedback or 0,
                "learning_examples_available": total_feedback >= self.max_examples
            }
            
        except Exception as e:
            logger.error(f"Failed to get feedback statistics: {e}")
            return {
                "total_feedback": 0,
                "action_distribution": {},
                "average_confidence": 0,
                "recent_feedback_30d": 0,
                "learning_examples_available": False
            }