"""
Security Controls Library for Threat Generator V3
Standalone implementation for parsing and analyzing security controls in documents.
"""

import re
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

# Security controls definitions
SECURITY_CONTROLS = {
    'authentication': {
        'keywords': ['oauth', 'jwt', 'mfa', '2fa', 'multi-factor', 'authentication', 'sso', 'ldap', 'saml', 'auth0'],
        'mitigates': ['Spoofing', 'Elevation'],
        'risk_reduction': 0.4
    },
    'encryption': {
        'keywords': ['tls', 'ssl', 'https', 'encrypted', 'encryption', 'aes', 'rsa', 'crypto', 'certificate'],
        'mitigates': ['Information Disclosure', 'Tampering'],
        'risk_reduction': 0.5
    },
    'access_control': {
        'keywords': ['rbac', 'acl', 'permission', 'authorization', 'access control', 'role-based', 'policy'],
        'mitigates': ['Elevation', 'Information Disclosure'],
        'risk_reduction': 0.4
    },
    'monitoring': {
        'keywords': ['audit', 'logging', 'monitoring', 'siem', 'detection', 'alert', 'alarm', 'log'],
        'mitigates': ['Repudiation', 'Tampering'],
        'risk_reduction': 0.3
    },
    'validation': {
        'keywords': ['validation', 'sanitization', 'whitelist', 'blacklist', 'input validation', 'parameterized', 'escape'],
        'mitigates': ['Tampering', 'Denial of Service'],
        'risk_reduction': 0.4
    },
    'rate_limiting': {
        'keywords': ['rate limit', 'throttling', 'quota', 'api limit', 'ddos protection', 'flood'],
        'mitigates': ['Denial of Service'],
        'risk_reduction': 0.5
    },
    'network_security': {
        'keywords': ['firewall', 'waf', 'ids', 'ips', 'vpn', 'bastion', 'dmz', 'segmentation', 'vlan'],
        'mitigates': ['Spoofing', 'Tampering', 'Information Disclosure'],
        'risk_reduction': 0.4
    }
}


class ControlsLibrary:
    """
    Security Controls Library for parsing and analyzing security controls in documents.
    """
    
    def __init__(self):
        self.detected_controls = {}
        logger.debug("📚 ControlsLibrary initialized")
    
    def parse_document_for_controls(self, document_text: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Parse document to identify security controls.
        
        Args:
            document_text: The document content to analyze
            
        Returns:
            Dictionary of detected controls with context
        """
        if not document_text:
            logger.warning("📄 No document text provided for control parsing")
            return {}
            
        logger.info(f"🔍 Parsing document for security controls (length: {len(document_text)} chars)")
        
        document_lower = document_text.lower()
        detected = {}
        
        for control_type, control_info in SECURITY_CONTROLS.items():
            found_keywords = []
            for keyword in control_info['keywords']:
                if keyword in document_lower:
                    # Find context around keyword
                    pattern = r'.{0,50}' + re.escape(keyword) + r'.{0,50}'
                    matches = re.findall(pattern, document_lower, re.IGNORECASE)
                    if matches:
                        found_keywords.append({
                            'keyword': keyword,
                            'context': matches[0].strip(),
                            'control_type': control_type
                        })
            
            if found_keywords:
                detected[control_type] = found_keywords
                logger.info(f"✅ Detected {control_type}: {[k['keyword'] for k in found_keywords]}")
        
        self.detected_controls = detected
        logger.info(f"📊 Total security control types detected: {len(detected)}")
        
        return detected
    
    def calculate_residual_risk(self, inherent_impact: str, inherent_likelihood: str, threat_category: str) -> Dict[str, Any]:
        """
        Calculate residual risk based on detected controls.
        
        Args:
            inherent_impact: Original impact level (Critical/High/Medium/Low)
            inherent_likelihood: Original likelihood (High/Medium/Low)
            threat_category: STRIDE category
            
        Returns:
            Dictionary with residual risk calculation
        """
        logger.debug(f"🧮 Calculating residual risk for {threat_category}")
        
        # Risk scoring
        impact_scores = {'Critical': 4, 'High': 3, 'Medium': 2, 'Low': 1}
        likelihood_scores = {'High': 3, 'Medium': 2, 'Low': 1}
        
        impact_score = impact_scores.get(inherent_impact, 2)
        likelihood_score = likelihood_scores.get(inherent_likelihood, 2)
        
        # Find applicable controls
        total_reduction = 0.0
        applicable_controls = []
        
        for control_type, keywords in self.detected_controls.items():
            control_info = SECURITY_CONTROLS[control_type]
            if any(threat_category.lower() in mitigation.lower() for mitigation in control_info['mitigates']):
                total_reduction += control_info['risk_reduction']
                applicable_controls.append(control_type)
        
        # Cap total reduction at 70%
        total_reduction = min(total_reduction, 0.7)
        
        # Calculate residual risk
        adjusted_likelihood_score = max(1, likelihood_score * (1 - total_reduction))
        residual_risk_score = impact_score * adjusted_likelihood_score
        
        # Determine risk level
        if residual_risk_score >= 9:
            residual_level = 'Critical'
        elif residual_risk_score >= 6:
            residual_level = 'High'
        elif residual_risk_score >= 3:
            residual_level = 'Medium'
        else:
            residual_level = 'Low'
        
        result = {
            'inherent_risk_score': impact_score * likelihood_score,
            'residual_risk_score': residual_risk_score,
            'residual_risk_level': residual_level,
            'risk_reduction_percentage': total_reduction * 100,
            'applicable_controls': applicable_controls
        }
        
        logger.debug(f"📊 Residual risk: {inherent_impact} → {residual_level} (controls: {applicable_controls})")
        
        return result


class ResidualRiskCalculator:
    """
    Calculator for residual risk assessment using detected controls.
    """
    
    def __init__(self, controls_library: ControlsLibrary):
        self.controls_library = controls_library
        logger.debug("⚖️ ResidualRiskCalculator initialized")
    
    def calculate_residual_risk(self, threat: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate residual risk for a single threat.
        
        Args:
            threat: Threat dictionary with impact, likelihood, and category
            
        Returns:
            Updated threat with residual risk information
        """
        try:
            inherent_impact = threat.get('impact', 'Medium')
            inherent_likelihood = threat.get('likelihood', 'Medium')
            threat_category = threat.get('category', threat.get('stride_category', 'Unknown'))
            
            risk_calculation = self.controls_library.calculate_residual_risk(
                inherent_impact, inherent_likelihood, threat_category
            )
            
            # Update threat with residual risk
            threat.update({
                'inherent_impact': inherent_impact,
                'inherent_likelihood': inherent_likelihood,
                'residual_impact': inherent_impact,  # Impact typically doesn't change
                'residual_likelihood': self._score_to_level(risk_calculation['residual_risk_score'] / 4),
                'residual_risk_level': risk_calculation['residual_risk_level'],
                'applicable_controls': risk_calculation['applicable_controls'],
                'risk_reduction_percentage': risk_calculation['risk_reduction_percentage']
            })
            
            return threat
            
        except Exception as e:
            logger.error(f"❌ Error calculating residual risk: {e}")
            return threat
    
    def _score_to_level(self, score: float) -> str:
        """Convert numeric score to risk level."""
        if score >= 2.5:
            return 'High'
        elif score >= 1.5:
            return 'Medium'
        else:
            return 'Low'
