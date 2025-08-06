"""
Multi-Agent Threat Analysis System
Part 2 of the three-stage threat modeling improvement plan.

This module implements specialized analyzer agents that examine systems from different perspectives:
1. Architectural Risk Agent - Detects systemic and foundational flaws
2. Business & Financial Risk Agent - Connects technical threats to business impact
3. Compliance & Governance Agent - Views system through auditor's lens
"""

import re
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseAnalyzerAgent(ABC):
    """Base class for all specialized analyzer agents."""
    
    def __init__(self, name: str, focus_area: str):
        self.name = name
        self.focus_area = focus_area
        self.findings = []
        
    @abstractmethod
    async def analyze(
        self, 
        document_text: str,
        dfd_components: Dict[str, Any],
        existing_threats: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Analyze the system from this agent's perspective."""
        pass
    
    def _extract_context(self, text: str, keyword: str, window: int = 100) -> str:
        """Extract context around a keyword."""
        text_lower = text.lower()
        keyword_lower = keyword.lower()
        
        if keyword_lower not in text_lower:
            return ""
        
        idx = text_lower.index(keyword_lower)
        start = max(0, idx - window)
        end = min(len(text), idx + len(keyword) + window)
        
        return text[start:end].strip()


class ArchitecturalRiskAgent(BaseAnalyzerAgent):
    """
    Architectural Risk Agent
    Mission: Detect systemic, foundational flaws often missed by traditional scanners.
    """
    
    def __init__(self):
        super().__init__(
            name="Architectural Risk Agent",
            focus_area="System Architecture and Design Patterns"
        )
        
        # Architectural anti-patterns to detect
        self.anti_patterns = {
            'single_point_of_failure': [
                'single point of failure', 'spof', 'no redundancy', 
                'single instance', 'no failover', 'single server'
            ],
            'shared_database': [
                'shared database', 'shared db', 'common database',
                'monolithic database', 'single database for all'
            ],
            'insufficient_segmentation': [
                'no segmentation', 'flat network', 'same vpc',
                'no isolation', 'shared environment', 'no dmz'
            ],
            'untested_dr': [
                'dr not tested', 'recovery never tested', 'no dr test',
                'backup not verified', 'untested backup'
            ],
            'tight_coupling': [
                'tightly coupled', 'direct dependency', 'synchronous only',
                'no message queue', 'no event bus'
            ],
            'missing_caching': [
                'no cache', 'no caching', 'without cache',
                'direct database access', 'no cdn'
            ],
            'no_rate_limiting': [
                'no rate limit', 'unlimited requests', 'no throttling',
                'no api limits', 'unprotected endpoint'
            ]
        }
        
        # Component patterns that indicate architectural risks
        self.risky_patterns = {
            'centralized_auth': {
                'indicators': ['authentication service', 'auth service', 'login service'],
                'risk': 'Single authentication service is a critical SPOF'
            },
            'public_database': {
                'indicators': ['external', 'public', 'internet'],
                'component_type': 'data_store',
                'risk': 'Database exposed to public network'
            },
            'missing_gateway': {
                'indicators': ['direct access', 'no gateway', 'no proxy'],
                'risk': 'Services exposed without API gateway protection'
            }
        }
    
    async def analyze(
        self,
        document_text: str,
        dfd_components: Dict[str, Any],
        existing_threats: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Analyze for architectural risks."""
        findings = []
        
        # 1. Check for architectural anti-patterns in document
        for pattern_name, keywords in self.anti_patterns.items():
            for keyword in keywords:
                if keyword in document_text.lower():
                    context = self._extract_context(document_text, keyword)
                    
                    finding = {
                        'agent': self.name,
                        'type': 'Architectural Risk',
                        'pattern': pattern_name,
                        'severity': self._assess_pattern_severity(pattern_name),
                        'finding': f"Detected {pattern_name.replace('_', ' ')}: {keyword}",
                        'context': context,
                        'recommendation': self._get_pattern_recommendation(pattern_name)
                    }
                    findings.append(finding)
                    logger.info(f"Architectural Risk Agent found: {pattern_name}")
        
        # 2. Analyze component architecture
        findings.extend(self._analyze_component_architecture(dfd_components))
        
        # 3. Check for missing architectural components
        findings.extend(self._check_missing_components(dfd_components))
        
        # 4. Analyze data flow patterns
        findings.extend(self._analyze_data_flow_patterns(dfd_components))
        
        # Convert findings to threats
        threats = self._convert_findings_to_threats(findings)
        
        return threats
    
    def _analyze_component_architecture(self, dfd_components: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze component structure for architectural issues."""
        findings = []
        
        # Check for single points of failure
        processes = dfd_components.get('processes', [])
        critical_services = ['authentication', 'auth', 'payment', 'order', 'database']
        
        for process in processes:
            process_name = process.get('name', '').lower() if isinstance(process, dict) else str(process).lower()
            
            for critical in critical_services:
                if critical in process_name:
                    # Check if there's redundancy
                    redundant = any(
                        critical in (p.get('name', '').lower() if isinstance(p, dict) else str(p).lower())
                        for p in processes if p != process
                    )
                    
                    if not redundant:
                        findings.append({
                            'agent': self.name,
                            'type': 'Single Point of Failure',
                            'component': process_name,
                            'severity': 'High',
                            'finding': f"{process_name} appears to be a single point of failure",
                            'recommendation': f"Implement redundancy for {process_name} with load balancing and failover"
                        })
        
        # Check for missing API gateway
        external_entities = dfd_components.get('external_entities', [])
        has_gateway = any(
            'gateway' in (p.get('name', '').lower() if isinstance(p, dict) else str(p).lower())
            for p in processes
        )
        
        if external_entities and not has_gateway:
            findings.append({
                'agent': self.name,
                'type': 'Missing Component',
                'severity': 'Medium',
                'finding': 'No API Gateway detected for external access',
                'recommendation': 'Implement API Gateway for centralized authentication, rate limiting, and monitoring'
            })
        
        return findings
    
    def _check_missing_components(self, dfd_components: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for missing critical architectural components."""
        findings = []
        processes = dfd_components.get('processes', [])
        process_names = [
            p.get('name', '').lower() if isinstance(p, dict) else str(p).lower()
            for p in processes
        ]
        
        # Critical components that should exist
        required_components = {
            'cache': ['cache', 'redis', 'memcached'],
            'queue': ['queue', 'message', 'kafka', 'rabbitmq', 'sqs'],
            'monitoring': ['monitoring', 'logging', 'observability', 'metrics'],
            'backup': ['backup', 'disaster recovery', 'dr']
        }
        
        for component_type, indicators in required_components.items():
            found = any(
                any(indicator in name for indicator in indicators)
                for name in process_names
            )
            
            if not found:
                findings.append({
                    'agent': self.name,
                    'type': 'Missing Architecture Component',
                    'severity': 'Medium' if component_type != 'backup' else 'High',
                    'finding': f'No {component_type} component detected in architecture',
                    'recommendation': self._get_component_recommendation(component_type)
                })
        
        return findings
    
    def _analyze_data_flow_patterns(self, dfd_components: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze data flow patterns for architectural risks."""
        findings = []
        data_flows = dfd_components.get('data_flows', [])
        
        # Check for direct database access from external entities
        external_entities = [
            e.get('name', '') if isinstance(e, dict) else str(e)
            for e in dfd_components.get('external_entities', [])
        ]
        
        data_stores = [
            d.get('name', '') if isinstance(d, dict) else str(d)
            for d in dfd_components.get('data_stores', [])
        ]
        
        for flow in data_flows:
            if isinstance(flow, dict):
                source = flow.get('source', '')
                destination = flow.get('destination', '')
                
                # Check for direct external to database flows
                if source in external_entities and destination in data_stores:
                    findings.append({
                        'agent': self.name,
                        'type': 'Architectural Flaw',
                        'severity': 'Critical',
                        'finding': f'Direct data flow from external entity "{source}" to data store "{destination}"',
                        'recommendation': 'Implement service layer between external entities and data stores'
                    })
        
        return findings
    
    def _assess_pattern_severity(self, pattern: str) -> str:
        """Assess severity of architectural pattern."""
        critical_patterns = ['single_point_of_failure', 'insufficient_segmentation', 'untested_dr']
        high_patterns = ['shared_database', 'no_rate_limiting']
        
        if pattern in critical_patterns:
            return 'Critical'
        elif pattern in high_patterns:
            return 'High'
        else:
            return 'Medium'
    
    def _get_pattern_recommendation(self, pattern: str) -> str:
        """Get recommendation for architectural pattern."""
        recommendations = {
            'single_point_of_failure': 'Implement redundancy with load balancing and automatic failover',
            'shared_database': 'Consider database per service pattern or implement proper data isolation',
            'insufficient_segmentation': 'Implement network segmentation with VLANs, subnets, and security groups',
            'untested_dr': 'Establish regular DR testing schedule with documented RTO/RPO targets',
            'tight_coupling': 'Introduce message queues or event bus for asynchronous communication',
            'missing_caching': 'Implement caching strategy with Redis/Memcached and CDN for static content',
            'no_rate_limiting': 'Implement rate limiting at API gateway and application levels'
        }
        return recommendations.get(pattern, 'Review and address architectural concern')
    
    def _get_component_recommendation(self, component_type: str) -> str:
        """Get recommendation for missing component."""
        recommendations = {
            'cache': 'Implement caching layer (Redis/Memcached) to reduce database load and improve performance',
            'queue': 'Add message queue (Kafka/RabbitMQ) for asynchronous processing and decoupling',
            'monitoring': 'Implement comprehensive monitoring with metrics, logging, and alerting',
            'backup': 'Establish automated backup strategy with regular testing and documented recovery procedures'
        }
        return recommendations.get(component_type, f'Consider adding {component_type} to architecture')
    
    def _convert_findings_to_threats(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert architectural findings to threat format."""
        threats = []
        
        for finding in findings:
            threat = {
                'Threat Category': 'Architectural',
                'Threat Name': f"Architectural Risk: {finding['type']}",
                'Description': finding['finding'],
                'Potential Impact': finding['severity'],
                'Likelihood': 'High' if finding['severity'] == 'Critical' else 'Medium',
                'Suggested Mitigation': finding['recommendation'],
                'component_name': finding.get('component', 'System Architecture'),
                'component_type': 'architecture',
                'agent_source': self.name,
                'analysis_type': 'architectural',
                'pattern_detected': finding.get('pattern', ''),
                'context': finding.get('context', '')
            }
            threats.append(threat)
        
        return threats


class BusinessFinancialRiskAgent(BaseAnalyzerAgent):
    """
    Business & Financial Risk Agent
    Mission: Connect technical threats to tangible business impact.
    """
    
    def __init__(self):
        super().__init__(
            name="Business & Financial Risk Agent",
            focus_area="Business Impact and Financial Risk"
        )
        
        # Business impact indicators
        self.impact_indicators = {
            'revenue': ['revenue', 'sales', 'income', 'profit', 'earning'],
            'cost': ['cost', 'expense', 'budget', 'financial', 'money', 'dollar', '$'],
            'downtime': ['downtime', 'availability', 'uptime', 'sla', 'outage'],
            'customers': ['customer', 'user', 'client', 'subscriber', 'member'],
            'reputation': ['reputation', 'brand', 'trust', 'confidence', 'public'],
            'operations': ['operation', 'business', 'process', 'workflow', 'productivity']
        }
        
        # SLA and business requirement patterns
        self.sla_patterns = {
            'uptime': r'(\d+\.?\d*)\s*%\s*(?:uptime|availability|sla)',
            'rto': r'rto[:\s]+(\d+)\s*(hour|minute|second|day)',
            'rpo': r'rpo[:\s]+(\d+)\s*(hour|minute|second|day)',
            'response_time': r'response\s+time[:\s]+(\d+)\s*(ms|millisecond|second)',
            'cost_per_hour': r'\$(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:per|\/)\s*hour',
            'cost_per_incident': r'\$(\d+(?:,\d{3})*(?:\.\d+)?)\s*per\s*(?:incident|breach|record)',
            'user_count': r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:user|customer|client)',
        }
    
    async def analyze(
        self,
        document_text: str,
        dfd_components: Dict[str, Any],
        existing_threats: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Analyze for business and financial risks."""
        findings = []
        
        # 1. Extract business metrics from document
        business_metrics = self._extract_business_metrics(document_text)
        
        # 2. Analyze critical business processes
        findings.extend(self._analyze_business_critical_components(dfd_components, business_metrics))
        
        # 3. Calculate financial impact of threats
        findings.extend(self._calculate_threat_financial_impact(existing_threats, business_metrics))
        
        # 4. Identify business continuity risks
        findings.extend(self._analyze_business_continuity(dfd_components, business_metrics))
        
        # 5. Assess customer impact
        findings.extend(self._assess_customer_impact(dfd_components, business_metrics))
        
        # Convert to threats
        threats = self._convert_findings_to_threats(findings, business_metrics)
        
        return threats
    
    def _extract_business_metrics(self, document_text: str) -> Dict[str, Any]:
        """Extract business metrics and requirements from document."""
        metrics = {
            'sla': {},
            'costs': {},
            'scale': {},
            'requirements': []
        }
        
        # Extract SLA requirements
        for metric_name, pattern in self.sla_patterns.items():
            matches = re.findall(pattern, document_text.lower())
            if matches:
                metrics['sla'][metric_name] = matches[0] if matches else None
                logger.info(f"Business Agent found {metric_name}: {matches[0]}")
        
        # Extract cost implications
        cost_matches = re.findall(r'\$(\d+(?:,\d{3})*(?:\.\d+)?)', document_text)
        if cost_matches:
            metrics['costs']['identified_amounts'] = cost_matches
        
        # Look for business requirements
        for impact_type, keywords in self.impact_indicators.items():
            for keyword in keywords:
                if keyword in document_text.lower():
                    metrics['requirements'].append(impact_type)
                    break
        
        return metrics
    
    def _analyze_business_critical_components(
        self, 
        dfd_components: Dict[str, Any],
        business_metrics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify business-critical components and their risks."""
        findings = []
        
        # Business-critical keywords
        critical_keywords = [
            'payment', 'billing', 'invoice', 'transaction',
            'order', 'checkout', 'cart', 'purchase',
            'customer', 'user', 'account', 'profile',
            'inventory', 'stock', 'product', 'catalog'
        ]
        
        processes = dfd_components.get('processes', [])
        
        for process in processes:
            process_name = process.get('name', '').lower() if isinstance(process, dict) else str(process).lower()
            
            # Check if this is a business-critical process
            is_critical = any(keyword in process_name for keyword in critical_keywords)
            
            if is_critical:
                # Calculate potential business impact
                impact = self._calculate_component_business_impact(process_name, business_metrics)
                
                if impact['severity'] in ['High', 'Critical']:
                    findings.append({
                        'component': process_name,
                        'type': 'Business-Critical Component',
                        'severity': impact['severity'],
                        'business_impact': impact['description'],
                        'financial_exposure': impact.get('financial_exposure', 'Unknown'),
                        'recommendation': f"Implement enhanced protection for {process_name} due to high business impact"
                    })
        
        return findings
    
    def _calculate_threat_financial_impact(
        self,
        existing_threats: List[Dict[str, Any]],
        business_metrics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Calculate financial impact for existing threats."""
        findings = []
        
        # Get cost per hour if available
        cost_per_hour = None
        if 'cost_per_hour' in business_metrics['sla']:
            try:
                cost_per_hour = float(business_metrics['sla']['cost_per_hour'][0].replace(',', ''))
            except:
                pass
        
        for threat in existing_threats[:10]:  # Analyze top 10 threats
            threat_category = threat.get('Threat Category', '')
            component = threat.get('component_name', '')
            
            # Calculate financial impact based on threat type
            if 'denial' in threat_category.lower() and cost_per_hour:
                # DoS threats impact availability
                financial_impact = f"${cost_per_hour:,.0f} per hour of downtime"
                business_impact = f"Service disruption could cost {financial_impact}"
            elif 'disclosure' in threat_category.lower():
                # Data breach costs
                financial_impact = "$150-$300 per compromised record (industry average)"
                business_impact = "Data breach could result in regulatory fines and customer compensation"
            elif 'tampering' in threat_category.lower():
                financial_impact = "Data integrity loss requiring full audit and recovery"
                business_impact = "Transaction manipulation could cause revenue loss and legal liability"
            else:
                continue
            
            findings.append({
                'threat_id': threat.get('id', ''),
                'component': component,
                'type': 'Financial Risk Assessment',
                'severity': 'High',
                'business_impact': business_impact,
                'financial_exposure': financial_impact,
                'threat_category': threat_category
            })
        
        return findings
    
    def _analyze_business_continuity(
        self,
        dfd_components: Dict[str, Any],
        business_metrics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Analyze business continuity risks."""
        findings = []
        
        # Check for backup and recovery components
        processes = dfd_components.get('processes', [])
        has_backup = any(
            'backup' in (p.get('name', '').lower() if isinstance(p, dict) else str(p).lower())
            for p in processes
        )
        
        # Check RTO/RPO requirements
        rto = business_metrics['sla'].get('rto')
        rpo = business_metrics['sla'].get('rpo')
        
        if (rto or rpo) and not has_backup:
            findings.append({
                'type': 'Business Continuity Risk',
                'severity': 'Critical',
                'business_impact': f"No backup strategy detected despite RTO/RPO requirements",
                'financial_exposure': 'Complete business disruption in case of disaster',
                'recommendation': 'Implement comprehensive backup and disaster recovery strategy'
            })
        
        # Check uptime SLA
        uptime_sla = business_metrics['sla'].get('uptime')
        if uptime_sla:
            try:
                uptime_percent = float(uptime_sla[0])
                if uptime_percent >= 99.9:  # High availability requirement
                    findings.append({
                        'type': 'SLA Risk',
                        'severity': 'High',
                        'business_impact': f"{uptime_percent}% uptime SLA requires robust architecture",
                        'financial_exposure': 'SLA penalties and customer churn for violations',
                        'recommendation': 'Implement high availability with redundancy and auto-failover'
                    })
            except:
                pass
        
        return findings
    
    def _assess_customer_impact(
        self,
        dfd_components: Dict[str, Any],
        business_metrics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Assess customer-facing risks."""
        findings = []
        
        # Check for customer-facing components
        external_entities = dfd_components.get('external_entities', [])
        customer_entities = [
            e for e in external_entities
            if 'customer' in (e.get('name', '').lower() if isinstance(e, dict) else str(e).lower())
        ]
        
        if customer_entities:
            # Look for customer data stores
            data_stores = dfd_components.get('data_stores', [])
            customer_data = [
                d for d in data_stores
                if any(keyword in (d.get('name', '').lower() if isinstance(d, dict) else str(d).lower())
                      for keyword in ['user', 'customer', 'profile', 'account'])
            ]
            
            if customer_data:
                findings.append({
                    'type': 'Customer Data Risk',
                    'severity': 'High',
                    'business_impact': 'Customer data breach could result in loss of trust and legal action',
                    'financial_exposure': 'GDPR fines up to 4% of annual revenue',
                    'recommendation': 'Implement data protection measures including encryption and access controls'
                })
        
        return findings
    
    def _calculate_component_business_impact(
        self,
        component_name: str,
        business_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate business impact for a component."""
        impact = {
            'severity': 'Medium',
            'description': '',
            'financial_exposure': 'Unknown'
        }
        
        # Payment/transaction components are always critical
        if any(keyword in component_name for keyword in ['payment', 'billing', 'transaction']):
            impact['severity'] = 'Critical'
            impact['description'] = 'Direct revenue impact - payment processing failure stops all sales'
            impact['financial_exposure'] = 'Complete revenue loss during outage'
        
        # Customer-facing components
        elif any(keyword in component_name for keyword in ['customer', 'user', 'account']):
            impact['severity'] = 'High'
            impact['description'] = 'Customer experience impact - affects user satisfaction and retention'
            impact['financial_exposure'] = 'Customer churn and reputation damage'
        
        # Inventory/catalog components
        elif any(keyword in component_name for keyword in ['inventory', 'catalog', 'product']):
            impact['severity'] = 'High'
            impact['description'] = 'Operations impact - inability to manage products affects sales'
            impact['financial_exposure'] = 'Lost sales opportunities'
        
        return impact
    
    def _convert_findings_to_threats(
        self,
        findings: List[Dict[str, Any]],
        business_metrics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Convert business findings to threat format."""
        threats = []
        
        for finding in findings:
            threat = {
                'Threat Category': 'Business Risk',
                'Threat Name': f"Business Risk: {finding['type']}",
                'Description': finding.get('business_impact', ''),
                'Potential Impact': finding['severity'],
                'Likelihood': 'Medium',
                'Suggested Mitigation': finding.get('recommendation', ''),
                'component_name': finding.get('component', 'Business Operations'),
                'component_type': 'business',
                'agent_source': self.name,
                'analysis_type': 'business_impact',
                'financial_exposure': finding.get('financial_exposure', 'Unknown'),
                'business_metrics': business_metrics
            }
            threats.append(threat)
        
        return threats


class ComplianceGovernanceAgent(BaseAnalyzerAgent):
    """
    Compliance & Governance Agent
    Mission: View system through the lens of an auditor.
    """
    
    def __init__(self):
        super().__init__(
            name="Compliance & Governance Agent",
            focus_area="Regulatory Compliance and Governance"
        )
        
        # Compliance frameworks and requirements
        self.compliance_frameworks = {
            'gdpr': {
                'keywords': ['gdpr', 'general data protection', 'eu privacy'],
                'requirements': [
                    'data encryption at rest and in transit',
                    'right to be forgotten implementation',
                    'data portability features',
                    'consent management',
                    'data breach notification within 72 hours'
                ]
            },
            'pci_dss': {
                'keywords': ['pci', 'pci dss', 'payment card', 'credit card'],
                'requirements': [
                    'network segmentation',
                    'encryption of cardholder data',
                    'access control measures',
                    'regular security testing',
                    'logging and monitoring'
                ]
            },
            'hipaa': {
                'keywords': ['hipaa', 'health insurance portability', 'phi', 'protected health'],
                'requirements': [
                    'encryption requirements',
                    'access controls and audit logs',
                    'data backup and disaster recovery',
                    'business associate agreements',
                    'risk assessments'
                ]
            },
            'sox': {
                'keywords': ['sox', 'sarbanes-oxley', 'sarbox'],
                'requirements': [
                    'internal controls documentation',
                    'audit trail maintenance',
                    'change management processes',
                    'segregation of duties',
                    'data retention policies'
                ]
            },
            'iso27001': {
                'keywords': ['iso 27001', 'iso27001', 'information security management'],
                'requirements': [
                    'risk assessment and treatment',
                    'security policy documentation',
                    'incident management procedures',
                    'business continuity planning',
                    'supplier relationship security'
                ]
            }
        }
        
        # Governance requirements
        self.governance_checks = {
            'audit_logging': ['audit', 'log', 'trail', 'record', 'history'],
            'access_control': ['rbac', 'access control', 'permission', 'authorization'],
            'data_retention': ['retention', 'archive', 'storage policy', 'data lifecycle'],
            'incident_response': ['incident response', 'breach', 'security incident'],
            'change_management': ['change control', 'change management', 'version control'],
            'testing': ['penetration test', 'security test', 'vulnerability scan', 'audit']
        }
    
    async def analyze(
        self,
        document_text: str,
        dfd_components: Dict[str, Any],
        existing_threats: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Analyze for compliance and governance risks."""
        findings = []
        
        # 1. Identify applicable compliance frameworks
        applicable_frameworks = self._identify_compliance_requirements(document_text)
        
        # 2. Check compliance implementation
        findings.extend(self._check_compliance_implementation(
            document_text, dfd_components, applicable_frameworks
        ))
        
        # 3. Analyze governance controls
        findings.extend(self._analyze_governance_controls(document_text, dfd_components))
        
        # 4. Check data handling compliance
        findings.extend(self._check_data_handling_compliance(dfd_components, applicable_frameworks))
        
        # 5. Assess audit readiness
        findings.extend(self._assess_audit_readiness(document_text, dfd_components))
        
        # Convert to threats
        threats = self._convert_findings_to_threats(findings, applicable_frameworks)
        
        return threats
    
    def _identify_compliance_requirements(self, document_text: str) -> List[str]:
        """Identify which compliance frameworks apply."""
        applicable = []
        document_lower = document_text.lower()
        
        for framework, info in self.compliance_frameworks.items():
            for keyword in info['keywords']:
                if keyword in document_lower:
                    applicable.append(framework)
                    logger.info(f"Compliance Agent identified {framework.upper()} requirements")
                    break
        
        return applicable
    
    def _check_compliance_implementation(
        self,
        document_text: str,
        dfd_components: Dict[str, Any],
        frameworks: List[str]
    ) -> List[Dict[str, Any]]:
        """Check if compliance requirements are implemented."""
        findings = []
        document_lower = document_text.lower()
        
        for framework in frameworks:
            requirements = self.compliance_frameworks[framework]['requirements']
            missing_requirements = []
            
            for requirement in requirements:
                # Simple check if requirement keywords are mentioned
                requirement_keywords = requirement.lower().split()
                found = any(keyword in document_lower for keyword in requirement_keywords[:3])
                
                if not found:
                    missing_requirements.append(requirement)
            
            if missing_requirements:
                findings.append({
                    'type': f'{framework.upper()} Compliance Gap',
                    'severity': 'High' if framework in ['pci_dss', 'hipaa'] else 'Medium',
                    'finding': f'Missing {len(missing_requirements)} {framework.upper()} requirements',
                    'missing_requirements': missing_requirements[:3],  # Top 3
                    'recommendation': f'Implement missing {framework.upper()} controls to achieve compliance'
                })
        
        return findings
    
    def _analyze_governance_controls(
        self,
        document_text: str,
        dfd_components: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Analyze governance control implementation."""
        findings = []
        document_lower = document_text.lower()
        
        missing_controls = []
        
        for control_type, keywords in self.governance_checks.items():
            found = any(keyword in document_lower for keyword in keywords)
            
            if not found:
                missing_controls.append(control_type)
        
        if missing_controls:
            severity = 'High' if 'audit_logging' in missing_controls else 'Medium'
            
            findings.append({
                'type': 'Governance Control Gap',
                'severity': severity,
                'finding': f'Missing governance controls: {", ".join(missing_controls)}',
                'recommendation': 'Implement comprehensive governance controls for audit readiness'
            })
        
        # Check for logging on sensitive data stores
        data_stores = dfd_components.get('data_stores', [])
        for store in data_stores:
            store_name = store.get('name', '').lower() if isinstance(store, dict) else str(store).lower()
            
            if any(keyword in store_name for keyword in ['user', 'customer', 'payment', 'personal']):
                # This is sensitive data - check if logging is mentioned
                if 'audit' not in document_lower and 'log' not in document_lower:
                    findings.append({
                        'type': 'Audit Trail Missing',
                        'severity': 'High',
                        'component': store_name,
                        'finding': f'No audit logging detected for sensitive data store: {store_name}',
                        'recommendation': 'Implement comprehensive audit logging for all data access'
                    })
        
        return findings
    
    def _check_data_handling_compliance(
        self,
        dfd_components: Dict[str, Any],
        frameworks: List[str]
    ) -> List[Dict[str, Any]]:
        """Check data handling for compliance issues."""
        findings = []
        
        # GDPR specific checks
        if 'gdpr' in frameworks:
            # Check for personal data handling
            data_stores = dfd_components.get('data_stores', [])
            personal_data_stores = [
                d for d in data_stores
                if any(keyword in (d.get('name', '').lower() if isinstance(d, dict) else str(d).lower())
                      for keyword in ['user', 'customer', 'personal', 'profile'])
            ]
            
            if personal_data_stores:
                findings.append({
                    'type': 'GDPR Data Protection',
                    'severity': 'High',
                    'finding': f'Personal data detected in {len(personal_data_stores)} stores - GDPR compliance required',
                    'recommendation': 'Implement GDPR requirements: encryption, consent, right to deletion, data portability'
                })
        
        # PCI DSS specific checks
        if 'pci_dss' in frameworks:
            # Check for payment data handling
            payment_components = []
            for comp_type in ['processes', 'data_stores', 'data_flows']:
                components = dfd_components.get(comp_type, [])
                for comp in components:
                    comp_name = comp.get('name', '').lower() if isinstance(comp, dict) else str(comp).lower()
                    if any(keyword in comp_name for keyword in ['payment', 'card', 'credit', 'billing']):
                        payment_components.append(comp_name)
            
            if payment_components:
                findings.append({
                    'type': 'PCI DSS Compliance',
                    'severity': 'Critical',
                    'finding': f'Payment processing detected in {len(payment_components)} components',
                    'recommendation': 'Ensure PCI DSS compliance: network segmentation, encryption, tokenization'
                })
        
        return findings
    
    def _assess_audit_readiness(
        self,
        document_text: str,
        dfd_components: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Assess system's audit readiness."""
        findings = []
        document_lower = document_text.lower()
        
        # Key audit requirements
        audit_requirements = {
            'logging': ['log', 'audit', 'trail'],
            'monitoring': ['monitor', 'alert', 'siem'],
            'documentation': ['document', 'policy', 'procedure'],
            'testing': ['test', 'scan', 'assessment'],
            'retention': ['retention', 'archive', 'backup']
        }
        
        missing_capabilities = []
        
        for capability, keywords in audit_requirements.items():
            found = any(keyword in document_lower for keyword in keywords)
            if not found:
                missing_capabilities.append(capability)
        
        if len(missing_capabilities) >= 3:
            findings.append({
                'type': 'Audit Readiness',
                'severity': 'High',
                'finding': 'System lacks audit readiness - missing key capabilities',
                'missing_capabilities': missing_capabilities,
                'recommendation': 'Implement comprehensive audit program with logging, monitoring, and regular testing'
            })
        
        # Check for DR testing
        if 'disaster recovery' in document_lower or 'dr' in document_lower:
            if 'test' not in document_lower and 'exercise' not in document_lower:
                findings.append({
                    'type': 'Untested DR Plan',
                    'severity': 'High',
                    'finding': 'Disaster Recovery plan exists but testing not mentioned',
                    'recommendation': 'Implement regular DR testing with documented results'
                })
        
        return findings
    
    def _convert_findings_to_threats(
        self,
        findings: List[Dict[str, Any]],
        frameworks: List[str]
    ) -> List[Dict[str, Any]]:
        """Convert compliance findings to threat format."""
        threats = []
        
        for finding in findings:
            threat = {
                'Threat Category': 'Compliance Risk',
                'Threat Name': f"Compliance Risk: {finding['type']}",
                'Description': finding['finding'],
                'Potential Impact': finding['severity'],
                'Likelihood': 'High' if frameworks else 'Medium',
                'Suggested Mitigation': finding['recommendation'],
                'component_name': finding.get('component', 'Governance & Compliance'),
                'component_type': 'compliance',
                'agent_source': self.name,
                'analysis_type': 'compliance_audit',
                'applicable_frameworks': frameworks,
                'missing_requirements': finding.get('missing_requirements', []),
                'missing_capabilities': finding.get('missing_capabilities', [])
            }
            threats.append(threat)
        
        return threats


class MultiAgentOrchestrator:
    """
    Orchestrates multiple analyzer agents to provide comprehensive threat analysis.
    """
    
    def __init__(self):
        self.agents = [
            ArchitecturalRiskAgent(),
            BusinessFinancialRiskAgent(),
            ComplianceGovernanceAgent()
        ]
        logger.info(f"Multi-Agent Orchestrator initialized with {len(self.agents)} agents")
    
    async def analyze_system(
        self,
        document_text: str,
        dfd_components: Dict[str, Any],
        existing_threats: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run all agents and consolidate findings.
        
        Args:
            document_text: Original system documentation
            dfd_components: Extracted DFD components
            existing_threats: Threats from traditional analysis
            
        Returns:
            Consolidated multi-perspective threat analysis
        """
        if existing_threats is None:
            existing_threats = []
        
        all_findings = {
            'architectural_risks': [],
            'business_risks': [],
            'compliance_risks': [],
            'consolidated_threats': [],
            'summary': {}
        }
        
        # Run all agents concurrently for faster execution
        import asyncio
        
        logger.info(f"Running {len(self.agents)} agents concurrently...")
        start_time = asyncio.get_event_loop().time()
        
        # Create concurrent tasks for all agents
        agent_tasks = []
        for agent in self.agents:
            task = agent.analyze(document_text, dfd_components, existing_threats)
            agent_tasks.append((agent, task))
        
        # Execute all agents concurrently
        try:
            results = await asyncio.gather(*[task for agent, task in agent_tasks], return_exceptions=True)
            
            # Process results and categorize findings
            for (agent, _), result in zip(agent_tasks, results):
                if isinstance(result, Exception):
                    logger.error(f"{agent.name} failed: {result}")
                    continue
                
                logger.info(f"{agent.name} completed successfully")
                agent_threats = result
                
                # Categorize findings
                if isinstance(agent, ArchitecturalRiskAgent):
                    all_findings['architectural_risks'] = agent_threats
                elif isinstance(agent, BusinessFinancialRiskAgent):
                    all_findings['business_risks'] = agent_threats
                elif isinstance(agent, ComplianceGovernanceAgent):
                    all_findings['compliance_risks'] = agent_threats
                
                all_findings['consolidated_threats'].extend(agent_threats)
                
            execution_time = asyncio.get_event_loop().time() - start_time
            logger.info(f"All agents completed in {execution_time:.1f}s (concurrent execution)")
                
        except Exception as e:
            logger.error(f"Critical error in multi-agent execution: {e}")
            # Continue with partial results if some agents succeeded
        
        # Generate summary statistics
        all_findings['summary'] = {
            'total_threats': len(all_findings['consolidated_threats']),
            'architectural_risks': len(all_findings['architectural_risks']),
            'business_risks': len(all_findings['business_risks']),
            'compliance_risks': len(all_findings['compliance_risks']),
            'agents_executed': len(self.agents),
            'analysis_timestamp': datetime.utcnow().isoformat()
        }
        
        # Prioritize threats
        all_findings['consolidated_threats'] = self._prioritize_threats(
            all_findings['consolidated_threats']
        )
        
        return all_findings
    
    def _prioritize_threats(self, threats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize threats based on severity and type."""
        severity_order = {'Critical': 4, 'High': 3, 'Medium': 2, 'Low': 1}
        
        # Sort by severity and agent type
        threats.sort(
            key=lambda t: (
                severity_order.get(t.get('Potential Impact', 'Medium'), 2),
                t.get('agent_source', '')
            ),
            reverse=True
        )
        
        # Add priority ranking
        for idx, threat in enumerate(threats):
            threat['multi_agent_priority'] = idx + 1
        
        return threats