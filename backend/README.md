# ProjectAria Backend 🚀

The FastAPI-based backend for ProjectAria.PA - a Multi-Service Business Intelligence Platform.

## 🎯 Overview

This backend provides a comprehensive API and WebSocket interface for ProjectAria's AI-powered business management system. It integrates with Google Calendar, Tally ERP, WhatsApp, and AI services to provide a unified business intelligence platform.

## 🏗️ Architecture

### **Multi-Service Architecture**
```
User Request → AI Interpretation → Service Orchestration → Unified Response
```

**Core Components**:
- **API Layer**: FastAPI with automatic OpenAPI documentation
- **WebSocket Layer**: Real-time communication for chat
- **Service Layer**: Business logic and external integrations
- **Data Layer**: SQLAlchemy ORM with PostgreSQL
- **AI Layer**: GPT/Gemini integration for natural language processing

## 🛠️ Tech Stack

- **Framework**: FastAPI with WebSocket support
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Migrations**: Alembic for database schema management
- **Authentication**: Google OAuth 2.0 + JWT
- **AI Services**: OpenAI GPT-4 / Google Gemini Pro
- **External APIs**: Google Calendar, Tally ERP, Twilio WhatsApp
- **Logging**: Structured logging with ContextVars
- **Testing**: Pytest with async support

## 📁 Project Structure

```
backend/
├── app/
│   ├── core/                    # Core configuration
│   │   ├── config.py            # Environment configuration
│   │   ├── security.py          # JWT and OAuth handling
│   │   └── logging_config.py    # Structured logging setup
│   ├── db/                      # Database layer
│   │   ├── database.py          # Database connection
│   │   ├── models.py            # SQLAlchemy models
│   │   └── crud.py              # CRUD operations
│   ├── routes/                  # API endpoints
│   │   ├── auth_routes.py       # Authentication endpoints
│   │   ├── calendar_routes.py   # Calendar management
│   │   ├── chat_routes.py       # Chat and WebSocket
│   │   ├── user_routes.py       # User management
│   │   ├── integrations/        # Integration endpoints
│   │   │   ├── tally_routes.py  # Tally ERP integration
│   │   │   └── integration_status_routes.py
│   │   └── whatsapp/           # WhatsApp integration
│   │       ├── webhook_routes.py
│   │       └── handlers/        # Message handlers
│   ├── services/               # Business logic
│   │   ├── ai_service.py       # AI service orchestration
│   │   ├── ai_functions.py     # AI function definitions
│   │   ├── gpt_adapter.py      # OpenAI GPT integration
│   │   ├── gemini_adapter.py   # Google Gemini integration
│   │   ├── calendar_service.py # Google Calendar integration
│   │   ├── chat_handler.py     # Chat message processing
│   │   ├── twilio_service.py   # WhatsApp messaging
│   │   └── accounting/         # Accounting integrations
│   │       ├── tally_sql_service.py
│   │       └── README.md
│   └── utils/                  # Utility functions
│       └── helpers.py
├── alembic/                    # Database migrations
├── tests/                      # Test suite
├── logs/                       # Application logs
├── requirements.txt            # Python dependencies
├── alembic.ini                # Alembic configuration
└── run.py                     # Application entry point
```

## 🚀 Getting Started

### **Prerequisites**
- Python 3.9+
- PostgreSQL 12+
- Google Cloud Console project
- OpenAI API key or Google Gemini API key
- Twilio account for WhatsApp

### **Installation**
```bash
# Clone repository
git clone <repository-url>
cd ProjectAriaPA/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### **Environment Configuration**
Create `.env` file:
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/projectaria

# Authentication
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
JWT_SECRET=your_jwt_secret_key

# AI Services
OPENAI_API_KEY=your_openai_api_key
GEMINI_API_KEY=your_gemini_api_key

# WhatsApp
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_WHATSAPP_NUMBER=your_whatsapp_number

# Tally ERP
TALLY_SERVER_URL=http://localhost:9000

# Application
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### **Database Setup**
```bash
# Run migrations
alembic upgrade head

# Create initial data (optional)
python -c "from app.db.crud import create_initial_data; create_initial_data()"
```

### **Run Application**
```bash
# Development server
python run.py

# Or with uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📚 API Documentation

### **Authentication Endpoints**
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/login` | GET | Google OAuth login |
| `/auth/callback` | GET | OAuth callback |
| `/auth/me` | GET | Get current user |
| `/auth/refresh` | POST | Refresh JWT token |

### **Chat & WebSocket**
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/ws/chat` | WebSocket | Real-time chat connection |
| `/chat/history` | GET | Get chat history |
| `/chat/history` | DELETE | Clear chat history |
| `/chat/context` | GET | Get user context |

### **Calendar Management**
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/calendar/today` | GET | Today's events |
| `/calendar/upcoming` | GET | Upcoming events |
| `/calendar/events` | POST | Create event |
| `/calendar/events/{event_id}` | GET | Get event details |
| `/calendar/events/{event_id}` | PUT | Update event |
| `/calendar/events/{event_id}` | DELETE | Delete event |

### **User Management**
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/users/me` | GET | Get user profile |
| `/users/me` | PUT | Update user profile |
| `/users/contacts` | GET | Get user contacts |
| `/users/contacts` | POST | Add contact |

### **Tally ERP Integration**
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tally/test-connection` | GET | Test Tally connection |
| `/tally/company-info` | GET | Get company information |
| `/tally/ledgers` | GET | Get ledger list |
| `/tally/ledger-balance` | GET | Get ledger balance |
| `/tally/vouchers` | GET | Get voucher data |
| `/tally/stock-items` | GET | Get stock items |
| `/tally/parties` | GET | Get party data |

### **WhatsApp Integration**
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/whatsapp/webhook` | POST | Twilio webhook |
| `/whatsapp/send` | POST | Send WhatsApp message |
| `/whatsapp/status` | GET | Get WhatsApp status |

## 🤖 AI Integration

### **Function Calling**
The AI system uses function calling to execute business operations:

```python
# Example AI function
{
    "name": "get_today_events",
    "description": "Fetch ONLY today's Google Calendar events for the user.",
    "parameters": {
        "type": "object",
        "properties": {},
        "required": []
    }
}
```

### **Available AI Functions**
- **Calendar**: `get_today_events`, `get_upcoming_events`, `create_calendar_event`
- **Accounting**: `get_tally_ledger_balance`, `get_tally_vouchers`, `get_tally_stock_items`
- **User**: `get_user_profile`, `get_help`
- **General**: `get_help`, `unknown`

### **AI Service Architecture**
```python
# AI service orchestration
class AIService:
    def __init__(self):
        self.gpt_adapter = GPTAdapter()
        self.gemini_adapter = GeminiAdapter()
    
    async def process_message(self, message: str, user_id: int):
        # Interpret user intent
        intent = await self.interpret_message(message)
        
        # Execute appropriate function
        result = await self.execute_function(intent, user_id)
        
        return result
```

## 🔌 WebSocket Communication

### **Connection Protocol**
```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/chat?token=jwt_token');

// Send message
ws.send(JSON.stringify({
    type: 'message',
    content: 'What\'s on my calendar today?'
}));

// Receive response
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    // Handle response
};
```

### **Message Types**
- **`message`**: Chat messages
- **`typing`**: Typing indicators
- **`history`**: Chat history
- **`error`**: Error messages
- **`status`**: Connection status

## 🗄️ Database Schema

### **Core Models**
```python
# User model
class User(Base):
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    google_id = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Chat message model
class ChatMessage(Base):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String)  # "user" or "assistant"
    content = Column(String)
    intent = Column(String)  # AI detected intent
    created_at = Column(DateTime, default=datetime.utcnow)

# Contact model
class Contact(Base):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    email = Column(String)
    phone = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
```

## 🔒 Security

### **Authentication Flow**
1. **Google OAuth**: User authenticates with Google
2. **JWT Token**: Server issues JWT token
3. **Token Validation**: All requests validate JWT
4. **User Context**: Requests are scoped to user

### **Security Features**
- **JWT Tokens**: Secure token-based authentication
- **OAuth 2.0**: Google OAuth integration
- **CORS**: Cross-origin resource sharing
- **Rate Limiting**: API rate limiting
- **Input Validation**: Request validation
- **SQL Injection Protection**: SQLAlchemy ORM protection

## 📊 Logging

### **Structured Logging**
```python
# User context logging
logger.info(f"Processing request for user {user_id}")

# Request/response logging
logger.info(f"API request: {method} {endpoint}")
logger.info(f"API response: {status_code} {response_time}ms")

# Error logging
logger.error(f"Error processing request: {error}")
```

### **Log Levels**
- **DEBUG**: Detailed debugging information
- **INFO**: General information
- **WARNING**: Warning messages
- **ERROR**: Error messages
- **CRITICAL**: Critical errors

## 🧪 Testing

### **Test Structure**
```
tests/
├── conftest.py              # Test configuration
├── test_ai_functions.py     # AI function tests
├── test_calendar_handler.py # Calendar tests
├── test_calendar_service.py # Calendar service tests
└── test_reminder_service.py # Reminder tests
```

### **Running Tests**
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_ai_functions.py

# Run with coverage
pytest --cov=app

# Run with verbose output
pytest -v
```

### **Test Categories**
- **Unit Tests**: Individual function testing
- **Integration Tests**: Service integration testing
- **API Tests**: Endpoint testing
- **WebSocket Tests**: Real-time communication testing

## 🚀 Deployment

### **Production Configuration**
```bash
# Environment variables
ENVIRONMENT=production
DATABASE_URL=postgresql://user:password@host:port/database
LOG_LEVEL=INFO

# Security
JWT_SECRET=strong_secret_key
CORS_ORIGINS=["https://yourdomain.com"]

# External services
OPENAI_API_KEY=your_production_key
TWILIO_ACCOUNT_SID=your_production_sid
```

### **Docker Deployment**
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### **Database Migrations**
```bash
# Create new migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## 📈 Performance

### **Optimization Strategies**
- **Connection Pooling**: Database connection pooling
- **Caching**: Redis caching for frequently accessed data
- **Async Operations**: Non-blocking I/O operations
- **Database Indexing**: Optimized database queries
- **Rate Limiting**: API rate limiting

### **Monitoring**
- **Response Times**: API response time monitoring
- **Error Rates**: Error rate tracking
- **Database Performance**: Query performance monitoring
- **Memory Usage**: Memory usage tracking

## 🔧 Configuration

### **Environment Variables**
```bash
# Application
ENVIRONMENT=development|production
LOG_LEVEL=DEBUG|INFO|WARNING|ERROR|CRITICAL

# Database
DATABASE_URL=postgresql://user:password@host:port/database

# Authentication
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
JWT_SECRET=your_jwt_secret

# AI Services
OPENAI_API_KEY=your_openai_key
GEMINI_API_KEY=your_gemini_key

# External Services
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TALLY_SERVER_URL=http://localhost:9000
```

### **Database Configuration**
```python
# Database settings
DATABASE_URL = os.getenv("DATABASE_URL")
DB_POOL_SIZE = 10
DB_MAX_OVERFLOW = 20
DB_POOL_TIMEOUT = 30
```

## 🤝 Contributing

### **Development Workflow**
1. **Fork Repository**: Create your own fork
2. **Create Branch**: `git checkout -b feature/amazing-feature`
3. **Make Changes**: Implement your feature
4. **Add Tests**: Write tests for your changes
5. **Run Tests**: Ensure all tests pass
6. **Commit Changes**: `git commit -m 'Add amazing feature'`
7. **Push Branch**: `git push origin feature/amazing-feature`
8. **Create PR**: Open a pull request

### **Code Standards**
- **PEP 8**: Follow Python style guidelines
- **Type Hints**: Use Python type hints
- **Docstrings**: Write comprehensive docstrings
- **Testing**: Write tests for new features
- **Documentation**: Update documentation

## 📞 Support

For questions and support:
- **Email**: projectaria.pa@gmail.com
- **Issues**: GitHub Issues
- **Documentation**: Project documentation

## 📄 License

MIT License - see main project LICENSE file.

---

⭐ **Star this repo if you find it helpful!**

