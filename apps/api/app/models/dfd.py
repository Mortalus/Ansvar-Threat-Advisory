from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class DataClassification(str, Enum):
    """Data classification levels"""
    CONFIDENTIAL = "Confidential"
    PII = "PII"
    PUBLIC = "Public"
    INTERNAL = "Internal"
    RESTRICTED = "Restricted"

class DataFlow(BaseModel):
    """Represents a single data flow between components"""
    source: str = Field(description="Source component of the data flow.")
    destination: str = Field(description="Destination component of the data flow.")
    data_description: str = Field(description="Description of data being transferred.")
    data_classification: str = Field(description="Classification like 'Confidential', 'PII', or 'Public'.")
    protocol: str = Field(description="Protocol used (e.g., 'HTTPS', 'TLS', 'SSH').")
    authentication_mechanism: str = Field(description="Authentication method (e.g., 'OAuth2', 'API Key', 'Certificate').")

class DFDComponents(BaseModel):
    """Complete DFD components extracted from documents"""
    project_name: str = Field(default='Unknown Project', description="Name of the project or system")
    project_version: str = Field(default='1.0', description="Version of the project")
    industry_context: str = Field(default='Unknown', description="Industry or domain context")
    external_entities: List[str] = Field(default_factory=list, description="External users, systems, or services")
    assets: List[str] = Field(default_factory=list, description="Data stores, databases, and storage systems")
    processes: List[str] = Field(default_factory=list, description="Processing components, services, or functions")
    trust_boundaries: List[str] = Field(default_factory=list, description="Security boundaries in the system")
    data_flows: List[DataFlow] = Field(default_factory=list, description="Data flow connections between components")
    
    class Config:
        json_schema_extra = {
            "example": {
                "project_name": "E-Commerce Platform",
                "project_version": "2.0",
                "industry_context": "Retail",
                "external_entities": ["Customer", "Payment Gateway", "Shipping Provider"],
                "assets": ["User Database", "Product Catalog", "Order History"],
                "processes": ["Authentication Service", "Order Processing", "Inventory Management"],
                "trust_boundaries": ["Internet DMZ", "Internal Network", "Database Zone"],
                "data_flows": [
                    {
                        "source": "Customer",
                        "destination": "Authentication Service",
                        "data_description": "Login credentials",
                        "data_classification": "Confidential",
                        "protocol": "HTTPS",
                        "authentication_mechanism": "OAuth2"
                    }
                ]
            }
        }