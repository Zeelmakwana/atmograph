# AtmoGraph — Poora Project Ekdum Seedha Samjho
## (Desi Style Mein, Ek Chote Bacche Ko Samjhane Jaisa)

---

# SECTION 1 — YE PROJECT HAI KYA BHAI?

Soch ek badi company hai — jaise Samsung ya Tata Motors.
Unka kaam chalane ke liye hazaron cheezein chahiye:
- Kisi factory se parts aate hain
- Kisi port se ship hote hain
- Kisi warehouse mein store hote hain
- Phir assembly line pe lagte hain

Is poore network ko bolte hain **Supply Chain**.

Ab agar koi badi news aaye — jaise:
- "Rotterdam port mein workers ne strike kar di"
- "Shanghai mein typhoon aa gaya"
- "Taiwan mein factory band ho gayi"

Toh kya hoga? Kaun sa supplier affected hoga? Kaun sa product late aayega? Kitne din ki delay hogi?

**AtmoGraph** yahi kaam karta hai — **news padho, AI se samjho, predict karo ki ripple effect kahan kahan jayega.**

Jaise paani mein ek pathar phenko — lehren door door tak jaati hain. Waise hi ek event ki "ripple" poori supply chain mein failti hai.

---

# SECTION 2 — PROJECT KA POORA STRUCTURE

```
atmograph/
├── backend/        ← Python server (FastAPI) — API + Business Logic
├── frontend/       ← React UI — jo browser mein dikhta hai
├── ml/             ← Machine Learning — news samajhna, graph banana
├── neo4j/          ← Graph Database queries
├── data/           ← Excel files (import/export)
└── docs/           ← Documentation
```

Ye 4 bade hisse hain. Har ek alag kaam karta hai.
Milke ek poora system banta hai.

---

# SECTION 3 — ML FOLDER (Machine Learning Brain)

Ye project ka **dimag** hai. Yahan news aati hai aur "samajh" mein aati hai.

---

## 3.1 — ml/ingestion/ (News Ko Andar Laana)

**Kaam:** Bahar se news lo, saaf karo, ek proper "event" banao.

---

### FILE: ml/ingestion/news_parser.py

**Language:** Python
**Kaam:** Raw news title + content leke clean karta hai

```
Input:  title="Strike at Rotterdam port", content="Workers walked out...", source="BBC"
Output: { "title": "Strike at Rotterdam port",
          "content": "Workers walked out...",
          "source": "BBC",
          "ingested_at": "2024-01-15T10:30:00Z" }
```

Ye file sirf **cleaning** karti hai — extra spaces hatao, timestamp lagao, source set karo.

---

### FILE: ml/ingestion/event_builder.py  ← (Teri Active File!)

**Language:** Python
**Kaam:** news_parser + entity_extractor ko milake ek complete event dict banata hai

```python
def build_event(title, content, source):
    news = parse_news(title, content, source)      # Step 1: Clean karo
    entities = extract_event_entities(news["content"])  # Step 2: Naam dhundo
    return {
        "title": news["title"],
        "content": news["content"],
        "source": news["source"],
        "ingested_at": news["ingested_at"],
        "entities": entities,   # ["Rotterdam", "Samsung", "TSMC"]
    }
```

Ye file **do kaam milata hai** — cleaning + entity extraction.

---

### FILE: ml/ingestion/event_ingestor.py

**Language:** Python
**Kaam:** build_event() se bana event database mein save karta hai

Flow:
```
build_event() → event dict → database mein INSERT
```

---

### FILE: ml/ingestion/event_loader.py

**Language:** Python
**Kaam:** Database se events wapas load karta hai (read)

---

### FILE: ml/ingestion/news_ingestion.py

**Language:** Python
**Kaam:** RSS feed se news fetch karta hai (Google News, Reuters, etc.)

---

### FILE: ml/ingestion/run_ingestion.py

**Language:** Python
**Kaam:** Poori ingestion pipeline ek saath chalata hai — ek "runner" script

---

### FILE: ml/ingestion/seed_events.py

**Language:** Python
**Kaam:** Testing ke liye fake/sample events database mein dalta hai

---

## 3.2 — ml/nlp/ (News Ko Samajhna — Natural Language Processing)

**Kaam:** News text padho aur samjho — kaun hai, kya hua, kahan hua.

**Library:** spaCy (ek famous NLP library)
**Model:** en_core_web_sm (English language model)

---

### FILE: ml/nlp/entity_extractor.py

**Language:** Python
**Library:** spaCy

**Kaam:** News text mein se **named entities** dhundta hai

```python
import spacy
nlp = spacy.load("en_core_web_sm")

text = "Strike at Rotterdam port disrupts Samsung supply chain"
doc = nlp(text)

# Output:
# [{"text": "Rotterdam", "label": "GPE"},   ← GPE = Geographic Place
#  {"text": "Samsung",   "label": "ORG"}]   ← ORG = Organization
```

spaCy automatically samajhta hai:
- GPE = Jagah (Rotterdam, Shanghai, India)
- ORG = Company (Samsung, TSMC, Apple)
- PERSON = Insaan ka naam
- DATE = Tarikh

---

### FILE: ml/nlp/event_analyzer.py

**Language:** Python
**Kaam:** Event ka type aur severity detect karta hai

```
"Strike at Rotterdam port" → event_type: "port_strike", severity: "high"
"Minor delay in shipping"  → event_type: "transport_disruption", severity: "low"
```

---

## 3.3 — ml/graph/ (Neo4j Mein Graph Banana)

**Kaam:** Event data leke Neo4j graph database mein nodes aur relationships banao.

**Database:** Neo4j (graph database)
**Language:** Cypher (Neo4j ki query language) + Python

---

### FILE: ml/graph/neo4j_client.py

**Language:** Python
**Library:** neo4j (Python driver)
**Kaam:** Neo4j se connection banata hai, queries chalata hai

```python
from neo4j import GraphDatabase
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
```

---

### FILE: ml/graph/graph_builder.py

**Language:** Python
**Kaam:** Event data leke Neo4j mein graph banata hai

```
Event (Rotterdam Strike)
    ↓ AFFECTS
Location (Rotterdam)

Event (Rotterdam Strike)
    ↓ AFFECTS
Organization (Samsung)
```

Cypher query example:
```cypher
MERGE (e:Event {id: $event_id})
SET e.title = $title

MERGE (l:Location {name: $location})

MERGE (e)-[:AFFECTS]->(l)
```

MERGE matlab — "agar pehle se hai toh update karo, nahi hai toh banao"

---

### FILE: ml/graph/event_graph.py

**Language:** Python
**Kaam:** Ek specific event ka poora graph Neo4j se fetch karta hai

---

### FILE: ml/graph/event_projection.py

**Language:** Python
**Kaam:** Neo4j graph ko GNN ke liye ek "projection" format mein convert karta hai

---

### FILE: ml/graph/sync_events.py

**Language:** Python
**Kaam:** SQLite database ke events ko Neo4j mein sync karta hai

---

## 3.4 — ml/inference/ (Prediction Karna)

**Kaam:** Graph dekh ke risk score calculate karo.

---

### FILE: ml/inference/ripple_predictor.py

**Language:** Python
**Kaam:** Graph projection leke har node ka risk score calculate karta hai

```python
def predict_ripple(projection):
    # Event ki severity dekho
    base_score = _severity_score(event_properties["severity"])

    # Agar disruption type hai toh score badha do
    if event_type in {"port_closure", "strike", "natural_disaster"}:
        base_score += 0.10

    # Har directly connected node ko score do
    for relationship in projection["relationships"]:
        if relationship["type"] == "AFFECTS":
            score = base_score + (0.05 if target_type == "Organization" else 0.0)
            predictions.append({
                "target_id": target["id"],
                "risk_score": round(score, 2),
                "risk_level": "high" if score >= 0.70 else "medium" if score >= 0.40 else "low"
            })
```

Ye abhi **deterministic baseline** hai — matlab rules se kaam karta hai, trained model nahi.
GNN training baad mein hogi.

---

# SECTION 4 — BACKEND FOLDER (FastAPI Server)

Ye **server** hai. React frontend yahan se data maangta hai.
Ye Python mein likha hai, FastAPI framework use karta hai.

**Language:** Python 3.11+
**Framework:** FastAPI
**Database 1:** SQLite (local file — atmograph.db)
**Database 2:** Neo4j (graph database)
**ORM:** SQLAlchemy (Python se database se baat karne ka tool)

---

## 4.1 — backend/app/main.py (Server Ka Darwaza)

**Kaam:** Poora FastAPI server yahan se start hota hai

```python
app = FastAPI(title="AtmoGraph API", version="1.0.0")

# CORS — React (port 5173) ko Python server (port 8000) se baat karne deta hai
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"])

# Saare routes register karo
app.include_router(events_router, prefix="/api")
app.include_router(graph_router, prefix="/api")
app.include_router(predictions_router, prefix="/api")
# ... aur bhi bahut saare

# App start hote hi Live News Monitor chalu karo
@asynccontextmanager
async def lifespan(app):
    live_news_monitor.start()   # ← Background mein RSS check karna shuru
    yield
    await live_news_monitor.stop()  # ← Band karte waqt saaf band karo
```

**CORS kya hai?** — Browser security rule. React localhost:5173 pe hai, API localhost:8000 pe. Browser bolega "alag domain hai, allow nahi." CORS middleware bolega "theek hai, allow hai."

---

## 4.2 — backend/app/core/ (Server Ki Neenv)

---

### FILE: backend/app/core/config.py

**Library:** pydantic-settings
**Kaam:** .env file se settings padhta hai

```python
class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///atmograph.db"
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_PASSWORD: str = ""

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()  # ← Ek baar banao, poore project mein use karo
```

.env file mein real passwords hote hain (git mein nahi jaate).

---

### FILE: backend/app/core/database.py

**Library:** SQLAlchemy
**Kaam:** SQLite database connection banata hai

```python
engine = create_engine("sqlite:///atmograph.db")
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()  # ← Saare models isse inherit karte hain
```

---

### FILE: backend/app/core/neo4j.py

**Kaam:** Neo4j connection check karta hai

```python
def get_neo4j_driver():
    if neo4j_service.driver is None:
        raise RuntimeError("Neo4j not connected!")
    return neo4j_service.driver

def verify_neo4j():
    return neo4j_service.verify_connection()
```

---

### FILE: backend/app/core/init_db.py

**Kaam:** Pehli baar chalane pe database tables banata hai

---

### FILE: backend/app/core/seed.py

**Kaam:** Sample data dalta hai database mein (testing ke liye)

---

## 4.3 — backend/app/models/ (Database Tables)

Ye files SQLAlchemy ORM models hain — matlab Python classes jo database tables represent karti hain.

---

### FILE: backend/app/models/event.py

**Kaam:** `events` table ka structure

```python
class Event(Base):
    __tablename__ = "events"

    id          = Column(Integer, primary_key=True)
    title       = Column(String(255))      # "Strike at Rotterdam port"
    description = Column(Text)             # Full news text
    source      = Column(String(255))      # "BBC", "Reuters"
    event_type  = Column(String(100))      # "port_strike", "factory_shutdown"
    location    = Column(String(255))      # "Rotterdam"
    severity    = Column(String(50))       # "critical", "high", "medium", "low"
    status      = Column(String(50))       # "active", "resolved"
    company_id  = Column(String(100))      # Multi-tenant ke liye
    created_at  = Column(DateTime)
    updated_at  = Column(DateTime)
```

---

### FILE: backend/app/models/supply_chain.py

**Kaam:** `suppliers` aur `products` tables

```python
class Supplier(Base):
    __tablename__ = "suppliers"
    id       = Column(Integer, primary_key=True)
    name     = Column(String)    # "Samsung Electronics"
    country  = Column(String)    # "South Korea"
    industry = Column(String)    # "Electronics"

class Product(Base):
    __tablename__ = "products"
    id          = Column(Integer, primary_key=True)
    name        = Column(String)    # "OLED Display Panel"
    category    = Column(String)    # "Electronics"
    supplier_id = Column(Integer)   # Kaun banata hai ise
```

---

### FILE: backend/app/models/supply_chain_link.py

**Kaam:** Event aur Supplier/Product ke beech ka connection

```python
class SupplyChainLink(Base):
    __tablename__ = "supply_chain_links"
    event_id              = Column(Integer)   # Kaun sa event
    supplier_id           = Column(Integer)   # Kaun sa supplier affected
    product_id            = Column(Integer)   # Kaun sa product affected
    relationship_type     = Column(String)    # "affected"
    impact_level          = Column(String)    # "high"
    estimated_delay_days  = Column(Float)     # 10.0 din
```

---

### FILE: backend/app/models/user.py

**Kaam:** Users table — login/register ke liye

```python
class User(Base):
    __tablename__ = "users"
    id           = Column(Integer, primary_key=True)
    email        = Column(String, unique=True)
    password     = Column(String)    # Hashed (bcrypt)
    company_name = Column(String)
    company_id   = Column(String)    # Multi-tenant isolation
```

---

### FILE: backend/app/models/business_supply_chain.py

**Kaam:** Business-level supply chain data — Excel se import hota hai

```python
class BusinessSupplier(Base):   # User ka actual supplier
class BusinessProduct(Base):    # User ka actual product
class Component(Base):          # Product ke parts
class Plant(Base):              # Manufacturing plant
class Inventory(Base):          # Stock kitna hai
class Demand(Base):             # Demand kitni hai
class Dependency(Base):         # Kaun sa component kaun se product mein lagta hai
class SupplyAllocation(Base):   # Kaun sa supplier kitna supply karta hai
class Company(Base):            # Company info
```

Ye sab Excel se import hote hain — user apna data upload karta hai.


---

# SECTION 5 — SERVICES FOLDER (Asli Kaam Yahan Hota Hai)

Ye folder **project ka engine room** hai. Har service ek specific kaam karti hai.

---

## 5.1 — nlp_engine.py (News Ko Samajhna — Main NLP Brain)

**Language:** Python
**Library:** spaCy (en_core_web_sm model)
**Kaam:** News text se supply chain intelligence nikalna

Ye class 4 kaam karti hai:

### Kaam 1 — Event Type Detect Karo

```python
EVENT_PATTERNS = {
    "port_strike": [r"port\s+strike", r"strike.*port"],
    "port_closure": [r"port\s+(?:closure|closed|shutdown)"],
    "weather_disruption": [r"\bstorm\b", r"\bhurricane\b", r"\bflood\b"],
    "factory_shutdown": [r"factory\s+(?:shutdown|closed)"],
    "supply_chain_disruption": [r"supply\s+chain\s+disruption"],
}
```

Regex patterns se text mein dhundta hai — "port strike" mila? → event_type = "port_strike"

### Kaam 2 — Severity Detect Karo

```python
SEVERITY_TERMS = {
    "critical": ["critical", "severe", "massive"],
    "high":     ["major", "significant", "serious"],
    "medium":   ["moderate", "notable"],
    "low":      ["minor", "limited", "small"],
}
```

### Kaam 3 — Locations Nikalo

```python
KNOWN_LOCATIONS = {
    "rotterdam", "shanghai", "singapore",
    "hamburg", "suez canal", "panama canal", ...
}
```

spaCy se GPE/LOC entities nikalo + domain knowledge se known ports dhundo.

### Kaam 4 — Organizations Nikalo

spaCy se ORG entities nikalo — company names.

**Final output:**
```python
{
    "event_type": "port_strike",
    "severity": "high",
    "locations": ["Rotterdam"],
    "entities": [
        {"text": "Rotterdam", "label": "GPE"},
        {"text": "Samsung",   "label": "ORG"}
    ]
}
```

---

## 5.2 — neo4j_service.py (Graph Database Ka Manager)

**Language:** Python
**Library:** neo4j (Python driver)
**Kaam:** Neo4j se saari baat-cheet yahan hoti hai

### Graph Structure:
```
Event (Rotterdam Strike)
    │
    ├── AFFECTS ──> Supplier (Samsung)
    │                   │
    │                   └── SUPPLIES ──> Product (OLED Panel)
    │
    └── AFFECTS ──> Product (Semiconductor)
```

### Important Methods:

**create_event()** — Neo4j mein Event node banao
```cypher
MERGE (e:Event {event_id: $event_id})
SET e.title = $title, e.severity = $severity
```

**create_supplier()** — Supplier node banao
```cypher
MERGE (s:Supplier {supplier_id: $supplier_id})
SET s.name = $name, s.country = $country
```

**create_event_supplier_relationship()** — Event → Supplier connection banao
```cypher
MATCH (e:Event {event_id: $event_id})
MATCH (s:Supplier {supplier_id: $supplier_id})
MERGE (e)-[r:AFFECTS]->(s)
SET r.impact_level = $impact_level
```

**get_ripple_paths()** — Downstream ripple paths dhundo
```cypher
MATCH path = (e:Event {event_id: $event_id})-[*1..5]->(downstream)
RETURN path
```

**sync_nlp_graph()** — NLP se bane nodes/relationships Neo4j mein sync karo
- NLP temporary IDs ko canonical IDs mein convert karta hai
- Example: "event_global_components_ltd_faces_disruption" → "event_18"

---

## 5.3 — intelligence_pipeline.py (Poora Pipeline — Sabse Important File!)

**Language:** Python
**Kaam:** News se lekar prediction tak ka POORA flow yahan hai

Ye 11 steps mein kaam karta hai:

```
Step 1:  NLP — news analyze karo
Step 2:  SQL Event banao — database mein save karo
Step 3:  Legacy entity matching — purane suppliers/products dhundo
Step 4:  Business supplier matching — user ke uploaded suppliers se match karo
Step 5:  SQL supply chain links banao
Step 6:  Neo4j graph sync karo
Step 7:  Prediction — rule-based + GNN hybrid
Step 8:  Business impact simulation
Step 9:  Aggregate business impact
Step 10: Graph ID assign karo
Step 11: Final response banao
```

### Step 4 — Business Supplier Matching (Sabse Smart Part)

Ye check karta hai ki news mein mentioned company user ke uploaded suppliers mein se koi hai kya.

**Matching Rules:**
- Exact name match → score 100
- Strong NLP entity match → score 95
- Token overlap + location match → score 75-95

**Anti-false-positive rules:**
- Generic words jaise "components", "systems", "global", "india" akele match nahi kar sakte
- Kam se kam 2 meaningful tokens chahiye
- "Global Components Ltd" aur "Global Components Limited" same maane jaate hain

### Step 7 — Hybrid Prediction

```
Rule-based score × 0.40
+
GNN score × 0.60
= Final hybrid risk score
```

---

## 5.4 — prediction_engine.py (Rule-Based Prediction)

**Language:** Python
**Kaam:** Event ki severity + affected suppliers/products dekh ke risk score calculate karo

```python
severity_score = {
    "critical": 100,
    "high": 80,
    "medium": 60,
    "low": 30,
}.get(event.severity, 50)

supplier_factor = min(len(suppliers) * 5, 20)
product_factor  = min(len(products) * 5, 20)

risk_score = (severity_score * 0.6 + supplier_factor + product_factor) * status_multiplier
```

**Risk levels:**
- 75+ → critical
- 50-74 → high
- 30-49 → medium
- 0-29 → low

---

## 5.5 — gnn_model.py (Graph Neural Network — AI Model)

**Language:** Python
**Libraries:** PyTorch, PyTorch Geometric (PyG)
**Kaam:** Graph structure dekh ke har node ka risk score predict karo

```python
class AtmoGraphGNN(nn.Module):
    def __init__(self):
        self.conv1 = GCNConv(10, 32)   # 10 features → 32 hidden
        self.conv2 = GCNConv(32, 32)   # 32 → 32
        self.output = nn.Linear(32, 1) # 32 → 1 risk score

    def forward(self, x, edge_index):
        x = F.relu(self.conv1(x, edge_index))  # Layer 1
        x = F.relu(self.conv2(x, edge_index))  # Layer 2
        x = self.output(x)
        return torch.sigmoid(x)  # 0 to 1 risk score
```

**GCNConv kya hai?** — Graph Convolutional Network layer. Ye ek node ki features ko uske neighbors ki features se combine karta hai. Matlab ek supplier ka risk score uske connected events aur products se influence hota hai.

**Input:**
- x = har node ke 10 features (numbers)
- edge_index = graph connections (kaun kaun se nodes connected hain)

**Output:**
- Har node ke liye ek risk score (0.0 to 1.0)

Trained model save hota hai: `backend/models/atmograph_gnn.pt`

---

## 5.6 — gnn_prediction_service.py (GNN Ko Chalana)

**Language:** Python
**Kaam:** Saved GNN model load karo, Neo4j graph lo, prediction karo

```python
# Model load karo
checkpoint = torch.load("models/atmograph_gnn.pt")
model.load_state_dict(checkpoint["model_state_dict"])
model.eval()

# Graph lo Neo4j se
graph_result = graph_service.build_event_graph(graph_id)

# Tensors banao
x = torch.tensor(graph_result["x"], dtype=torch.float)
edge_index = torch.tensor(graph_result["edge_index"], dtype=torch.long)

# Prediction karo
with torch.no_grad():
    predictions = model(x, edge_index)

# 0-1 range ko 0-100 mein convert karo
risk_scores = [float(p) * 100.0 for p in predictions]
```

---

## 5.7 — hybrid_prediction_service.py (Rule + GNN Milao)

**Language:** Python
**Kaam:** Rule-based aur GNN predictions ko combine karo

```python
# Rule-based prediction
base_score = predict_event_impact(db, event_id)["risk_score"]  # e.g. 65.0

# GNN prediction
gnn_score = gnn_service.predict(graph_id)["overall_risk_score"]  # e.g. 72.0

# Hybrid = 40% rule + 60% GNN
final_score = base_score * 0.40 + gnn_score * 0.60
# = 65 * 0.4 + 72 * 0.6 = 26 + 43.2 = 69.2
```

GNN ko zyada weight (60%) isliye diya kyunki wo graph structure samajhta hai.

---

## 5.8 — ripple_engine.py (Visual Ripple Graph Banana)

**Language:** Python
**Kaam:** Prediction results leke ek visual graph banata hai (nodes + edges)

```
Event Node (Rotterdam Strike, risk: 69.2)
    ↓ "affects" edge
Location Node (Rotterdam)
    ↓ "disrupts" edge
Supplier Node (Samsung, risk: 69.2)
    ↓ "has_impact" edge
Impact Node (supply_disruption, delay: 10 days)
    ↓ "impacts" edge
Product Node (OLED Panel, risk: 69.2)
```

Frontend pe ye graph visually dikhta hai — React Flow library se.

---

## 5.9 — news_ingestion_service.py (RSS News Processor)

**Language:** Python
**Libraries:** urllib (HTTP requests), xml.etree.ElementTree (XML parsing)
**Kaam:** RSS feed se news fetch karo, parse karo, pipeline mein dalo

### RSS Kya Hai?
RSS ek XML format hai jisme news websites apni latest news publish karti hain.
Google News, Reuters, BBC sab RSS feeds dete hain.

```xml
<rss>
  <channel>
    <item>
      <title>Strike at Rotterdam port disrupts shipping</title>
      <description>Workers walked out on Monday...</description>
      <pubDate>Mon, 15 Jan 2024</pubDate>
    </item>
  </channel>
</rss>
```

### Default RSS URL:
```
https://news.google.com/rss/search?q=supply+chain+disruption
```

### Flow:
```
RSS URL → HTTP fetch → XML parse → articles list
    ↓
Duplicate check (title already in DB?)
    ↓
IntelligencePipeline.process() → full analysis
    ↓
WebSocket broadcast → frontend ko real-time update
```

---

## 5.10 — live_news_monitor.py (Background RSS Monitor)

**Language:** Python
**Library:** asyncio (Python async)
**Kaam:** Background mein har 5 minute mein RSS check karta rehta hai

```python
class LiveNewsMonitor:
    def __init__(self):
        self.interval_seconds = 300  # 5 minute
        self.limit = 10              # Ek baar mein max 10 articles

    async def _run(self):
        await asyncio.sleep(2)   # Startup ke 2 sec baad pehla check
        await self._run_once()

        while self._running:
            await asyncio.sleep(300)  # Har 5 min
            await self._run_once()

    async def _run_once(self):
        db = SessionLocal()          # Fresh DB session
        service = NewsIngestionService(db)
        result = await asyncio.to_thread(
            service.ingest_rss,      # Sync code ko async thread mein chalao
            limit=10,
            auto_simulate=True
        )
        db.close()
```

**asyncio.to_thread()** — Synchronous (blocking) code ko background thread mein chalata hai taaki main FastAPI event loop block na ho.

---

## 5.11 — supply_chain/disruption_simulator.py (Business Impact Calculator)

**Language:** Python
**Kaam:** Agar ek supplier fail ho jaye toh business pe kya asar padega?

Ye sabse complex service hai. Step by step:

### Step 1 — Lost Supply Calculate Karo
```
Supplier X normally 1000 units deta tha → ab 0 → lost_supply = 1000
```

### Step 2 — Alternative Suppliers Dhundo
```
Supplier Y ke paas 300 units spare capacity hai → recovery = 300
Remaining loss = 1000 - 300 = 700
```

### Step 3 — Inventory Check Karo
```
Warehouse mein 200 units hain → net_shortage = 700 - 200 = 500
```

### Step 4 — Demand Calculate Karo
```
Daily demand = 100 units/day
Shortage delay = 500 / 100 = 5 days
```

### Step 5 — Route Disruption Check Karo
```
Normal transit = 14 days (Shanghai to Germany)
Disruption delay = +7 days (port strike)
Effective route time = 21 days
```

### Step 6 — Risk Score Calculate Karo
```python
score = 0
if lost_supply > 0:          score += 20
if gross_shortage > 0:       score += 15
if net_shortage > 0:         score += 30
if disruption_delay > 0:     score += min(20, delay * 2.5)
if inventory <= 0:           score += 10
if criticality == "critical": score += 10
# Final score: 0-100
```

### Step 7 — Product aur Plant Impact
```
Component shortage → Product production stop?
Multiple components → Plant-level impact
```

---

## 5.12 — websocket_manager.py (Real-Time Updates)

**Language:** Python
**Library:** FastAPI WebSocket
**Kaam:** Jab bhi nayi news process ho, frontend ko turant update bhejo

```python
class WebSocketManager:
    def __init__(self):
        self.connections = []  # Saare connected browsers

    async def connect(self, websocket):
        await websocket.accept()
        self.connections.append(websocket)

    async def broadcast(self, message):
        for websocket in self.connections:
            await websocket.send_json(message)
```

Frontend WebSocket se connected rehta hai. Jab bhi news aati hai:
```
News processed → broadcast("EVENT_CREATED", data)
                → broadcast("IMPACT_UPDATED", data)
                → broadcast("RISK_UPDATED", data)
                → broadcast("PREDICTION_UPDATED", data)
```

Frontend automatically update ho jaata hai bina page refresh ke.

---

## 5.13 — auth_service.py (Login/Register)

**Language:** Python
**Libraries:** bcrypt (password hashing), python-jose (JWT tokens)
**Kaam:** User authentication

```
Register: email + password → bcrypt hash → database save
Login:    email + password → hash verify → JWT token generate
API call: JWT token → verify → user identify
```

**JWT (JSON Web Token)** — Ek encrypted string jo user ki identity prove karta hai.
Frontend localStorage mein save karta hai, har API call mein bhejta hai.

---

## 5.14 — dashboard_engine.py (Dashboard Data)

**Language:** Python
**Kaam:** Dashboard ke liye summary data prepare karta hai

```python
{
    "total_events": 47,
    "active_events": 12,
    "critical_events": 3,
    "affected_suppliers": 8,
    "affected_products": 23,
    "average_risk_score": 67.4,
    "recent_events": [...],
}
```

---

## 5.15 — supply_chain/route_impact_service.py (Route Intelligence)

**Language:** Python
**Kaam:** Supplier ke routes check karta hai — kya disruption location supplier ke route pe hai?

```
Supplier: Shanghai, China
Route: Shanghai → Suez Canal → Rotterdam → Germany
Disruption: Suez Canal blocked

→ Route disrupted: YES
→ Additional delay: 14 days (via Cape of Good Hope)
```

---

## 5.16 — supply_chain/resilience_service.py (Resilience Score)

**Language:** Python
**Kaam:** Supply chain kitni resilient hai? Ek score deta hai.

Factors:
- Alternative suppliers hain? (+points)
- Inventory buffer hai? (+points)
- Single point of failure hai? (-points)
- Geographic diversification hai? (+points)

---

## 5.17 — entity_resolver.py (Entity Matching)

**Language:** Python
**Library:** difflib (Python standard library — fuzzy matching)
**Kaam:** NLP se nikale entity names ko database ke canonical names se match karo

```
NLP nikala: "Samsung Electronics Co."
Database mein: "Samsung Electronics"
→ Match! (similarity > 0.88)
```

---

## 5.18 — location_resolution_service.py (Location Samajhna)

**Language:** Python
**Kaam:** Raw location string ko structured location mein convert karo

```
Input:  "Rotterdam"
Output: {
    "raw": "Rotterdam",
    "normalized": "Rotterdam",
    "location_type": "port",
    "city": "Rotterdam",
    "country": "Netherlands",
    "confidence": 0.95
}
```

---

# SECTION 6 — API ROUTES (Endpoints)

Ye files define karti hain ki kaunse URLs pe kya milega.

---

## 6.1 — routes/events.py

```
GET  /api/events          → Saare events list karo
GET  /api/events/{id}     → Ek event ki detail
POST /api/events          → Naya event banao
PUT  /api/events/{id}     → Event update karo
DELETE /api/events/{id}   → Event delete karo
```

---

## 6.2 — routes/graph.py

```
GET /api/graph/statistics              → Neo4j graph stats
GET /api/graph/event/{id}              → Event ka graph
GET /api/graph/event/{id}/suppliers    → Affected suppliers
GET /api/graph/event/{id}/products     → Affected products
GET /api/graph/event/{id}/ripple       → Ripple paths
```

---

## 6.3 — routes/news.py

```
POST /api/news/analyze      → Manual news analyze karo
POST /api/news/ingest-rss   → RSS feed se news lo
GET  /api/news/monitor-status → Live monitor ka status
```

---

## 6.4 — routes/predictions.py

```
GET /api/predictions/{event_id}  → Event ka prediction
```

---

## 6.5 — routes/ripple.py

```
GET /api/ripple/{event_id}  → Ripple effect graph
```

---

## 6.6 — routes/graph_intelligence.py

```
GET  /api/graph-intelligence/features/{graph_id}         → Graph features
GET  /api/graph-intelligence/gnn-graph/{graph_id}        → GNN ke liye graph
GET  /api/graph-intelligence/gnn-predict/{graph_id}      → GNN prediction
GET  /api/graph-intelligence/hybrid-predict/{eid}/{gid}  → Hybrid prediction
GET  /api/graph-intelligence/event-impact/{event_id}     → Event impact graph
```

---

## 6.7 — routes/supply_chain.py

```
GET  /api/supply-chain/business-graph    → Business supply chain graph
POST /api/supply-chain/import-excel      → Excel file upload
GET  /api/supply-chain/simulate/{id}     → Supplier failure simulate karo
```

---

## 6.8 — routes/auth.py

```
POST /api/auth/register  → Naya account banao
POST /api/auth/login     → Login karo, JWT token lo
GET  /api/auth/me        → Apni info dekho
```

---

## 6.9 — routes/websocket.py

```
WS ws://localhost:8000/ws/updates  → Real-time updates ka WebSocket
```

---

## 6.10 — routes/health.py

```
GET /health              → Server theek hai?
GET /api/diagnostics     → Detailed system status
```

---

## 6.11 — routes/nlp.py

```
POST /api/nlp/analyze  → Text analyze karo (NLP test)
```

---

## 6.12 — routes/nlp_graph.py

```
POST /api/nlp-graph/sync    → NLP graph Neo4j mein sync karo
GET  /api/nlp-graph/ripple  → NLP graph ka ripple
```

---

# SECTION 7 — SCHEMAS (Data Validation)

**Library:** Pydantic
**Kaam:** API request/response ka structure define karo aur validate karo

```python
# schemas/event.py
class EventCreate(BaseModel):
    title: str
    description: str
    event_type: str
    severity: str = "medium"

class EventResponse(BaseModel):
    id: int
    title: str
    event_type: str
    severity: str
    created_at: datetime
```

Pydantic automatically validate karta hai — agar `title` missing hai toh 422 error dega.

---

# SECTION 8 — FRONTEND (React UI)

**Language:** TypeScript
**Framework:** React 18
**Build Tool:** Vite (bahut fast)
**Icons:** Lucide React
**Styling:** CSS (App.css, index.css)

---

## 8.1 — src/App.tsx (Poora UI Ka Controller)

**Kaam:** Sidebar navigation + page switching

7 tabs hain:

| Tab | Page | Kya dikhta hai |
|-----|------|----------------|
| overview | DashboardOverview.tsx | Ripple Predictor Studio |
| network | SupplyNetworkPage.tsx | Interactive graph |
| simulator | SupplyChainSimulator.tsx | What-If simulator |
| catalog | ExcelDataImport.tsx | Excel upload |
| radar | IncidentRadarPage.tsx | Live news radar |
| history | HistoricalIntelligence.tsx | Purani events |
| status | SystemStatusPage.tsx | System health |

**Multi-tenant workspace:**
- Har company ka alag workspace hota hai
- WorkspaceModal se switch kar sakte hain
- "PRIVATE" badge dikhta hai — data isolated hai

---

## 8.2 — src/services/api.ts (Backend Se Baat Karna)

**Kaam:** Saari HTTP calls yahan se hoti hain

```typescript
const API_BASE_URL = "http://127.0.0.1:8000";

async function request<T>(endpoint: string, options = {}): Promise<T> {
    const token = localStorage.getItem("atmograph_token");
    const response = await fetch(API_BASE_URL + endpoint, {
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`,
        },
        ...options,
    });
    return response.json();
}

// Usage examples:
export function getEvents() {
    return request("/api/events");
}

export function analyzeNews(title, description) {
    return request("/api/news-intelligence/analyze", {
        method: "POST",
        body: JSON.stringify({ title, description }),
    });
}
```

---

## 8.3 — src/services/websocket.ts (Real-Time Connection)

**Kaam:** Backend WebSocket se connected rehna

```typescript
const ws = new WebSocket("ws://localhost:8000/ws/updates");

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.type === "EVENT_CREATED") {
        // Naya event aaya — UI update karo
    }
    if (data.type === "RISK_UPDATED") {
        // Risk score update hua
    }
};
```

---

## 8.4 — src/context/AuthContext.tsx (Login State)

**Kaam:** Poore app mein user ka login state manage karna

```typescript
const AuthContext = createContext({
    user: null,
    isAuthenticated: false,
    login: (userData, token) => {},
    logout: () => {},
});

// JWT token localStorage mein save hota hai
// Har page refresh pe check hota hai
```

---

## 8.5 — src/pages/DashboardOverview.tsx (Main Dashboard)

**Kaam:** Ripple Predictor Studio — news dalo, prediction dekho

Features:
- News input form
- Risk score display
- Affected suppliers list
- Affected products list
- Ripple graph visualization

---

## 8.6 — src/pages/supply-chain/SupplyChainSimulator.tsx (What-If Simulator)

**Kaam:** "Agar ye supplier fail ho jaye toh kya hoga?" simulate karo

User select karta hai:
- Kaun sa supplier fail hua
- Disruption location
- Severity

System calculate karta hai:
- Lost supply units
- Alternative recovery
- Net shortage
- Delay days
- Production stop risk

---

## 8.7 — src/pages/supply-chain/ExcelDataImport.tsx (Data Upload)

**Kaam:** User apna supply chain data Excel mein upload karta hai

Excel template mein hota hai:
- Suppliers list
- Products list
- Components list
- Plants list
- Inventory levels
- Demand data
- Supply allocations

---

## 8.8 — src/pages/IncidentRadarPage.tsx (Live News Radar)

**Kaam:** Live news events dikhata hai, filter karo, analyze karo

Features:
- Real-time news feed
- Severity filter
- Event type filter
- Click karo → full analysis dekho
- "Simulate" button → simulator pe le jaao

---

## 8.9 — src/components/dashboard/SupplyGraph.tsx (Graph Visualization)

**Library:** React Flow (ya D3.js)
**Kaam:** Supply chain graph visually dikhata hai

Nodes:
- Event node (red/orange)
- Supplier node (blue)
- Product node (green)
- Location node (purple)
- Impact node (yellow)

Edges:
- "affects" — event → location/supplier
- "disrupts" — event → supplier
- "impacts" — event → product
- "supplies" — supplier → product

---

## 8.10 — src/hooks/useDashboard.ts (Dashboard Data Hook)

**Kaam:** Dashboard ke liye data fetch karne ka React hook

```typescript
function useDashboard() {
    const [events, setEvents] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        getEvents().then(setEvents).finally(() => setLoading(false));
    }, []);

    return { events, loading };
}
```

---

## 8.11 — src/hooks/useLiveUpdates.ts (WebSocket Hook)

**Kaam:** WebSocket se real-time updates receive karne ka React hook

```typescript
function useLiveUpdates(onUpdate) {
    useEffect(() => {
        const ws = new WebSocket("ws://localhost:8000/ws/updates");
        ws.onmessage = (e) => onUpdate(JSON.parse(e.data));
        return () => ws.close();  // Cleanup
    }, []);
}
```


---

# SECTION 9 — NEO4J FOLDER (Graph Database)

**Database:** Neo4j
**Query Language:** Cypher
**Port:** 7687 (Bolt protocol)

Neo4j ek **graph database** hai. Normal databases (MySQL, SQLite) mein data tables mein hota hai. Neo4j mein data **nodes aur relationships** mein hota hai — bilkul jaise ek map ya network diagram.

---

## 9.1 — neo4j/schema/constraints.cypher

**Kaam:** Unique constraints lagao — duplicate nodes mat bano

```cypher
CREATE CONSTRAINT event_id_unique
IF NOT EXISTS
FOR (e:Event)
REQUIRE e.event_id IS UNIQUE;
CREATE CONSTRAINT supplier_id_unique
IF NOT EXISTS
FOR (s:Supplier)
REQUIRE s.supplier_id IS UNIQUE;
```

---

## 9.2 — neo4j/schema/indexes.cypher

**Kaam:** Fast search ke liye indexes banao

```cypher
CREATE INDEX event_title_index IF NOT EXISTS
FOR (e:Event) ON (e.title);

CREATE INDEX supplier_name_index IF NOT EXISTS
FOR (s:Supplier) ON (s.name);
```

---

## 9.3 — neo4j/queries/graph_queries.cypher

**Kaam:** Common queries jo project mein use hoti hain

```cypher
-- Ek event se saare affected suppliers
MATCH (e:Event {event_id: $event_id})-[:AFFECTS]->(s:Supplier)
RETURN s.name, s.country;

-- Ripple paths — event se downstream sab kuch
MATCH path = (e:Event {event_id: $event_id})-[*1..5]->(downstream)
RETURN path;

-- Supplier ke saare products
MATCH (s:Supplier {supplier_id: $id})-[:SUPPLIES]->(p:Product)
RETURN p.name, p.category;
```

---

## 9.4 — neo4j/seeds/sample_graph.cypher

**Kaam:** Testing ke liye sample data

```cypher
CREATE (e:Event {event_id: 1, title: "Rotterdam Port Strike", severity: "high"})
CREATE (s:Supplier {supplier_id: 1, name: "Samsung Electronics", country: "South Korea"})
CREATE (p:Product {product_id: 1, name: "OLED Display Panel"})
CREATE (e)-[:AFFECTS {impact_level: "high"}]->(s)
CREATE (s)-[:SUPPLIES]->(p)
```

---

# SECTION 10 — DATA FOLDER

---

## 10.1 — data/templates/supply_chain_template.xlsx

**Kaam:** User ko ye template download karke apna data fill karna hota hai

Sheets:
- **Suppliers** — supplier_id, name, country, city
- **Products** — product_id, name, category
- **Components** — component_id, name, unit
- **Plants** — plant_id, name, location
- **Inventory** — component_id, quantity
- **Demand** — product_id, plant_id, daily_demand
- **SupplyAllocations** — supplier_id, component_id, capacity_units, spare_capacity
- **Dependencies** — product_id, component_id, required_quantity

---

## 10.2 — data/imports/

**Kaam:** User ke uploaded Excel files yahan save hote hain (UUID names se)

---

# SECTION 11 — BACKEND SCRIPTS

---

## 11.1 — backend/train_gnn.py

**Language:** Python
**Libraries:** PyTorch, PyTorch Geometric
**Kaam:** GNN model train karo

```python
# Neo4j se graph data lo
# Training data prepare karo
# Model train karo
# backend/models/atmograph_gnn.pt mein save karo
```

---

## 11.2 — backend/verify_atmograph.py

**Kaam:** Poora system check karo — database, Neo4j, NLP sab theek hai?

---

## 11.3 — backend/scripts/migrate_*.py

**Kaam:** Database schema changes apply karo (migrations)

---

# SECTION 12 — POORA DATA FLOW EK BAAR MEIN

Ye sabse important section hai. Ek baar poora flow samjho:

```
╔══════════════════════════════════════════════════════════════╗
║                    ATMOGRAPH DATA FLOW                       ║
╚══════════════════════════════════════════════════════════════╝

📰 RSS FEED (Google News / Reuters)
"Strike at Rotterdam port disrupts Samsung supply chain"
         │
         ▼
🔄 LiveNewsMonitor (har 5 min background mein)
   live_news_monitor.py
         │
         ▼
📥 NewsIngestionService.ingest_rss()
   news_ingestion_service.py
   - RSS XML fetch karo
   - Articles parse karo
   - Duplicate check karo
         │
         ▼
🧠 IntelligencePipeline.process()
   intelligence_pipeline.py
         │
    ┌────┴────────────────────────────────────┐
    │                                         │
    ▼                                         │
STEP 1: NLP Analysis                          │
nlp_engine.py (spaCy)                         │
→ event_type: "port_strike"                   │
→ severity: "high"                            │
→ locations: ["Rotterdam"]                    │
→ entities: ["Samsung", "Rotterdam"]          │
    │                                         │
    ▼                                         │
STEP 2: SQL Event Create                      │
SQLite database                               │
→ events table mein INSERT                    │
→ event_id = 47                               │
    │                                         │
    ▼                                         │
STEP 3: Legacy Entity Matching                │
→ "Samsung" database mein hai? YES            │
→ matched_suppliers = [Samsung]               │
→ matched_products = [OLED Panel]             │
    │                                         │
    ▼                                         │
STEP 4: Business Supplier Matching            │
→ User ke uploaded suppliers mein Samsung hai?│
→ match_score = 95 (strong NLP entity match)  │
    │                                         │
    ▼                                         │
STEP 5: SQL Supply Chain Links                │
→ supply_chain_links table mein INSERT        │
→ event_47 → Samsung → OLED Panel             │
→ estimated_delay_days = 10.0                 │
    │                                         │
    ▼                                         │
STEP 6: Neo4j Graph Sync                      │
neo4j_service.py                              │
→ Event node banao (event_47)                 │
→ Supplier node banao (Samsung)               │
→ Product node banao (OLED Panel)             │
→ AFFECTS relationship banao                  │
→ SUPPLIES relationship banao                 │
    │                                         │
    ▼                                         │
STEP 7: Prediction                            │
    │                                         │
    ├── Rule-based (prediction_engine.py)     │
    │   severity=high → score=80              │
    │   1 supplier → +5                       │
    │   1 product → +5                        │
    │   base_score = 54.0                     │
    │                                         │
    ├── GNN (gnn_prediction_service.py)       │
    │   Neo4j graph → tensors                 │
    │   AtmoGraphGNN.forward()                │
    │   gnn_score = 68.0                      │
    │                                         │
    └── Hybrid (hybrid_prediction_service.py) │
        final = 54*0.4 + 68*0.6 = 62.4        │
        risk_level = "high"                   │
    │                                         │
    ▼                                         │
STEP 8: Business Impact Simulation            │
disruption_simulator.py                       │
→ Samsung fails → lost_supply = 1000 units    │
→ Alternative supplier → recovery = 300       │
→ Inventory buffer → 200 units                │
→ net_shortage = 500 units                    │
→ shortage_delay = 5 days                     │
→ route_delay = 7 days (port strike)          │
→ production_stop = TRUE                      │
    │                                         │
    ▼                                         │
STEP 9-11: Final Response Build               │
    │                                         │
    └─────────────────────────────────────────┘
         │
         ▼
⚡ WebSocket Broadcast
websocket_manager.py
→ EVENT_CREATED → frontend
→ IMPACT_UPDATED → frontend
→ RISK_UPDATED → frontend
→ PREDICTION_UPDATED → frontend
         │
         ▼
🖥️ React Frontend
App.tsx → IncidentRadarPage.tsx
→ Naya event dikhao
→ Risk score: 62.4 (HIGH)
→ Affected: Samsung, OLED Panel
→ Delay: 7 days
→ Production stop: YES
         │
         ▼
📊 Ripple Graph (SupplyGraph.tsx)
ripple_engine.py → nodes + edges
→ Visual graph dikhao
→ Event → Samsung → OLED Panel
```

---

# SECTION 13 — TECHNOLOGIES COMPLETE LIST

| Technology | Type | Version | Kahan Use Hua | Kyu |
|-----------|------|---------|--------------|-----|
| **Python** | Language | 3.11+ | Backend + ML | Main language |
| **TypeScript** | Language | 5.x | Frontend | Type-safe JavaScript |
| **FastAPI** | Framework | 0.100+ | backend/app/ | Fast async API server |
| **SQLAlchemy** | ORM | 2.x | backend/app/models/ | Python se database |
| **Pydantic** | Validation | 2.x | backend/app/schemas/ | Data validation |
| **SQLite** | Database | 3.x | backend/atmograph.db | Local SQL database |
| **Neo4j** | Graph DB | 5.x | neo4j/ | Graph relationships |
| **neo4j (Python)** | Driver | 5.x | neo4j_service.py | Neo4j se baat karna |
| **spaCy** | NLP | 3.x | nlp_engine.py | News samajhna |
| **en_core_web_sm** | NLP Model | 3.x | entity_extractor.py | English NER model |
| **PyTorch** | ML | 2.x | gnn_model.py | Deep learning |
| **PyTorch Geometric** | Graph ML | 2.x | gnn_model.py | Graph Neural Network |
| **React** | UI Framework | 18.x | frontend/src/ | UI banana |
| **Vite** | Build Tool | 5.x | frontend/ | Fast development |
| **Lucide React** | Icons | latest | App.tsx | UI icons |
| **asyncio** | Async | stdlib | live_news_monitor.py | Background tasks |
| **bcrypt** | Crypto | latest | auth_service.py | Password hashing |
| **python-jose** | JWT | latest | auth_service.py | Auth tokens |
| **pydantic-settings** | Config | 2.x | core/config.py | .env file padhna |
| **difflib** | Fuzzy Match | stdlib | entity_resolver.py | Name matching |
| **xml.etree** | XML | stdlib | news_ingestion_service.py | RSS parse karna |
| **urllib** | HTTP | stdlib | news_ingestion_service.py | RSS fetch karna |
| **openpyxl** | Excel | latest | excel_importer.py | Excel read/write |
| **Cypher** | Query Lang | Neo4j | neo4j/queries/ | Graph queries |

---

# SECTION 14 — MULTI-TENANT SYSTEM (Har Company Ka Alag Data)

AtmoGraph ek **multi-tenant** system hai — matlab ek hi server pe multiple companies ka data hota hai, lekin sab alag alag.

```
Company A (Tata Motors) → company_id = "tata_001"
Company B (Samsung)     → company_id = "samsung_002"
Company C (Zomato)      → company_id = "zomato_003"
```

Har event, supplier, product pe `company_id` hota hai.
Jab koi query hoti hai, sirf us company ka data aata hai.

```python
# Sirf apni company ke events
events = db.query(Event).filter(Event.company_id == current_user.company_id).all()
```

**WorkspaceModal** se user multiple workspaces switch kar sakta hai.

---

# SECTION 15 — ENVIRONMENT VARIABLES (.env files)

---

## backend/.env

```
DATABASE_URL=sqlite:///./atmograph.db
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password_here
SECRET_KEY=your_jwt_secret_here
```

---

## frontend/.env

```
VITE_API_BASE_URL=http://127.0.0.1:8000
```

---

# SECTION 16 — PROJECT CHALANE KA TARIKA

## Backend Chalao:

```bash
cd backend
pip install -r requirements.txt
python -m spacy download en_core_web_sm
uvicorn app.main:app --reload --port 8000
```

## Frontend Chalao:

```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

## Neo4j Chalao:

```bash
# Neo4j Desktop ya Docker se
docker run -p 7474:7474 -p 7687:7687 neo4j:latest
```

## GNN Train Karo (Optional):

```bash
cd backend
python train_gnn.py
# Saves to backend/models/atmograph_gnn.pt
```

---

# SECTION 17 — TESTING

**Framework:** pytest
**Location:** backend/tests/

```
tests/
├── test_event_impact_graph_service.py    ← Event impact graph test
├── test_historical_intelligence_service.py
├── test_intelligence_contract.py         ← Pipeline contract test
├── test_multi_tenant_isolation.py        ← Company data isolation test
├── test_news_intelligence_api_contract.py
├── test_unified_intelligence_service.py
└── supply_chain/
    ├── test_disruption_simulator.py      ← Simulator test
    ├── test_resilience_service.py
    └── test_import_service.py
```

```bash
cd backend
pytest tests/ -v
```

---

# SECTION 18 — EK LINE MEIN POORA PROJECT

```
📰 News aao
    ↓
🧠 spaCy se samjho (event type, severity, location, entities)
    ↓
💾 SQLite mein save karo
    ↓
🕸️ Neo4j mein graph banao (Event → Supplier → Product)
    ↓
🤖 GNN se risk predict karo (PyTorch + PyG)
    ↓
📊 Business impact simulate karo (shortage, delay, production stop)
    ↓
⚡ WebSocket se frontend ko real-time update bhejo
    ↓
🖥️ React UI mein dikhao (graph, risk score, affected entities)
```

**Bas itna hi hai AtmoGraph!**

---

*Document generated: AtmoGraph Complete Technical Explanation*
*Coverage: All files, all technologies, all data flows*
