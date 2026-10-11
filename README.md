# AtmoGraph 🌐⚡

> **AI-Powered Supply Chain Ripple Effect Predictor & Resilience Intelligence Engine**  
> *Built with Neo4j Graph Database, spaCy NLP, Graph Neural Networks (PyTorch Geometric), FastAPI, and React.*

---

## 📌 Overview

**AtmoGraph** maps complex multi-tier supply chain networks to simulate, predict, and mitigate ripple-effect disruptions in real time. Combining graph topologies, live event extraction, and a hybrid prediction engine (Graph Neural Networks + rule-based cascades), AtmoGraph enables enterprises to proactively respond to weather events, geopolitical tensions, transit bottlenecks, and supplier failures.

---

## 🛠️ Key Capabilities

- **Interactive Knowledge Graphs**: Multi-tier supplier, factory, warehouse, and retail node dependencies powered by Neo4j and React Flow.
- **NLP Disruption Extraction**: Automated parsing and geo-entity resolution of live news feeds using spaCy.
- **Hybrid Ripple Effect Prediction**: 
  - **60%** Graph Neural Network (GNN) structural propagation embedding
  - **40%** Rule-based deterministic cascade simulation
- **Multi-Tenant Isolation**: Tenant-specific graph workspaces and pre-seeded enterprise datasets.
- **Real-Time Simulation & Radar**: Interactive disruption testing with historical intelligence replay and impact radius scoring.

---

## 🏗️ Architecture & Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 19, TypeScript, Vite, React Flow (@xyflow/react), Recharts, Lucide Icons |
| **Backend API** | FastAPI, Uvicorn, SQLAlchemy, Pydantic v2, Python 3.11/3.12 |
| **Graph Database** | Neo4j (Dockerized, Bolt Protocol & Cypher queries) |
| **Machine Learning & NLP** | PyTorch Geometric (GNN), spaCy (`en_core_web_sm`), Pandas |
| **Deployment & Orchestration** | Docker Compose |

---

## ⚙️ Prerequisites

Before getting started, make sure you have the following installed on your machine:

1. **Python (Version 3.11 or 3.12)**:  
   Download: [python.org/downloads](https://www.python.org/downloads/)  
   > ⚠️ **CRITICAL (Windows):** Check the box **"Add Python to PATH"** on the first installer screen!

2. **Node.js (LTS Version)**:  
   Download: [nodejs.org](https://nodejs.org/)  
   Follow standard installer defaults.

3. **Docker Desktop (For Neo4j Database)**:  
   Download: [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/)  
   Install Docker Desktop, restart your computer if prompted, and ensure the Docker engine is running.

---

## 🚀 Step-by-Step Setup Guide

Follow these steps sequentially on a new machine or setup.

### Step 1: Start the Neo4j Database (Docker)

1. Make sure **Docker Desktop** is running.
2. In the root `atmograph` folder, run:
   ```bash
   docker compose up -d
   ```
   *(Alternative without compose:)*
   ```bash
   docker run -d --name atmograph_neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:latest
   ```

* **Neo4j Browser UI:** [http://localhost:7474](http://localhost:7474)  
  * **Username:** `neo4j`  
  * **Password:** `password`

---

### Step 2: Setup & Run the Backend (FastAPI)

Open a terminal window (PowerShell or CMD) in the project directory:

```bash
# 1. Navigate to backend directory
cd backend

# 2. Create virtual environment
python -m venv .venv

# 3. Activate the virtual environment
# In Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# (Or in Windows CMD):
.venv\Scripts\activate.bat

# 4. Create environment configuration
copy .env.example .env

# 5. Install Python dependencies
pip install -r requirements.txt

# 6. Download NLP English model for spaCy
python -m spacy download en_core_web_sm

# 7. Initialize database tables
python -m app.core.init_db

# 8. Load baseline seed data
python -m app.core.seed

# 9. Start the Backend API server
uvicorn app.main:app --reload --port 8000
```

* **Backend API Docs (Swagger):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)  
* Keep this terminal window running.

---

### Step 3: Setup & Run the Frontend (React + Vite)

Open a **second** terminal window:

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Create environment configuration
copy .env.example .env

# 3. Install packages (first-time only)
npm install

# 4. Start the Frontend development server
npm run dev
```

* **Frontend Web Application:** [http://localhost:5173](http://localhost:5173)

---

### Step 4: Register & Explore Demo Data

1. Open [http://localhost:5173](http://localhost:5173) in your browser.
2. Click **Register**.
3. Enter any email and password of your choice.
4. In **Company Name**, enter your company name (e.g., `Mohilya Couture` to load the Surat textile dataset, `AdilQadri Perfumes` for the perfumes/attar dataset, or your custom company name).
5. Click **Create Account** to load the interactive dashboard, dependency graph, disruption simulator, and radar!

---

## ⚡ Daily Quick Start (Subsequent Runs)

Once installed, running AtmoGraph each day takes just 3 quick steps:

1. **Docker:** Ensure Docker Desktop is running (`docker compose up -d`).
2. **Backend (Terminal 1):**
   ```bash
   cd backend
   .\.venv\Scripts\activate
   uvicorn app.main:app --reload --port 8000
   ```
3. **Frontend (Terminal 2):**
   ```bash
   cd frontend
   npm run dev
   ```
4. **Browser:** Open [http://localhost:5173](http://localhost:5173).

---

## 📁 Repository Structure

```text
atmograph/
├── backend/
│   ├── app/
│   │   ├── api/routes/        # REST & WebSocket API endpoints
│   │   ├── core/              # Config, DB initialization, seed scripts
│   │   ├── models/            # SQLAlchemy models
│   │   ├── services/          # GNN, Neo4j, Hybrid Prediction, NLP services
│   ├── requirements.txt       # Python backend dependencies
│   └── .env.example           # Backend environment variables
├── frontend/
│   ├── src/
│   │   ├── components/        # Graph visualizers, simulator, radars
│   │   ├── pages/             # App views & dashboard
│   │   ├── services/          # API client services
│   ├── package.json           # Frontend dependencies & scripts
│   └── .env.example           # Frontend environment variables
├── ml/                        # GNN training & graph models
├── data/                      # Sample datasets & templates
├── docker-compose.yml         # Neo4j container setup
└── README.md                  # Project overview & execution guide
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
