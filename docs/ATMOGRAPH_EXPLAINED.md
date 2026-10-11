# AtmoGraph — The Ultimate Master Guide 🌐⚡
## (Poora Project Ekdum Seedha, Aasan Desi Bhasha Mein Samjho)

> **Ek hi file mein poore project ka 360-degree gyaan:**  
> Core working, har file ka role, har library aur technology ka explanation, data flow, multi-tenancy, aur viva/interview questions!

---

# 📑 TABLE OF CONTENTS
1. [Ye Project Hai Kya Bhai? (The Real-World Story)](#-1-ye-project-hai-kya-bhai-the-real-world-story)
2. [Project Ke 4 Bade Khambhe (4 Core Pillars)](#-2-project-ke-4-bade-khambhe-4-core-pillars)
3. [Technologies, Tools aur Libraries Ki Complete List](#-3-technologies-tools-aur-libraries-ki-complete-list)
4. [A-to-Z Data Flow: Ek News Aane Se Screen Par Red Alert Tak](#-4-a-to-z-data-flow-ek-news-aane-se-screen-par-red-alert-tak)
5. [In-Depth File-by-File & Folder Tour](#-5-in-depth-file-by-file--folder-tour)
   - 5.1 [Backend: Core & Config](#51-backend-core--config)
   - 5.2 [Backend: Database Models (SQL Tables)](#52-backend-database-models-sql-tables)
   - 5.3 [Backend: Services (The Real Brains)](#53-backend-services-the-real-brains)
   - 5.4 [Backend: API Routes (The Doorways)](#54-backend-api-routes-the-doorways)
   - 5.5 [Frontend: Pages & Components (The Beautiful Face)](#55-frontend-pages--components-the-beautiful-face)
   - 5.6 [Neo4j Graph Database (Schema & Queries)](#56-neo4j-graph-database-schema--queries)
   - 5.7 [Data & Excel Templates](#57-data--excel-templates)
6. [Multi-Tenant System (Har Company Ka Alag Data)](#-6-multi-tenant-system-har-company-ka-alag-data)
7. [Viva, Interview & Presentation Cheat Sheet](#-7-viva-interview--presentation-cheat-sheet)
8. [Project Run Kaise Karein? (Quick Start)](#-8-project-run-kaise-karein-quick-start)

---

# 🌟 1. Ye Project Hai Kya Bhai? (The Real-World Story)

### 👶 Bachho Jaisi Kahani:
Socho tumhare mohalle mein ek bohot famous bakery hai jo premium chocolate cake banati hai:
1. **Doodh** aata hai gaon ke dairy farm se.
2. **Cocoa & Chocolate** aati hai Switzerland se cargo ship ke zariye.
3. **Flour (Maida)** aata hai Punjab ke wheat mills se.
4. **Oven ki bijli** aati hai local power plant se.

Ab socho ek din TV par breaking news aayi: **"Suez Canal mein jahaz phans gaya, shipping route block!"** 🚢💥  
Aam insaan sochega: *"Humein kya, hum toh bakery me baith kar chai pi rahe hain!"*  
Lekin bakery ka maalik tension mein aa jayega, kyunki:
* Jahaz phansa ➔ Switzerland se chocolate delivery ruk gayi.
* Chocolate nahi aayi ➔ Cake banna band ho gaya.
* Cake banna band hua ➔ Customers gussa, orders cancel, aur company ka karodo ka nuksan!

Isi ko bolte hain **"Domino Effect"** ya **"Ripple Effect"** (paani mein pathar maro toh lehren door-door tak failti hain). Aur is aane-jaane ke poore network ko bolte hain **Supply Chain**.

### ⚡ AtmoGraph Asal Mein Kya Karta Hai?
**AtmoGraph ek 24x7 jaagne wala Super-Smart AI Watchman aur Doctor hai.**
Ye internet par duniya bhar ki live news padhta hai (jaise port strike, toofan, flood, factory me aag), turant samajhta hai ki kahan kya ghatna ghati, aapke supply chain ke nakshe (Graph) mein dhundhta hai ki kaunsa supplier khatre mein hai, aur 7 din pehle hi alert bhej deta hai:
> *"Bhai! 7 din baad tumhari factory mein raw material khatam hone wala hai, backup supplier se baat kar lo!"*

---

# 🏛️ 2. Project Ke 4 Bade Khambhe (4 Core Pillars)

AtmoGraph 4 main parts se milkar bana hai:

```
┌────────────────────────────────────────────────────────────────────────┐
│                          ATMOGRAPH SYSTEM                              │
├───────────────────┬───────────────────┬────────────────────────────────┤
│ 1. Kaan & Aankhein│ 2. Yaad-daasht    │ 3. Dimag & Calculator          │ 4. Chehra (UI)   │
│ (News & NLP)      │ (Databases)       │ (AI + Graph + Simulation)      │ (Frontend)       │
│                   │                   │                                │                  │
│ • Google News RSS │ • SQLite (Tables) │ • spaCy (NLP Understanding)    │ • React 19       │
│ • Live Scraper    │ • Neo4j (Graph/   │ • PyTorch Geometric (GNN 60%)  │ • TypeScript     │
│                   │   Relationships)  │ • Rule Engine (Math 40%)       │ • Vite           │
│                   │                   │ • Disruption Simulator         │ • React Flow     │
│                   │                   │   (Net Shortage, Plant Halt)   │ • Recharts       │
└───────────────────┴───────────────────┴────────────────────────────────┴──────────────────┘
```

1. **Kaan & Aankhein (Data Ingestion & NLP):** Internet se news articles pakadna aur English text ko samajhna.
2. **Yaad-daasht (Databases):** 
   - **SQLite:** Aam tables ke liye (User accounts, logs, static properties).
   - **Neo4j:** Graph database — kaunsa supplier kis factory se juda hai, kaunsa route kahan jata hai (Connections & Relationships).
3. **Dimag & Calculator (Hybrid AI + Simulation Engine):**
   - **GNN (Graph Neural Network):** 60% weightage — graph topology dekh kar risk travel hone ka pattern predict karta hai.
   - **Rule Engine:** 40% weightage — strict mathematical logic.
   - **Disruption Simulator:** Calculate karta hai ki godown ka buffer inventory kab khatam hoga aur factory band hogi ya nahi.
4. **Chehra (React UI):** Beautiful dark-mode dashboard jahan interactive graph, live radar, aur simulation screen dikhti hai.

---

# 🧰 3. Technologies, Tools aur Libraries Ki Complete List

| Technology / Library | Kahan Use Hui | Kis File Me | Aam Bhasha Me Kya Kaam Hai? |
| :--- | :--- | :--- | :--- |
| **Python 3.11/3.12** | Backend & ML | `backend/**`, `ml/**` | Backend API aur AI models ki main programming bhasha. |
| **FastAPI** | REST API Server | `backend/app/main.py` | Super-fast Python web framework jo frontend se data mangwata aur bhejta hai. |
| **Uvicorn** | Server Runner | `main:app` | FastAPI ke code ko live port `8000` par chalane wala motor. |
| **Neo4j** | Graph Database | Docker (`bolt://localhost:7687`)| Normal tables ke bajaye **rishton ka jaal (Graph)** store karta hai. |
| **neo4j (Python Driver)** | DB Connector | `app/services/neo4j_service.py` | Python code se Neo4j me Cypher queries chalata hai. |
| **SQLAlchemy** | SQL ORM | `app/core/database.py`, `models/**`| Python code ko SQLite database se jodta hai bina lambi SQL queries likhe. |
| **Pydantic v2** | Data Validation | `app/schemas/**` | Police guard ki tarah input check karta hai ki koi galat data format na bhej de. |
| **spaCy (`en_core_web_sm`)**| NLP Engine | `app/services/nlp_engine.py` | News padh kar shehar (GPE) aur company (ORG) ke naam alag karta hai. |
| **PyTorch & PyTorch Geometric**| Graph AI (GNN) | `app/services/gnn_model.py` | Graph par risk failne ka machine learning prediction karta hai. |
| **openpyxl & pandas** | Excel Importer | `app/services/supply_chain/excel_importer.py` | User ki `.xlsx` files ko read karke database me load karta hai. |
| **WebSockets** | Real-Time Push | `app/services/websocket_manager.py` | Nayi news aate hi bina page reload kiye screen par live popup dikhata hai. |
| **React 19 & Vite** | Frontend Framework | `frontend/src/**` | Modern, fast visual dashboard banane ke liye. |
| **TypeScript** | Frontend Language | `frontend/src/**/*.tsx`, `.ts` | Strict types wala JavaScript taaki bugs na banein. |
| **React Flow (@xyflow/react)**| Interactive Graph | `frontend/src/components/dashboard/SupplyGraph.tsx` | Screen par nodes aur arrows ko drag-and-drop format me dikhata hai. |
| **Recharts** | Analytics Charts | `frontend/src/pages/DashboardOverview.tsx` | Colorful bar charts, graphs aur risk meters draw karta hai. |
| **Lucide React** | Icons Library | `frontend/src/**` | Dashboard ke icons (truck, warning, radar, building, etc.). |
| **bcrypt & python-jose** | Auth & Security | `app/services/auth_service.py` | Passwords ko encrypt (hash) karna aur JWT access tokens generate karna. |

---

# 🔄 4. A-to-Z Data Flow: Ek News Aane Se Screen Par Red Alert Tak

Chalo dekhte hain ki jab duniya me koi ghatna ghati hai, toh code ke andar step-by-step kya hota hai:

```
[ STEP 1: RSS FEED SE NEWS AAYI ]
Google News RSS feed me khabar aayi: 
"Chemical plant fire in Vapi disrupts synthetic dye supplies for Gujarat apparel makers."
       │
       ▼
[ STEP 2: LIVE MONITOR & DEDUPLICATION ]
backend/app/services/live_news_monitor.py
Background worker ne XML parse kiya, nayi khabar pakdi aur duplicate check kiya.
       │
       ▼
[ STEP 3: NLP ANALYSIS (SPACY) ]
backend/app/services/nlp_engine.py
spaCy English model ne text padha:
  • Location nikali: "Vapi", "Gujarat" (GPE)
  • Event Type: "fire_hazard" / "factory_shutdown"
  • Severity: "high"
       │
       ▼
[ STEP 4: DATABASE & CANONICAL MATCHING ]
backend/app/services/location_resolution_service.py
  • Database me search kiya: Kya hamari company ka koi supplier Vapi me hai?
  • MATCH FOUND: "Vapi Dye Works" (Confidence: 94%)
       │
       ▼
[ STEP 5: NEO4J GRAPH SYNC ]
backend/app/services/neo4j_service.py
Neo4j me Cypher query chali:
  CREATE (e:Event {title: "Chemical plant fire in Vapi"})
  MATCH (s:BusinessSupplier {supplier_id: "SUP_VAPI"})
  CREATE (e)-[:AFFECTS {severity: "high"}]->(s)
       │
       ▼
[ STEP 6: HYBRID PREDICTION ENGINE ]
backend/app/services/hybrid_prediction_service.py
  • Rule-based score: 72 / 100
  • GNN (PyTorch Geometric) topology score: 79 / 100
  • Final Score = (72 * 0.40) + (79 * 0.60) = 76.2 (CRITICAL RISK)
       │
       ▼
[ STEP 7: DISRUPTION SIMULATOR (BUSINESS MATH) ]
backend/app/services/supply_chain/disruption_simulator.py
  • Synthetic dye ka godown stock: 500 Liters
  • Factory daily usage: 100 Liters/day
  • Buffer stock chalega: 5 Days
  • Supplier recovery time: 14 Days
  • Net Shortage: 900 Liters!
  • NUKSAAN: PRODUCTION HALT IN 5 DAYS!
       │
       ▼
[ STEP 8: WEBSOCKET BROADCAST ]
backend/app/services/websocket_manager.py
JSON message frontend par gaya:
{"type": "INCIDENT_DETECTED", "event_id": 102, "risk_score": 76.2, "halt": true}
       │
       ▼
[ STEP 9: REACT FRONTEND RENDERING ]
frontend/src/pages/IncidentRadarPage.tsx & SupplyGraph.tsx
  • Screen par live alert flashing notification aayi!
  • SupplyGraph me "Vapi Dye Works" ka node glowing RED ho gaya!
  • System ne alternative supplier suggestion display kar diya!
```

---

# 📂 5. In-Depth File-by-File & Folder Tour

---

### 5.1 Backend: Core & Config (`backend/app/core/`)

* **`config.py`**:
  * `.env` file se settings (Database URL, Neo4j Bolt URL, Secret Key, Token Expire time) load karta hai.
* **`database.py`**:
  * SQLite database ka connection (`engine`) aur `SessionLocal` banata hai.
* **`init_db.py`**:
  * SQLite ke andar saare tables (`users`, `events`, `business_suppliers`, etc.) create karta hai.
* **`seed.py`**:
  * Pehli baar run karne par default seed data load karta hai taaki dashboard shuru me khali na lage.

---

### 5.2 Backend: Database Models (SQL Tables) (`backend/app/models/`)

* **`user.py`**:
  * `User` model: `id`, `email`, `hashed_password`, `company_name`. Multi-tenancy ka foundation yahi se shuru hota hai.
* **`business_supply_chain.py`**:
  * Enterprise supply chain ka poora table schema:
    - `BusinessSupplier`: Supplier name, city, country, reliability score.
    - `BusinessProduct`: Finished goods jo company bechti hai.
    - `Component`: Raw material (jaise kapda, attar bottle, microchip).
    - `Plant`: Company ki manufacturing factory.
    - `Inventory`: Godown me kitna component stock bacha hai.
    - `SupplyAllocation`: Kaunsa supplier kitna material deliver karta hai aur uske paas kitni spare capacity hai.
    - `Demand`: Factory ki daily raw material demand.
    - `Dependency`: Ek product banane me kitne units component lagte hain.
* **`event.py`**:
  * News events table: `title`, `description`, `location`, `event_type`, `severity`, `status`.
* **`supply_chain_link.py`**:
  * Event aur affected supplier ke beech mapping table.

---

### 5.3 Backend: Services (The Real Brains) (`backend/app/services/`)

* **`nlp_engine.py`**:
  * `spaCy` ke sath English Named Entity Recognition (NER) chalata hai. Shehar (`GPE`), desh, aur company (`ORG`) pehchanta hai.
* **`news_ingestion_service.py` & `live_news_monitor.py`**:
  * Background mein Google News RSS feed check karta hai aur nayi khabron ko deduplicate karke parse karta hai.
* **`intelligence_pipeline.py`**:
  * Saare components ka master conductor. News aane par NLP ➔ Database ➔ Neo4j ➔ AI Prediction ➔ Business Simulation ko ek line me chalata hai.
* **`location_resolution_service.py`**:
  * News mein aayi location (jaise "Surat" ya "Rotterdam") ko database ke suppliers ke shehar se match karta hai.
* **`neo4j_service.py`**:
  * Neo4j se connect karke Cypher queries run karta hai (`Event ➔ AFFECTS ➔ Supplier ➔ SUPPLIES ➔ Component`).
* **`gnn_model.py` & `gnn_prediction_service.py`**:
  * PyTorch Geometric GNN model (`torch-geometric`). Graph ke nodes ko vector embeddings me convert karke ripple effect propagate karta hai.
* **`hybrid_prediction_service.py`**:
  * **Rule Engine (40%) + GNN (60%)** ko jod kar final risk score calculate karta hai. Agar Neo4j offline ho, toh gracefully rule-based mode par fallback karta hai.
* **`supply_chain/disruption_simulator.py`**:
  * Businessman ke kaam ki calculations karta hai:
    - Spare capacity check
    - Godown buffer inventory days calculation
    - Net shortage
    - Factory halt status
* **`supply_chain/excel_importer.py` & `database_importer.py`**:
  * User ki uploaded `.xlsx` file ki 8 sheets padhta hai aur SQLite database mein insert karta hai.
* **`supply_chain/neo4j_business_importer.py`**:
  * Excel ke business data ko Neo4j graph database mein graph nodes aur edges ke roop mein sync karta hai.
* **`historical_intelligence_service.py`**:
  * Purane events ko cluster karta hai taaki user dekh sake ki pichle saal jab strike hui thi tab kya asar pada tha.
* **`unified_intelligence_service.py`**:
  * Backend ke saare alag-alag metrics ko ek clean JSON contract mein pack karke frontend ko deta hai.
* **`websocket_manager.py`**:
  * Active frontend browser connections ko manage karta hai aur live alerts broadcast karta hai.

---

### 5.4 Backend: API Routes (The Doorways) (`backend/app/api/routes/`)

* **`auth.py`**: Login, Register (`/api/auth/register`, `/api/auth/login`), JWT tokens.
* **`supply_chain.py`**: Excel upload, catalog get karna, simulation run karna (`/api/supply-chain/simulate`).
* **`news.py` & `news_intelligence.py`**: Live news feed, manual news analysis endpoint.
* **`graph.py`**: Frontend graph ke liye nodes aur edges return karta hai.
* **`predictions.py`**: Event ID leke hybrid prediction result deta hai.
* **`historical_intelligence.py`**: Event clusters aur past incident replay endpoints.
* **`websocket.py`**: Real-time WebSocket connection endpoint (`/ws/updates`).

---

### 5.5 Frontend: Pages & Components (The Beautiful Face) (`frontend/src/`)

Frontend **React 19**, **TypeScript**, aur **Vite** par bana ek high-tech dark-mode dashboard hai:

* **`App.tsx`**: Main shell — Header, Sidebar navigation, Multi-tenant workspace switcher.
* **`pages/DashboardOverview.tsx` (Overview Tab)**:
  * Command Center — Total Suppliers, Active Disruptions, Stock Health, Live Activity Feed ticker.
* **`pages/supply-chain/ExcelDataImport.tsx` (Catalog Tab)**:
  * Excel file upload karna, sample templates download karna, aur 1-click me ready-made datasets load karna.
* **`components/dashboard/SupplyGraph.tsx` & `pages/SupplyNetworkPage.tsx` (Network Tab)**:
  * **React Flow (@xyflow/react)** ka interactive visual canvas:
    - 🔵 Blue Node = Supplier
    - 🟢 Green Node = Component
    - 🟣 Purple Node = Product
    - 🟠 Orange Node = Factory Plant
    - 🔴 Red Glowing Node = Disrupted Node
    - Nodes ko drag kar sakte ho, zoom kar sakte ho, aur click karke details dekh sakte ho.
* **`pages/supply-chain/SupplyChainSimulator.tsx` (Simulator Tab)**:
  * What-if sandbox — user kisi bhi supplier ko select karke slider se failure percentage set kar sakta hai aur live impact dekh sakta hai.
* **`pages/IncidentRadarPage.tsx` (Radar Tab)**:
  * World News Radar — Google News se aayi khabrein, scan button, filter by severity, aur auto-simulation playback.
* **`components/HistoricalIntelligence.tsx` (History Tab)**:
  * Purane incidents ki timeline aur cluster analysis.
* **`pages/SystemStatusPage.tsx` (Status Tab)**:
  * Health diagnostic screen: FastAPI, Neo4j, SQLite, aur spaCy model ka live status.
* **`context/AuthContext.tsx`**:
  * Login state, JWT token storage, current user session handle karta hai.

---

### 5.6 Neo4j Graph Database (Schema & Queries) (`neo4j/`)

* **`neo4j/schema/constraints.cypher`**: Duplicate nodes rokne ke liye unique ID constraints lagata hai.
* **`neo4j/schema/indexes.cypher`**: Name aur title par fast indexes banata hai.
* **`neo4j/queries/graph_queries.cypher`**: Multi-hop path traversal queries:
  ```cypher
  MATCH (e:Event {event_id: $id})-[:AFFECTS]->(s:Supplier)-[:SUPPLIES]->(c:Component)
  RETURN s.name, c.name;
  ```

---

### 5.7 Data & Excel Templates (`data/templates/`)

Project mein user ki testing ke liye ready-made real-world datasets hain:
* **`Mohilya_Couture_SupplyChain.xlsx`**: Surat Textile & Designer Apparel supply chain (Fabric, Zari, Dyes, Buttons).
* **`AdilQadri_Attar_SupplyChain.xlsx`**: Perfumes & Attar multi-tier supply chain (Oud, Essential Oils, Glass Bottles, Sprayers).
* **`BonkersCorner_SupplyChain.xlsx`**: Streetwear fashion multi-city supply chain.
* **`supply_chain_template.xlsx`**: Blank template jise download karke koi bhi company apna data fill kar sakti hai.

---

# 🏢 6. Multi-Tenant System (Har Company Ka Alag Data)

AtmoGraph me **Multi-Tenancy** built-in hai:
* Ek hi server par agar 5 alag-alag companies register hain (jaise Mohilya Couture aur AdilQadri), toh **Company A ka koi bhi supplier ya secret godown data Company B ko kabhi nahi dikhega.**
* Ye kaise kaam karta hai?
  1. Har database table mein `user_id` ya `company_name` column hota hai.
  2. Har request mein user ka secure JWT access token verify hota hai.
  3. Database query hamesha isolated filter ke sath chalti hai:
     ```python
     db.query(BusinessSupplier).filter(BusinessSupplier.user_id == current_user.id)
     ```
  4. Header mein **WorkspaceModal** se user easily workspaces ke beech switch kar sakta hai.

---

# 🎓 7. Viva, Interview & Presentation Cheat Sheet

Agar examiner, interviewer ya professor aapse sawaal poochein, toh ye direct answers dein:

### Q1: "AtmoGraph project ka core purpose kya hai?"
> **Answer:** *"AtmoGraph ek AI-powered supply chain resilience platform hai jo live global news ko NLP se analyze karta hai, Neo4j graph database aur Graph Neural Networks (GNN) se ripple-effect disruptions predict karta hai, aur business simulation se factory shutdown hone se pehle alerts provide karta hai."*

### Q2: "Normal SQL ke hote hue Neo4j Graph Database kyun use kiya?"
> **Answer:** *"Kyunki supply chain ek multi-tier interconnected network hota hai (Supplier ➔ Tier-2 Supplier ➔ Component ➔ Plant). SQL relational tables mein 4-5 table JOINs lagane par queries slow ho jaati hain aur arbitrary depth path search mushkil hota hai. Neo4j graph database mein relationships first-class citizen hoti hain, jisse multi-hop traversal millisecond mein ho jaati hai."*

### Q3: "Hybrid Prediction Model kya hai aur formula kya hai?"
> **Answer:** *"Hybrid model do signals ko combine karta hai: 40% Rule-based Mathematical score aur 60% Graph Neural Network (GNN) topological score:*
> $$\text{Risk Score} = (0.40 \times \text{Rule Score}) + (0.60 \times \text{GNN Score})$$
> *Rule-based model deterministic stability deta hai aur GNN deep graph propagation patterns capture karta hai."*

### Q4: "Disruption Simulator businessman ko kya value deta hai?"
> **Answer:** *"Machine learning sirf ek percentage score deti hai (jaise 75%), jo businessman ke liye actionable nahi hoti. Disruption Simulator exact business impact nikalta hai: supplier ke rukne par factory ka buffer stock kitne din chalega, alternative supplier ke paas spare capacity hai ya nahi, aur kitne din mein factory band hone wali hai."*

### Q5: "spaCy ka role kya hai?"
> **Answer:** *"spaCy ka `en_core_web_sm` model Named Entity Recognition (NER) ke liye use hota hai. Ye news text se automatically locations (GPE) jaise 'Surat', 'Rotterdam', aur organizations (ORG) pehchan kar database ke suppliers ke sath map karta hai."*

---

# ⚡ 8. Project Run Kaise Karein? (Quick Start)

Roz run karne ke 3 simple steps:

1. **Neo4j Database (Docker):**
   ```bash
   docker compose up -d
   ```
2. **Backend API Server (Terminal 1):**
   ```bash
   cd backend
   .\.venv\Scripts\activate
   uvicorn app.main:app --reload --port 8000
   ```
3. **Frontend React App (Terminal 2):**
   ```bash
   cd frontend
   npm run dev
   # Browser opens at http://localhost:5173
   ```

---

*Document Author: AtmoGraph Core Engineering Team*  
*Architecture Status: Fully Integrated & Verified*
