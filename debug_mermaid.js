// Debug Mermaid generation
const dfdData = {
  "project_name": "E-Commerce Security Platform",
  "project_version": "2.1",
  "industry_context": "E-commerce & Security",
  "external_entities": [
    "Customer",
    "Admin", 
    "Payment Gateway",
    "Shipping Provider",
    "Security Auditor"
  ],
  "assets": [
    "User DB",
    "Product DB",
    "Order DB", 
    "Session Cache",
    "Security Logs"
  ],
  "processes": [
    "Web Server",
    "API Gateway",
    "Auth Service",
    "Payment Service",
    "Security Monitor"
  ],
  "trust_boundaries": [
    "Public Zone",
    "DMZ",
    "Internal Network", 
    "Secure Zone"
  ],
  "data_flows": [
    {
      "source": "Customer",
      "destination": "Web Server",
      "data_description": "HTTPS requests",
      "data_classification": "Public",
      "protocol": "HTTPS",
      "authentication_mechanism": "None"
    },
    {
      "source": "Web Server",
      "destination": "API Gateway",
      "data_description": "API calls",
      "data_classification": "Internal",
      "protocol": "HTTPS",
      "authentication_mechanism": "JWT"
    },
    {
      "source": "API Gateway",
      "destination": "Auth Service",
      "data_description": "Auth requests",
      "data_classification": "Confidential",
      "protocol": "TLS",
      "authentication_mechanism": "OAuth2"
    },
    {
      "source": "Auth Service",
      "destination": "User DB",
      "data_description": "User data",
      "data_classification": "PII",
      "protocol": "TLS", 
      "authentication_mechanism": "DB Auth"
    },
    {
      "source": "Payment Service",
      "destination": "Payment Gateway",
      "data_description": "Payment data",
      "data_classification": "Confidential",
      "protocol": "HTTPS",
      "authentication_mechanism": "API Key"
    }
  ]
};

// Generate Mermaid diagram
let diagram = 'graph TB\n';

if (dfdData.project_name) {
  diagram += `    %% Project: ${dfdData.project_name} v${dfdData.project_version || '1.0'}\n`;
  diagram += `    %% Industry: ${dfdData.industry_context || 'Unknown'}\n\n`;
}

// Define external entities with square brackets
if (dfdData.external_entities?.length) {
  diagram += '    %% External Entities\n';
  dfdData.external_entities.forEach((entity, idx) => {
    const id = `EE${idx}`;
    const sanitized = entity.replace(/[^a-zA-Z0-9\s]/g, '').substring(0, 20);
    diagram += `    ${id}["${sanitized}"]\n`;
    diagram += `    style ${id} fill:#ff6b6b,stroke:#c92a2a,color:#fff\n`;
  });
  diagram += '\n';
}

// Define processes with rounded rectangles
if (dfdData.processes?.length) {
  diagram += '    %% Processes\n';
  dfdData.processes.forEach((process, idx) => {
    const id = `P${idx}`;
    const sanitized = process.replace(/[^a-zA-Z0-9\s]/g, '').substring(0, 20);
    diagram += `    ${id}("${sanitized}")\n`;
    diagram += `    style ${id} fill:#4c6ef5,stroke:#364fc7,color:#fff\n`;
  });
  diagram += '\n';
}

// Define assets/data stores with cylinders
if (dfdData.assets?.length) {
  diagram += '    %% Data Stores/Assets\n';
  dfdData.assets.forEach((asset, idx) => {
    const id = `DS${idx}`;
    const sanitized = asset.replace(/[^a-zA-Z0-9\s]/g, '').substring(0, 20);
    diagram += `    ${id}[("${sanitized}")]\n`;
    diagram += `    style ${id} fill:#37b24d,stroke:#2b8a3e,color:#fff\n`;
  });
  diagram += '\n';
}

// Define trust boundaries as subgraphs
if (dfdData.trust_boundaries?.length) {
  diagram += '    %% Trust Boundaries (as comments)\n';
  dfdData.trust_boundaries.forEach((boundary, idx) => {
    diagram += `    %% Trust Boundary: ${boundary}\n`;
  });
  diagram += '\n';
}

// Add data flows
if (dfdData.data_flows?.length) {
  diagram += '    %% Data Flows\n';
  dfdData.data_flows.forEach((flow, idx) => {
    const sourceIdx = dfdData.external_entities?.indexOf(flow.source) ?? -1;
    const destIdx = dfdData.external_entities?.indexOf(flow.destination) ?? -1;
    const sourceProcessIdx = dfdData.processes?.indexOf(flow.source) ?? -1;
    const destProcessIdx = dfdData.processes?.indexOf(flow.destination) ?? -1;
    const sourceAssetIdx = dfdData.assets?.indexOf(flow.source) ?? -1;
    const destAssetIdx = dfdData.assets?.indexOf(flow.destination) ?? -1;
    
    let sourceId = null;
    let destId = null;
    
    // Find source ID
    if (sourceIdx !== -1) sourceId = `EE${sourceIdx}`;
    else if (sourceProcessIdx !== -1) sourceId = `P${sourceProcessIdx}`;
    else if (sourceAssetIdx !== -1) sourceId = `DS${sourceAssetIdx}`;
    
    // Find destination ID
    if (destIdx !== -1) destId = `EE${destIdx}`;
    else if (destProcessIdx !== -1) destId = `P${destProcessIdx}`;
    else if (destAssetIdx !== -1) destId = `DS${destAssetIdx}`;
    
    console.log(`Flow: ${flow.source} -> ${flow.destination}`);
    console.log(`  Source: ${sourceId} (EE: ${sourceIdx}, P: ${sourceProcessIdx}, DS: ${sourceAssetIdx})`);
    console.log(`  Dest: ${destId} (EE: ${destIdx}, P: ${destProcessIdx}, DS: ${destAssetIdx})`);
    
    if (sourceId && destId) {
      const label = `${flow.protocol || 'Unknown'}`;
      diagram += `    ${sourceId} -->|"${label}"| ${destId}\n`;
    } else {
      console.log(`  WARNING: Could not find IDs for flow`);
    }
  });
}

console.log('\n=== GENERATED MERMAID DIAGRAM ===');
console.log(diagram);
console.log('=== END DIAGRAM ===\n');