# AtmoGraph — Core Architecture & Working Deep Dive
## (Ekdum Desi Bhasha Mein, Chhote Bachhe Ko Samjhane Jaisa Master Guide)

---

## 🌟 1. AtmoGraph Asal Mein Hai Kya? (The Real-World Story)

### 👶 Bachho Jaisi Kahani:
Socho tumhare mohalle mein ek bohot famous bakery hai jo chocolate pastry banati hai. 
Ek din pastry banne ke liye:
1. Dudh aata hai ek gaon ke dairy farm se.
2. Chocolate aati hai Switzerland se jahaz (ship) ke zariye.
3. Bakery ki oven chalne ke liye bijli aati hai local power plant se.

Ab socho ek din achanak news aayi: **"Suez Canal mein jahaz phans gaya!"** 🚢💥
Aam insaan sochega: *"Mujhe kya, main toh bakery me baitha hu."*
Lekin bakery ka malik tension me aa jayega kyunki:
- Jahaz phansa ➔ Chocolate nahi aayi.
- Chocolate nahi aayi ➔ Pastry nahi banegi.
- Pastry nahi banegi ➔ Customers gussa honge aur dukan ka nuksan hoga!

Isi ko bolte hain **"Domino Effect"** ya **"Ripple Effect"** (paani me pathar maro toh lehre door tak failti hain). Aur poore network ko bolte hain **Supply Chain**.

### ⚡ AtmoGraph Kya Karta Hai?
**AtmoGraph ek Super-Smart AI Watchman aur Doctor hai.**
Ye internet par 24 ghante chalne wali news padhta hai (jaise port strike, toofan, factory me aag), turant samajhta hai ki kahan kya gadbad hui, aapke supply chain ke poore nakshe (graph) me dhundhta hai ki kaunsa supplier khatre me hai, aur pehle hi bata deta hai:
> *"Bhai! 7 din baad tumhare factory me raw material khatam hone wala hai, production ruk jayega! Dusre supplier se baat kar lo!"*

---

## 🏛️ 2. Poore Project Ke 4 Bade Khambhe (4 Core Pillars)

AtmoGraph chaar bade hisson (pillars) se milkar bana hai:

```
┌────────────────────────────────────────────────────────────────────────┐
│                          ATMOGRAPH SYSTEM                              │
├───────────────────┬───────────────────┬────────────────────────────────┤
│ 1. Kaan & Aankhein│ 2. Yaad-daasht    │ 3. Dimag & Calculator          │ 4. Chehra (UI)   │
│ (Data Ingestion & │ (Databases)       │ (AI + Graph + Simulation)      │ (Frontend)       │
│  NLP)             │                   │                                │                  │
│                   │ • SQLite (Tables) │ • spaCy (NLP Understanding)    │ • React 19       │
│ • Google News RSS │ • Neo4j (Graph/   │ • PyTorch Geometric (GNN 60%)  │ • TypeScript     │
│ • Live Scraper    │   Relationships)  │ • Rule Engine (Math 40%)       │ • Vite           │
│                   │                   │ • Disruption Simulator         │ • React Flow     │
│                   │                   │   (Net Shortage, Plant Stop)   │ • Recharts       │
└───────────────────┴───────────────────┴────────────────────────────────┴──────────────────┘
```

---

## 🧰 3. Kis Technology, Tool aur Library Ka Kya Kaam Hai?

Yahan har us tool aur library ki list hai jo is project me use hui hai, aur unka aam bhasha me matlab:

| Technology / Library | Kahan Use Hui | Kis File Me | Aam Bhasha Me Kya Kaam Hai? |
| :--- | :--- | :--- | :--- |
| **Python 3.11/3.12** | Backend & ML | `backend/**`, `ml/**` | Poore backend aur machine learning ka main engine. |
| **FastAPI** | Backend Web API | `backend/app/main.py`, `backend/app/api/**` | Super-fast Python web framework jo frontend ke requests leta hai aur data wapas deta hai. |
| **Uvicorn** | ASGI Server | `main:app` | FastAPI ke code ko live port (8000) par chalane wala motor. |
| **Neo4j** | Graph Database | Docker Container (`bolt://localhost:7687`) | Aam database tables me data rakhta hai; Neo4j **rishtey (connections)** store karta hai (jaise Facebook friends graph). |
| **neo4j (Python Driver)**| Backend DB Bridge | `app/services/neo4j_service.py` | Python code se Neo4j me Cypher queries chalane ka tarika. |
| **SQLAlchemy** | SQL ORM | `app/core/database.py`, `app/models/**` | Python code ko SQLite database se jodta hai taaki raw SQL na likhna pade. |
| **Pydantic v2** | Data Validation | `app/schemas/**` | Police guard ki tarah input check karta hai ki koi galat data format na bhej de. |
| **spaCy (`en_core_web_sm`)** | NLP (Text Brain) | `app/services/nlp_engine.py` | English news articles padh kar pata lagata hai: Desh/City kaunsi hai (GPE), Company kaunsi hai (ORG). |
| **PyTorch & PyG** | Graph Neural Network | `app/services/gnn_model.py`, `train_gnn.py` | AI model jo Neo4j graph ke nodes ke beech me risk travel karne ka pattern predict karta hai. |
| **openpyxl & pandas** | Excel Importer | `app/services/supply_chain/excel_importer.py` | User ki `.xlsx` files ko read karta hai (Suppliers, Products, Inventory, Routes). |
| **WebSockets** | Real-time alerts | `app/services/websocket_manager.py` | Jab bhi nayi news aaye, bina page reload kiye screen par live popup dikhata hai. |
| **React 19 & Vite** | Frontend Framework | `frontend/src/**` | Modern, super-fast visual website banane ke liye. |
| **TypeScript** | Frontend Language | `frontend/src/**/*.tsx`, `.ts` | JavaScript me types ka rules lagata hai taaki bugs na aayein. |
| **React Flow (@xyflow/react)**| Graph Visualizer | `frontend/src/components/dashboard/SupplyGraph.tsx` | Screen par nodes aur connecting arrows (lines) ko drag-and-drop animated graph me dikhata hai. |
| **Recharts** | Analytics Charts | `frontend/src/pages/DashboardOverview.tsx` | Sundar bar charts, line graphs aur risk meters draw karta hai. |
| **Lucide React** | Icons Library | `frontend/src/**` | Dashboard ke icons (truck, warning, radar, building, etc.). |

---

## 📂 4. File-by-File & Folder-by-Folder In-Depth Tour

Chalo ab project ke har ek folder aur har zaroori file ke andar ghus kar dekhte hain ki usme kya likha hai aur kyun!

```
atmograph/
├── backend/          ← Python Server (FastAPI + Business Logic + AI)
├── frontend/         ← React UI (Jo screen par dikhta hai)
├── ml/               ← Machine Learning experiment scripts aur model definitions
├── neo4j/            ← Neo4j Cypher queries aur constraints
├── data/             ← Excel files aur templates
├── docs/             ← Project ki documentation
├── docker-compose.yml← Neo4j database container chalane ke liye
└── README.md         ← Main project guide
```

---

## 🐍 4.1. BACKEND DEEP DIVE (`backend/app/`)

### 1️⃣ Core Setup (`backend/app/core/`)
* **`config.py`**: Ye file `.env` file se saari zaroori settings (Database URL, Neo4j password, Secret Keys, Ports) padhti hai `pydantic-settings` use karke.
* **`database.py`**: SQLite database ka connection (`engine` aur `SessionLocal`) banati hai.
* **`init_db.py`**: Jab project pehli baar run hota hai, ye script SQLite ke andar saare tables (`users`, `events`, `business_suppliers`, etc.) create karti hai.
* **`seed.py`**: Pehli baar run karne par sample company data aur sample events database me daal deti hai taaki dashboard khali na lage.

---

### 2️⃣ Database Models (`backend/app/models/`)
Ye files batati hain ki database ke tables ka dhyan kaisa hoga:

* **`user.py`**:
  * Users ka table (`users`). Isme `email`, `hashed_password`, aur sabse zaroori `company_name` hota hai. Is se multi-tenancy chalti hai.
* **`business_supply_chain.py`**:
  * Asli enterprise supply chain ka daldal yahan map hota hai:
    - `BusinessSupplier`: Supplier ka naam, city, country, reliability score.
    - `BusinessProduct`: Finished product jo company banati hai.
    - `Component`: Raw material (jaise kapda, perfume bottle, microchip).
    - `Plant`: Company ki factory jahan cheezein banti hain.
    - `Inventory`: Factory me kitna spare raw material bacha hai.
    - `SupplyAllocation`: Kaunsa supplier kitna component deliver karta hai aur uske paas kitni spare capacity hai.
    - `Dependency`: Ek product banane me kitna component chahiye.
* **`event.py`**:
  * News events ka table (`events`). Isme event ka title, news text, location, event_type (`port_strike`, `storm`, etc.), severity, aur company_id hoti hai.
* **`supply_chain_link.py`**:
  * Event aur supplier ke beech ka link record karta hai.

---

### 3️⃣ Services Layer — The Real Magic (`backend/app/services/`)
Ye backend ka sabse bada aur sabse important hissa hai. Yahan actual dimag kaam karta hai:

#### A. `nlp_engine.py` (News Samajhne Ka Engine)
* **Library:** `spaCy` (`en_core_web_sm`)
* **Kaise Kaam Karta Hai:**
  1. News aayi: *"Major flood in Surat textile hub stops fabric delivery to Mohilya Couture."*
  2. spaCy text ko todta hai (tokenization).
  3. Named Entity Recognition (NER) chalata hai:
     - `Surat` ➔ **GPE** (Location/Geographic Entity)
     - `Mohilya Couture` ➔ **ORG** (Organization)
  4. Keyword pattern matching se detect karta hai:
     - Keywords like *"flood", "heavy rain"* ➔ Event Type = `natural_disaster`
     - Severity detection: *"major", "halted", "destroyed"* ➔ Severity = `critical`

#### B. `live_news_monitor.py` & `news_ingestion_service.py` (Live Watchman)
* Background me asynchronous worker (async loop) chalta hai.
* Har thodi der me Google News RSS feed se supply chain aur disruptions ki latest khabrein lata hai.
* Purani news ke sath match karke duplicate khabron ko discard karta hai.
* Nayi news ko turant `IntelligencePipeline` ke hawale kar deta hai.

#### C. `intelligence_pipeline.py` (The Central Nervous System)
* Ye AtmoGraph ka dil hai. Ye saare services ko ek line me khada karke kaam karwata hai:
  1. News ko parse karo.
  2. NLP chala ke location aur organization nikalo.
  3. `location_resolution_service.py` se check karo ki news kis city ya port ki hai.
  4. Company ke suppliers se match karo: *"Kya hamara koi supplier Surat me baitha hai?"*
  5. SQLite me Event record create karo.
  6. Neo4j me Graph node aur relationship banao.
  7. Hybrid Prediction aur Disruption Simulation run karo.
  8. Output WebSocket par broadcast karo!

#### D. `neo4j_service.py` & `entity_graph_builder.py` (Rishtey Banane Wala)
* **Database:** Neo4j (Cypher Language)
* Nodes banata hai: `(Event)`, `(Supplier)`, `(Plant)`, `(Component)`, `(Product)`.
* Relationships banata hai:
  - `(Event)-[:AFFECTS]->(Supplier)`
  - `(Supplier)-[:SUPPLIES]->(Component)`
  - `(Component)-[:REQUIRED_FOR]->(Product)`
  - `(Product)-[:MANUFACTURED_AT]->(Plant)`
* Cypher Query example jo ye execute karta hai:
  ```cypher
  MATCH (e:Event {id: $event_id})-[:AFFECTS]->(s:Supplier)-[:SUPPLIES]->(c:Component)
  RETURN s.name, c.name
  ```

#### E. `hybrid_prediction_service.py` (AI Risk Predictor)
* Ye service 2 alag-alag techniques ka mixture (hybrid) use karti hai:
  $$\text{Final Risk Score} = (0.40 \times \text{Rule Score}) + (0.60 \times \text{GNN Score})$$
* **Kyun aisa kiya?**
  - Sirf Rule-based mathematics graph ki gehraai (topology) nahi dekh sakti.
  - Sirf Machine Learning (GNN) kabhi-kabhi hallucinate ya black-box ban sakti hai.
  - Dono ko milane se **100% reliable aur accurate** prediction aati hai!
* Agar Neo4j kisi vajah se band ho, toh gracefully fallback karke 100% rule-based mode par switch ho jata hai (server crash nahi hota!).

#### F. `gnn_model.py` & `gnn_prediction_service.py` (Graph Neural Network)
* **Framework:** PyTorch & PyTorch Geometric (`torch-geometric`).
* Graph ke nodes ko numbers (vectors / node embeddings) me badalta hai.
* Graph Convolutional Network (GCN) layer use karta hai. Message Passing ke zariye ek node ka khatra uske padosi node me propagate hota hai.

#### G. `disruption_simulator.py` (Business Loss Calculator)
* Machine learning risk score ek number deti hai (e.g., 78/100), lekin businessman ko samajh nahi aata ki 78 ka matlab kitne rupaye ka nuksan hai.
* Ye simulator **exact business calculation** karta hai:
  - Supplier fail hua toh kitne units material ruk gaya?
  - Kya koi alternative supplier available hai jiske paas spare capacity hai?
  - Factory ke godown (Inventory buffer) me kitna maal bacha hai?
  - Kitne din tak factory bina raw material ke chal sakti hai?
  - **Net Shortage** kitna hai aur kya **Production Halt (Factory Band)** hoga ya nahi?

#### H. `historical_intelligence_service.py`
* Purane disruptions aur past events ko cluster (group) karta hai.
* Timeline banata hai taaki user dekh sake: *"Surat me pichle saal jab baadh aayi thi, tab hamari factory kitne din band hui thi?"*

#### I. `websocket_manager.py` (Live Broadcasting Station)
* FastAPI ke WebSocket protocol par kaam karta hai.
* Jaise hi koi naya incident detect hota hai ya simulation complete hoti hai, ye message bhejta hai `{"type": "EVENT_CREATED", "data": ...}`.
* Frontend bina refresh kiye turant red-alert flashing sound aur cards update kar deta hai.

---

### 4️⃣ API Endpoints Layer (`backend/app/api/routes/`)

Ye routes frontend ke liye darwaze (APIs) hain:
* **`auth.py`**: Login, Register (`/api/auth/register`, `/api/auth/login`), JWT access token generation, current company profile.
* **`supply_chain.py`**: Excel file upload karna, sample templates download karna, supplier details lena, simulation run karna (`/api/supply-chain/simulate`).
* **`news.py` & `news_intelligence.py`**: Live news feed lena, custom news analyze karwana, RSS scanner start/stop karna.
* **`graph.py`**: Neo4j se poora visual network fetch karna (`nodes` aur `edges`).
* **`predictions.py`**: Hybrid prediction run karna.
* **`historical_intelligence.py`**: Purane incidents ka cluster aur timeline timeline view dena.
* **`websocket.py`**: WebSocket connection endpoint (`/ws/updates`).

---

## ⚛️ 5. FRONTEND DEEP DIVE (`frontend/src/`)

Frontend ek modern single-page web app hai jo React 19, TypeScript, aur Vite par bani hai.

```
frontend/src/
├── components/          ← UI ke chhote aur reusable pieces
│   ├── dashboard/
│   │   └── SupplyGraph.tsx       ← Interactive Node Graph (React Flow)
│   ├── GlobalSearch.tsx          ← Poore system me search bar
│   ├── HistoricalIntelligence.tsx← Past incidents replay aur timeline
│   ├── PredictionIntelligence.tsx← GNN + Rule prediction card
│   ├── RippleAnalysis.tsx        ← Ripple cascade view
│   ├── Settings.tsx              ← Configurations
│   └── WorkspaceModal.tsx        ← Company switch karne ka popup
├── context/
│   └── AuthContext.tsx           ← Login state aur User session
├── pages/
│   ├── AuthPage.tsx              ← Login aur Register screen
│   ├── DashboardOverview.tsx     ← Main Command Center (Overview Tab)
│   ├── IncidentRadarPage.tsx     ← Live News & Disruption Radar (Radar Tab)
│   ├── SupplyNetworkPage.tsx     ← Interactive Network View (Network Tab)
│   ├── SystemStatusPage.tsx      ← Server, DB, Neo4j Health Check
│   └── supply-chain/
│       ├── ExcelDataImport.tsx   ← Excel upload aur datasets load karna
│       └── SupplyChainSimulator.tsx ← Interactive What-If Simulator
├── services/
│   ├── api.ts                    ← Backend REST endpoints ka fetch wrapper
│   ├── supplyChainApi.ts         ← Supply chain related API calls
│   └── websocket.ts              ← Live WebSocket client listener
├── App.tsx                       ← Main App Shell, Header, Sidebar, Routing
└── index.css                     ← High-tech dark mode styling & animations
```

### 🖥️ 7 Main Screens (Tabs) Jo User Ko Dikhti Hain:

1. **Overview Tab (`DashboardOverview.tsx`):**
   - High-level KPIs: Total Suppliers, Active Disruptions, High Risk Nodes, Stock Buffer.
   - Quick alerts aur recent news feed ticker.
2. **Catalog / Import Tab (`ExcelDataImport.tsx`):**
   - User yahan apni company ki Excel file drag-and-drop upload kar sakta hai.
   - Built-in ready-made sample datasets ko 1-click me load kar sakta hai (`Mohilya Couture`, `AdilQadri Perfumes`, `Bonkers Corner`).
3. **Network Tab (`SupplyNetworkPage.tsx` + `SupplyGraph.tsx`):**
   - Sabse visual feature! **React Flow** library ka use karke live interactive node-graph dikhta hai.
   - Nodes: Blue (Suppliers), Green (Components), Purple (Products), Orange (Plants), Red (Disrupted Event).
   - Aap nodes ko haath se drag kar sakte ho, zoom in/out kar sakte ho, aur click karke details dekh sakte ho.
4. **Simulator Tab (`SupplyChainSimulator.tsx`):**
   - What-if Analysis: User khud select karta hai: *"Agar XYZ Supplier 80% fail ho jaye, toh kya hoga?"*
   - System turant calculate karke shortage graph aur alternative supplier recommendation dikhata hai.
5. **Radar Tab (`IncidentRadarPage.tsx`):**
   - Live News Radar. Yahan world map style cards aate hain, background monitor ka status dikhta hai, aur naye aane wale incidents par auto-simulation chalti hai.
6. **History Tab (`HistoricalIntelligence.tsx`):**
   - Purane events ka comparison aur incident clusters.
7. **Status Tab (`SystemStatusPage.tsx`):**
   - Live system health: FastAPI (Green), Neo4j (Green), SQLite (Green), spaCy NLP (Loaded).

---

## 🔄 6. Poora Data Flow: Ek News Aane Se Screen Par Red Alert Tak!

Chalo step-by-step dekhte hain ki jab duniya me koi ghatna ghati hai, toh code ke andar millisecond-by-millisecond kya hota hai:

```
[ STEP 1: RSS FEED / NEWS ]
Google News RSS feed me news aayi: 
"Chemical plant fire in Vapi disrupts synthetic dye supplies for Gujarat apparel makers."
       │
       ▼
[ STEP 2: LIVE MONITOR ]
backend/app/services/live_news_monitor.py
RSS reader ne XML parse kiya, nayi khabar pakdi aur deduplicate kiya.
       │
       ▼
[ STEP 3: INTELLIGENCE PIPELINE & NLP ]
backend/app/services/intelligence_pipeline.py
nlp_engine.py (spaCy) ne article padha:
  - Location nikali: "Vapi", "Gujarat"
  - Event Type nikala: "fire_hazard" / "factory_shutdown"
  - Severity: "high"
       │
       ▼
[ STEP 4: DATABASE & ENTITY RESOLUTION ]
location_resolution_service.py aur database_importer:
  - Database me dekha: Company "Mohilya Couture" ka ek chemical supplier "Vapi Dye Works" Vapi me hai!
  - MATCH CONFIRMED (Confidence: 94%)
       │
       ▼
[ STEP 5: NEO4J GRAPH SYNC ]
backend/app/services/neo4j_service.py
Neo4j me Cypher query run hui:
  CREATE (e:Event {title: "Chemical plant fire in Vapi"})
  MATCH (s:BusinessSupplier {supplier_id: "SUP_VAPI"})
  CREATE (e)-[:AFFECTS {severity: "high"}]->(s)
       │
       ▼
[ STEP 6: HYBRID PREDICTION ]
backend/app/services/hybrid_prediction_service.py
  - Rule-based score calculate hua: 72/100
  - GNN (PyTorch Geometric) ne topological ripple calculate kiya: 79/100
  - Final Hybrid Risk Score = (72 * 0.4) + (79 * 0.6) = 76.2 (CRITICAL RISK)
       │
       ▼
[ STEP 7: DISRUPTION SIMULATION ]
backend/app/services/supply_chain/disruption_simulator.py
  - Synthetic dye ka normal stock factory me: 500 Liters
  - Daily consumption: 100 Liters/day
  - Vapi factory recovery time: 14 Days
  - Buffer days available: 5 Days
  - Net Shortage: 900 Liters!
  - RESULT: PRODUCTION WILL HALT IN 5 DAYS!
       │
       ▼
[ STEP 8: WEBSOCKET PUSH ]
backend/app/services/websocket_manager.py
JSON payload frontend ke open socket connection par gaya:
{"type": "INCIDENT_DETECTED", "event_id": 102, "risk_score": 76.2, "halt": true}
       │
       ▼
[ STEP 9: REACT FRONTEND RENDERING ]
frontend/src/pages/IncidentRadarPage.tsx & SupplyGraph.tsx
  - Screen par notification pop up hua!
  - SupplyGraph me "Vapi Dye Works" ka node glowing RED ho gaya!
  - Alternative supplier suggestion automatically screen par show ho gaya!
```

---

## 🏢 7. Multi-Tenant Architecture (Alag-Alag Companies Ka Data Isolation)

AtmoGraph me **Multi-Tenancy** built-in hai:
* Ek hi server par chahe 10 alag-alag companies register ho jayein, **Company A ka supplier ya secret inventory data Company B ko kabhi nahi dikhta.**
* Kaise ensure hota hai?
  1. Har table (`events`, `business_suppliers`, `business_products`, etc.) me `user_id` ya `company_name` column hota hai.
  2. Har API request me user ka JWT token pass hota hai.
  3. FastAPI ka database query filter hamesha lagta hai:
     ```python
     query = db.query(BusinessSupplier).filter(BusinessSupplier.user_id == current_user.id)
     ```
  4. Pre-configured demo datasets:
     - **Mohilya Couture**: Surat textile & apparel dataset.
     - **AdilQadri Perfumes**: Attar, essential oils, fragrance glass bottles dataset.
     - **Bonkers Corner**: Streetwear fashion multi-city apparel supply chain.

---

## 🎓 8. Quick Revision / Viva Cheat Sheet (Interview / Presentation Ke Liye)

Agar koi aapse pooche:

1. **"AtmoGraph kya hai?"**
   > *"AtmoGraph ek AI-driven supply chain resilience platform hai jo live news ko NLP aur Graph Neural Networks se analyze karke multi-tier supply chain disruptions aur factory stoppages ko pehle se predict karta hai."*

2. **"Neo4j kyun use kiya, normal SQL se kaam kyun nahi chalaya?"**
   > *"Kyunki supply chains multi-tier hoti hain (Supplier ka Supplier, uska Component, uski Plant). SQL me multiple nested JOINs lagane se database slow ho jata hai aur ripple-effect path dhundhna mushkil hota hai. Neo4j graph relationships ko first-class citizen maanta hai, jisse multi-hop traversal millisecond me ho jati hai."*

3. **"GNN aur Rule Engine dono kyun rakhe hain (Hybrid Model)?"**
   > *"GNN poore graph structure aur network connectivity ka probability score deta hai (60%), jabki deterministic rule-engine exact business logic aur constraints check karta hai (40%). Dono milkar false alarms ko kam karte hain aur highest accuracy dete hain."*

4. **"Simulator kya karta hai?"**
   > *"Simulator ye calculate karta hai ki ek supplier fail hone par factory godown ka buffer inventory kab khatam hoga, alternative supplier kitna recover kar payega, aur factory band hone me kitne din bache hain."*

---

*Document finalized & integrated into AtmoGraph Architecture Documentation.*
