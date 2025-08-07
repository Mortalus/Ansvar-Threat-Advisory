"""Token counting utilities for LLM cost estimation"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class TokenCounter:
    """Utility for counting tokens and estimating costs"""
    
    # Rough token estimation - 1 token ≈ 4 characters for most models
    CHARS_PER_TOKEN = 4
    
    # Pricing per 1K tokens (approximate USD, update as needed)
    TOKEN_PRICING = {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-3.5-turbo": {"input": 0.001, "output": 0.002},
        "llama-3.1-70b": {"input": 0.0004, "output": 0.0006},  # Scaleway pricing
        "llama-3.3-70b-instruct": {"input": 0.0004, "output": 0.0006},
        "claude-3-sonnet": {"input": 0.003, "output": 0.015},
        "default": {"input": 0.001, "output": 0.002}  # Fallback pricing
    }
    
    @classmethod
    def estimate_tokens(cls, text: str) -> int:
        """
        Estimate token count from text.
        This is a rough approximation - actual tokenization varies by model.
        """
        if not text:
            return 0
        return max(1, len(text) // cls.CHARS_PER_TOKEN)
    
    @classmethod
    def estimate_cost(cls, input_tokens: int, output_tokens: int, model: str = "default") -> Dict[str, Any]:
        """
        Estimate cost for input and output tokens.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens  
            model: Model name for pricing lookup
            
        Returns:
            Dictionary with cost breakdown
        """
        # Get pricing for model (case insensitive)
        model_key = model.lower()
        pricing = cls.TOKEN_PRICING.get(model_key, cls.TOKEN_PRICING["default"])
        
        # Calculate costs (per 1K tokens)
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        total_cost = input_cost + output_cost
        
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "input_cost_usd": round(input_cost, 6),
            "output_cost_usd": round(output_cost, 6), 
            "total_cost_usd": round(total_cost, 6),
            "model": model,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @classmethod
    def track_llm_usage(cls, prompt: str, response: str, model: str = "default") -> Dict[str, Any]:
        """
        Track LLM usage for a single prompt/response pair.
        
        Args:
            prompt: Input prompt text
            response: LLM response text
            model: Model name
            
        Returns:
            Usage tracking data
        """
        input_tokens = cls.estimate_tokens(prompt)
        output_tokens = cls.estimate_tokens(response)
        
        cost_data = cls.estimate_cost(input_tokens, output_tokens, model)
        
        logger.debug(f"LLM Usage: {model} - {input_tokens} in + {output_tokens} out = ${cost_data['total_cost_usd']:.6f}")
        
        return cost_data

class PipelineTokenTracker:
    """Tracks token usage across an entire pipeline run"""
    
    def __init__(self):
        self.usage_log = []
        self.total_cost = 0.0
        self.total_tokens = 0
        
    def add_llm_call(self, step_name: str, agent_type: Optional[str], prompt: str, response: str, model: str):
        """Add an LLM call to the tracking log"""
        usage = TokenCounter.track_llm_usage(prompt, response, model)
        
        entry = {
            "step_name": step_name,
            "agent_type": agent_type,
            "usage": usage
        }
        
        self.usage_log.append(entry)
        self.total_cost += usage["total_cost_usd"]
        self.total_tokens += usage["total_tokens"]
        
        logger.info(f"Token tracking: {step_name}/{agent_type} - {usage['total_tokens']} tokens, ${usage['total_cost_usd']:.6f}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all token usage"""
        
        # Group by step
        by_step = {}
        for entry in self.usage_log:
            step = entry["step_name"]
            if step not in by_step:
                by_step[step] = {
                    "calls": 0,
                    "total_tokens": 0,
                    "total_cost": 0.0
                }
            
            by_step[step]["calls"] += 1
            by_step[step]["total_tokens"] += entry["usage"]["total_tokens"]
            by_step[step]["total_cost"] += entry["usage"]["total_cost_usd"]
        
        return {
            "total_calls": len(self.usage_log),
            "total_tokens": self.total_tokens,
            "total_cost_usd": round(self.total_cost, 6),
            "by_step": by_step,
            "cost_breakdown": [
                {
                    "step": entry["step_name"],
                    "agent": entry["agent_type"],
                    "tokens": entry["usage"]["total_tokens"],
                    "cost": entry["usage"]["total_cost_usd"],
                    "model": entry["usage"]["model"]
                }
                for entry in self.usage_log
            ]
        }
    
    def get_discrete_summary(self) -> str:
        """Get a small, discrete summary for UI display"""
        if not self.usage_log:
            return "No LLM usage"
        
        return f"🪙 {self.total_tokens:,} tokens • ${self.total_cost:.4f}"