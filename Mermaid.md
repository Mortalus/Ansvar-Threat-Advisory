```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#2b2b2b', 'primaryTextColor': '#f5f5f5', 'lineColor': '#a9a9a9', 'fontSize': '14px'}}}%%
graph TD
    subgraph user_interaction ["User Interaction"]
        User([fa:fa-user User])
        Frontend[Next.js Frontend]
    end

    subgraph app_backend ["Application Backend (Docker Network)"]
        FastAPI[fa:fa-server FastAPI Backend]
        CeleryWorker[fa:fa-cogs Celery Worker]
        CeleryBeat["fa:fa-clock Celery Beat<br/>(Scheduler)"]
    end

    subgraph data_layer ["Data & State Layer (Docker Network)"]
        PostgreSQL[("fa:fa-database PostgreSQL")]
        Redis[("fa:fa-database Redis<br/>Celery Broker")]
    end
    
    subgraph db_components ["New DB Tables & Extensions"]
        style PostgreSQL fill:#224057,stroke:#fff
        pgvector{pgvector Extension}
        KnowledgeBase["KnowledgeBase Table<br/>(Embeddings)"]
        Prompts["Prompts Table<br/>(Versioned)"]
        Feedback[ThreatFeedback Table]
    end

    subgraph external_services ["External Services"]
        LLM_Provider["LLM Provider<br/>(Scaleway, Azure, Ollama)"]
        MITRE["fa:fa-shield-alt MITRE / CISA<br/>Knowledge Base Source"]
    end

    %% Styles for New/Modified Components
    style KnowledgeBase fill:#d4edda,stroke:#155724,stroke-width:2px
    style Prompts fill:#d4edda,stroke:#155724,stroke-width:2px
    style Feedback fill:#d4edda,stroke:#155724,stroke-width:2px
    style CeleryBeat fill:#d1ecf1,stroke:#0c5460,stroke-width:2px

    %% Main User Flows
    User -->|Interacts via Browser| Frontend
    Frontend -- "1. Uploads Docs &<br/>Triggers Pipeline" --> FastAPI
    FastAPI -->|"2. Creates Pipeline in DB"| PostgreSQL
    FastAPI -->|"3. Queues Task"| Redis
    Frontend -- "Submits Threat Review<br/>(Feedback Loop)" --> FastAPI
    FastAPI -->|"Records Feedback"| Feedback
    
    %% Celery Worker - RAG Threat Generation Flow
    CeleryWorker -- "4. Pulls Threat Gen Task" --> Redis
    CeleryWorker -- "5. Forms Query from<br/>DFD Component" --> CeleryWorker
    CeleryWorker -->|"6. Fetches Active Prompt"| Prompts
    CeleryWorker -->|"7. Performs Vector Search"| KnowledgeBase
    KnowledgeBase -->|"Returns Relevant Context"| CeleryWorker
    CeleryWorker -- "8. Augments Prompt &<br/>Calls LLM" --> LLM_Provider
    LLM_Provider -->|"Returns Generated Threats"| CeleryWorker
    CeleryWorker -- "9. Saves Results &<br/>Metadata (Prompt/Model Version)" --> PostgreSQL
    CeleryWorker -->|"10. Sends Real-time Update"| FastAPI
    FastAPI -.->|"WebSocket Push"| Frontend

    %% Data Ingestion Flow (Scheduled)
    CeleryBeat -->|"A. Triggers Ingestion Task"| Redis
    CeleryWorker -- "B. Pulls Ingestion Task" --> Redis
    CeleryWorker -->|"C. Fetches Latest Data"| MITRE
    CeleryWorker -->|"D. Creates Embeddings"| CeleryWorker
    CeleryWorker -->|"E. Stores in Vector DB"| KnowledgeBase

    %% Database Relationships
    PostgreSQL --- pgvector
    pgvector --- KnowledgeBase
    PostgreSQL --- Prompts
    PostgreSQL --- Feedback
    ```