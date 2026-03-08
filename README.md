# Senate Bot Administrator

**Autonomous Digital Governance ChatOps Platform**

An AI-powered governance chatbot that helps citizens interact with government services through natural conversation. Built with **FastAPI**, **React**, and **Ollama (llama3.1:8b)**.

---

## 🏗️ Architecture

```
Senate-Bot-Administrator/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── routers/
│   │   │   ├── chat.py          # POST /chat — main conversation endpoint
│   │   │   ├── location.py      # GET /api/location/{pin}
│   │   │   ├── ration.py        # GET /api/ration/{ration_id}
│   │   │   ├── birth.py         # GET /api/birth/{certificate_id}
│   │   │   └── grievance.py     # POST /api/grievance
│   │   ├── bot/
│   │   │   ├── agent.py         # LLM Agent (Ollama integration)
│   │   │   └── router.py        # Service router & API adapter
│   │   └── services/            # YAML service configurations
│   │       ├── ration.yaml
│   │       ├── birth.yaml
│   │       ├── grievance.yaml
│   │       └── location.yaml
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # React Chat UI
│   │   ├── App.css              # Component styles
│   │   └── index.css            # Design system & animations
│   └── package.json
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Ollama** installed and running — [ollama.com](https://ollama.com)

### 1. Pull the LLM Model

```bash
ollama pull llama3.1:8b
```

Make sure Ollama is running:
```bash
ollama serve
```

### 2. Start the Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser.

---

## 🔗 API Endpoints

| Method | Endpoint                    | Description                    |
|--------|-----------------------------|--------------------------------|
| POST   | `/chat`                     | Main chatbot conversation      |
| GET    | `/api/location/{pin}`       | Postal PIN code lookup (live)  |
| GET    | `/api/ration/{ration_id}`   | Mock ration card status        |
| GET    | `/api/birth/{cert_id}`      | Mock birth certificate status  |
| POST   | `/api/grievance`            | Mock grievance registration    |

---

## 🧠 How It Works

1. **User sends a message** via the React chat UI.
2. **FastAPI `/chat` endpoint** forwards the conversation to the **LLM Agent**.
3. The agent uses **llama3.1:8b** via Ollama to detect intent and extract entities.
4. If an action is detected (e.g., `check_ration`), the **Service Router** calls the corresponding API.
5. Results are passed back to the LLM to compose a friendly, explainable response with policy references.

---

## 📋 Services

- **Ration Card Status** — Check entitlement and scheme info (mock)
- **Birth Certificate Status** — Check issuance status (mock)
- **Grievance Registration** — File a public complaint (mock)
- **Location Lookup** — Get district/state from PIN code (live API)
- **Scheme Eligibility** — Rule-based eligibility assessment

---

## 🛠️ Tech Stack

| Layer     | Technology           |
|-----------|---------------------|
| Frontend  | React (Vite)        |
| Backend   | FastAPI (Python)    |
| AI Model  | llama3.1:8b (Ollama)|
| Styling   | Vanilla CSS         |
