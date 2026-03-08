# Senate Bot Administrator

**Autonomous Digital Governance ChatOps Platform**

An AI-powered governance chatbot that helps Indian citizens interact with government services through natural conversation. Built with **FastAPI**, **React**, **Supabase**, and **Ollama (llama3.1:8b)**.

---

## Features

- **AI-Powered Conversational Interface** — Natural language interaction via Llama 3.1:8b
- **Supabase Authentication** — Google OAuth & Email/Password login
- **Persistent Chat History** — Conversations stored in Supabase PostgreSQL
- **Multilingual Support** — English, Hindi (हिंदी), Marathi (मराठी), Telugu (తెలుగు)
- **Light / Dark Mode** — Theme toggle with localStorage persistence
- **My Applications** — Track service request status (Pending/Approved/Rejected)
- **Government Scheme Awareness** — Auto-suggests eligible schemes with step-by-step guides
- **Responsive Design** — Desktop, tablet, and mobile with collapsible sidebar
- 🇮🇳 **Indian Government-Inspired UI** — Saffron accent, clean DigiLocker-style design

---

## Architecture

```
Senate-Bot-Administrator/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI entry point
│   │   ├── auth.py                  # JWT validation via Supabase
│   │   ├── supabase_client.py       # Shared Supabase client
│   │   ├── routers/
│   │   │   ├── chat.py              # POST /chat — main conversation + multilingual
│   │   │   ├── chats.py             # CRUD for chat sessions
│   │   │   ├── auth_router.py       # User upsert on login
│   │   │   ├── service_requests.py  # GET /service-requests
│   │   │   ├── location.py          # GET /api/location/{pin}
│   │   │   ├── ration.py            # GET /api/ration/{id} (Supabase)
│   │   │   ├── birth.py             # GET /api/birth/{id} (Supabase)
│   │   │   └── grievance.py         # POST /api/grievance
│   │   └── bot/
│   │       ├── agent.py             # LLM Agent + system prompt
│   │       ├── router.py            # Service router & action handlers
│   │       └── language.py          # Language detection (langdetect)
│   ├── schema.sql                   # Supabase database schema
│   ├── schema_v2.sql                # Migration: ration_cards, birth_certificates
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx                  # Main app with auth gate & chat
│   │   ├── App.css                  # Component styles
│   │   ├── index.css                # Design system (light/dark)
│   │   ├── Login.jsx                # Login page (Google + Email)
│   │   ├── Login.css
│   │   ├── LanguageSelect.jsx       # Language selection screen
│   │   ├── LanguageSelect.css
│   │   ├── LanguageSwitcher.jsx     # Global language dropdown
│   │   ├── supabaseClient.js        # Supabase JS client
│   │   ├── context/
│   │   │   └── ThemeContext.jsx      # Light/Dark theme provider
│   │   ├── components/
│   │   │   ├── ThemeToggle.jsx      # Sun/Moon toggle button
│   │   │   ├── MessageBubble.jsx    # Chat message component
│   │   │   ├── Button.jsx           # Reusable button variants
│   │   │   └── LoadingSpinner.jsx   # Animated SVG spinner
│   │   └── i18n/
│   │       ├── index.js             # react-i18next initialization
│   │       └── locales/
│   │           ├── en.json          # English
│   │           ├── hi.json          # Hindi
│   │           ├── mr.json          # Marathi
│   │           └── te.json          # Telugu
│   └── package.json
├── .gitignore
└── README.md
```

---

## Getting Started

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Ollama** — [ollama.com](https://ollama.com)
- **Supabase** project — [supabase.com](https://supabase.com)

### 1. Clone & Pull the LLM Model

```bash
git clone https://github.com/vikas-shirsath/Senate-Bot-Administrator.git
cd Senate-Bot-Administrator

ollama pull llama3.1:8b
ollama serve
```

### 2. Setup Supabase

1. Create a project at [supabase.com](https://supabase.com)
2. Run `backend/schema.sql` in **Supabase SQL Editor**
3. Run `backend/schema_v2.sql` in **Supabase SQL Editor**
4. Enable **Google OAuth** in Dashboard → Authentication → Providers
5. Create environment files:

**`backend/.env`**
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key
SUPABASE_JWT_SECRET=your-jwt-secret
```

**`frontend/.env`**
```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

### 3. Start the Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 4. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser.

---

## API Endpoints

| Method | Endpoint                     | Auth | Description                          |
|--------|------------------------------|------|--------------------------------------|
| POST   | `/chat`                      | ✅   | Main chatbot conversation            |
| GET    | `/chats`                     | ✅   | List user's chat sessions            |
| POST   | `/chats`                     | ✅   | Create new chat session              |
| DELETE | `/chats/{id}`                | ✅   | Delete a chat session                |
| GET    | `/chats/{id}/messages`       | ✅   | Get messages for a chat              |
| POST   | `/auth/callback`             | ✅   | Upsert user profile on login         |
| GET    | `/auth/me`                   | ✅   | Get current user profile             |
| GET    | `/service-requests`          | ✅   | List user's service applications     |
| GET    | `/api/location/{pin}`        | ❌   | Postal PIN code lookup (live API)    |
| GET    | `/api/ration/{ration_id}`    | ❌   | Ration card status (Supabase)        |
| GET    | `/api/birth/{cert_id}`       | ❌   | Birth certificate status (Supabase)  |
| POST   | `/api/grievance`             | ❌   | Register a grievance                 |

---

## How It Works

1. **User selects language** → English / Hindi / Marathi / Telugu
2. **User authenticates** via Google OAuth or Email/Password (Supabase Auth)
3. **User sends a message** via the React chat UI
4. **FastAPI `/chat` endpoint** detects language and forwards conversation to the **LLM Agent**
5. The agent uses **llama3.1:8b** to detect intent, extract entities, and ask follow-up questions
6. If an action is detected (e.g., `apply_service`), the **Service Router** validates required fields and calls the corresponding API
7. Results are passed back to the LLM to compose a friendly response in the user's language with policy references and scheme information
8. Messages are **persisted to Supabase** for chat history

---

## Services

| Service | Description | Data Source |
|---------|-------------|-------------|
| Ration Card Status | Check entitlement, scheme info, eligible benefits | Supabase |
| Birth Certificate | Check issuance status, enabled services | Supabase |
| Grievance Registration | File a public complaint with tracking ID | Mock |
| Location Lookup | Get district/state from PIN code | Live API |
| Scheme Eligibility | Rule-based assessment (PMAY, NFSA, scholarships) | Built-in |
| Apply for Service | Submit ration card, birth cert, housing applications | Supabase |
| Track Request Status | Check application status by request ID | Supabase |

---

## Multilingual Support

| Language | Code | UI | Chat |
|----------|------|-----|------|
| English  | `en` | ✅  | ✅   |
| Hindi    | `hi` | ✅  | ✅   |
| Marathi  | `mr` | ✅  | ✅   |
| Telugu   | `te` | ✅  | ✅   |

- Language selection on first visit
- Global language switcher on every page
- Backend detects message language via `langdetect`
- LLM responds in user's preferred language

---

## UI/UX

- **Indian Government-Inspired Design** — Saffron (#FF9933) accent, clean typography
- **Light / Dark Mode** — Toggle with localStorage persistence
- **Collapsible Sidebar** — Expands with labels, collapses to icons only
- **Responsive** — Desktop, tablet, mobile with hamburger menu
- **My Applications Panel** — Slide-in panel with color-coded status badges
- **Chat Bubbles** — Distinct user/bot styling, typing animation, timestamps

---

## Database Schema (Supabase)

| Table | Description |
|-------|-------------|
| `users` | User profiles (linked to Supabase Auth) |
| `chats` | Chat sessions per user |
| `messages` | Individual messages per chat |
| `service_requests` | Application submissions with status + applicant details |
| `ration_cards` | Ration card records |
| `birth_certificates` | Birth certificate records |

All tables have **Row Level Security (RLS)** — users can only access their own data.

---

## Tech Stack

| Layer          | Technology                    |
|----------------|-------------------------------|
| Frontend       | React (Vite) + Vanilla CSS    |
| Backend        | FastAPI (Python)              |
| AI Model       | Llama 3.1:8b (Ollama)         |
| Database       | Supabase (PostgreSQL)         |
| Authentication | Supabase Auth (Google + Email)|
| i18n           | react-i18next                 |
| Icons          | Lucide React                  |
| Language Detection | langdetect (Python)       |

---

## Team

Built for the **BlueBit Hackathon 2026**.


