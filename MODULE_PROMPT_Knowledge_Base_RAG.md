User: Excellent. Now let's analyze the Knowledge Base & RAG module.

Here is the relevant code from the following files: apps/api/app/api/endpoints/knowledge_base.py, apps/api/app/services/ingestion_service.py, apps/api/app/tasks/knowledge_base_tasks.py, apps/api/app/models/knowledge_base.py

Python

// --- Start of apps/api/app/api/endpoints/knowledge_base.py ---
{{CODE:apps/api/app/api/endpoints/knowledge_base.py}}
// --- End of apps/api/app/api/endpoints/knowledge_base.py ---

// --- Start of apps/api/app/services/ingestion_service.py ---
{{CODE:apps/api/app/services/ingestion_service.py}}
// --- End of apps/api/app/services/ingestion_service.py ---

// --- Start of apps/api/app/tasks/knowledge_base_tasks.py ---
{{CODE:apps/api/app/tasks/knowledge_base_tasks.py}}
// --- End of apps/api/app/tasks/knowledge_base_tasks.py ---

// --- Start of apps/api/app/models/knowledge_base.py ---
{{CODE:apps/api/app/models/knowledge_base.py}}
// --- End of apps/api/app/models/knowledge_base.py ---


Your Task: Analyze this code and list the specific user-facing or API-level functionalities it provides. Be precise. For example: "Queue ingestion of external sources (e.g., CISA KEV)", "Search knowledge base (semantic/hybrid)", "Get KB stats", "Initialize default sources", "Delete entries by source", "Background ingestion tasks (general & CWE)", "Periodic update task", "Dual storage (pgvector/SQLite) models".


