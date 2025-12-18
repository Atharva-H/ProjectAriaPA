# ProjectAria.PA 🧠

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.68.0+-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-blue.svg)](https://reactjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> A Multi-Service Business Intelligence Platform that helps MSME CEOs manage their business through natural conversations. Connect Google Calendar, WhatsApp, Tally ERP, and AI to interact with your data like you're talking to your company.

## 🎯 Key Features

### 🤖 **AI-Powered Chat Interface**
- **Web Chat**: Real-time chat interface with WebSocket support
- **WhatsApp Integration**: Two-way messaging with AI-powered responses
- **Smart Intent Recognition**: ChatGPT/Gemini Pro for natural language understanding
- **Function Calling**: AI can execute calendar, accounting, and business operations

### 📅 **Calendar Management**
- **Google Calendar Integration**: Full CRUD operations via natural language
- **Smart Scheduling**: "Schedule meeting with sales team tomorrow at 2pm"
- **Event Details**: Rich event information with clickable links and emails
- **Conflict Detection**: Automatic scheduling conflict resolution

### 💼 **Accounting Integration**
- **Tally ERP Integration**: Direct connection to Tally Prime
- **Ledger Management**: View outstanding balances and customer data
- **Transaction History**: Access vouchers and financial records
- **Stock Management**: Inventory tracking and item management
- **Party Management**: Customer and vendor information

### 🔐 **Security & Authentication**
- **Google OAuth 2.0**: Secure authentication with JWT sessions
- **User Context**: Isolated data access per user
- **Enterprise Logging**: Structured logs with user context tracking

## 🏗️ Architecture

### **Multi-Service Business Intelligence Platform**
```
User Request → AI Interpretation → Service Orchestration → Unified Response
```

**Core Services**:
- **Calendar Service**: Google Calendar integration
- **Accounting Service**: Tally ERP integration  
- **WhatsApp Service**: Twilio messaging
- **AI Service**: GPT/Gemini integration
- **Chat Service**: WebSocket real-time communication

## 🛠️ Tech Stack

### **Backend**
- **Framework**: FastAPI with WebSocket support
- **Database**: PostgreSQL with SQLAlchemy ORM
- **AI**: OpenAI GPT-4 / Google Gemini Pro
- **Authentication**: Google OAuth 2.0 + JWT
- **Messaging**: Twilio WhatsApp API
- **Logging**: Structured logging with ContextVars

### **Frontend**
- **Framework**: React 18 with Vite
- **Styling**: Tailwind CSS
- **Real-time**: WebSocket integration
- **Routing**: React Router v6
- **UI Components**: Lucide React icons

### **Integrations**
- **Calendar**: Google Calendar API
- **Accounting**: Tally ERP (XML API)
- **Messaging**: Twilio WhatsApp API
- **AI**: OpenAI API / Google Gemini API

## 🚀 Quick Start

### **1. Clone & Setup**
```bash
git clone https://github.com/<username>/ProjectAriaPA
cd ProjectAriaPA

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install
```

### **2. Environment Configuration**
Create `.env` file in backend directory:
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/projectaria

# Authentication
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
JWT_SECRET=your_jwt_secret

# AI Services
OPENAI_API_KEY=your_openai_key
GEMINI_API_KEY=your_gemini_key

# WhatsApp
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_WHATSAPP_NUMBER=your_whatsapp_number

# Tally ERP
TALLY_SERVER_URL=http://localhost:9000
```

### **3. Database Setup**
```bash
cd backend
alembic upgrade head
```

### **4. Run Services**
```bash
# Backend (Terminal 1)
cd backend
source venv/bin/activate
python run.py

# Frontend (Terminal 2)
cd frontend
npm run dev

# For WhatsApp webhook (Terminal 3)
ngrok http 8000
```

## 📚 API Documentation

### **Authentication**
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/login` | GET | Google OAuth login |
| `/auth/callback` | GET | OAuth callback |
| `/auth/me` | GET | Get current user |

### **Chat & WebSocket**
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/ws/chat` | WebSocket | Real-time chat connection |
| `/chat/history` | GET | Get chat history |
| `/chat/history` | DELETE | Clear chat history |

### **Calendar**
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/calendar/today` | GET | Today's events |
| `/calendar/upcoming` | GET | Upcoming events |
| `/calendar/events` | POST | Create event |

### **Accounting (Tally)**
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tally/test-connection` | GET | Test Tally connection |
| `/tally/ledgers` | GET | Get ledger list |
| `/tally/ledger-balance` | GET | Get ledger balance |
| `/tally/vouchers` | GET | Get voucher data |
| `/tally/stock-items` | GET | Get stock items |
| `/tally/parties` | GET | Get party data |

## 💬 Natural Language Commands

### **Calendar Management**
- "What's on my calendar today?" → Shows today's events
- "Show me upcoming meetings" → Shows next 7 days
- "Schedule meeting with sales team tomorrow at 2pm" → Creates event
- "Any conflicts for tomorrow at 3pm?" → Checks availability

### **Accounting & Tally**
- "Show outstanding of ABC Company" → Ledger balance
- "What's the balance of XYZ Ltd?" → Customer balance
- "Show me last week's transactions" → Voucher data
- "List all stock items" → Inventory data
- "Show parties list" → Customer/vendor list

### **General Commands**
- "Help" → Shows available commands
- "What can you do?" → Lists capabilities
- "Show my profile" → User information

## 🔧 Development

### **Project Structure**
```
ProjectAriaPA/
├── backend/
│   ├── app/
│   │   ├── core/           # Configuration & security
│   │   ├── db/             # Database models & CRUD
│   │   ├── routes/         # API endpoints
│   │   ├── services/       # Business logic
│   │   └── utils/          # Helper functions
│   ├── alembic/           # Database migrations
│   └── tests/             # Test suite
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── services/      # API services
│   │   └── hooks/         # Custom hooks
│   └── public/            # Static assets
└── docs/                  # Documentation
```

### **Adding New Services**
1. Create service in `backend/app/services/`
2. Add AI function in `backend/app/services/ai_functions.py`
3. Create API routes in `backend/app/routes/`
4. Add frontend integration in `frontend/src/`

### **Testing**
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## 🚀 Deployment

### **Production Setup**
1. **Database**: Set up PostgreSQL
2. **Environment**: Configure production environment variables
3. **SSL**: Set up HTTPS for webhooks
4. **Monitoring**: Configure logging and monitoring
5. **Scaling**: Use load balancer for multiple instances

### **Docker Deployment**
```bash
# Build and run with Docker Compose
docker-compose up -d
```

## 🔜 Roadmap

### **Phase 1 - Core Platform** ✅
- [x] Web chat interface with WebSocket
- [x] Google Calendar integration
- [x] WhatsApp messaging
- [x] Tally ERP integration
- [x] AI-powered intent recognition

### **Phase 2 - Advanced Features** 🚧
- [ ] Gmail integration for email management
- [ ] Google Drive integration for document access
- [ ] Advanced Tally reporting
- [ ] Multi-user team management
- [ ] Mobile app (React Native)

### **Phase 3 - Enterprise Features** 📋
- [ ] Advanced analytics dashboard
- [ ] Custom AI training
- [ ] API rate limiting and quotas
- [ ] Enterprise SSO integration
- [ ] Advanced security features

## 📊 System Capabilities

### **Current Integrations**
- ✅ **Google Calendar**: Full CRUD operations
- ✅ **Tally ERP**: Complete accounting data access
- ✅ **WhatsApp**: Two-way messaging
- ✅ **Web Chat**: Real-time interface
- ✅ **AI Services**: GPT-4 and Gemini Pro

### **Business Functions**
- ✅ **Meeting Management**: Schedule, reschedule, conflict detection
- ✅ **Financial Data**: Ledger balances, transactions, reports
- ✅ **Inventory Management**: Stock items, quantities, values
- ✅ **Customer Management**: Party data, outstanding balances
- ✅ **Communication**: WhatsApp and web chat interfaces

## 👥 Contributing

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit changes**: `git commit -m 'Add amazing feature'`
4. **Push to branch**: `git push origin feature/amazing-feature`
5. **Open Pull Request**

### **Development Guidelines**
- Follow PEP 8 for Python code
- Use TypeScript for React components
- Write tests for new features
- Update documentation
- Follow conventional commits

## 📞 Contact

**Atharva Humar**
- **Email**: projectaria.pa@gmail.com
- **Role**: Founder & CEO, Paricott
- **LinkedIn**: [Atharva Humar](https://linkedin.com/in/atharvahumar)

## 📄 License

MIT License - feel free to use and modify!

---

⭐ **Star this repo if you find it helpful!**

## 🙏 Acknowledgments

- **FastAPI** for the amazing Python web framework
- **React** for the powerful frontend library
- **OpenAI** and **Google** for AI capabilities
- **Twilio** for WhatsApp integration
- **Tally Solutions** for ERP integration