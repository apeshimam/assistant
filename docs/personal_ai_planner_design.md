# Personal AI Planner - Design Document

## Executive Summary

A single-user AI-powered personal planning application that maintains persistent context about goals, tasks, and decisions. The system leverages Zep for memory persistence, integrates with Notion for task management, and provides an opinionated, challenging AI assistant that promotes deeper understanding rather than confirmation bias.

## Core Principles

1. **Context Persistence**: Every interaction builds upon previous knowledge
2. **Domain-Centric Design**: Model the problem space before the solution
3. **Constructive Challenge**: AI pushes back on assumptions and inconsistencies
4. **Minimal UI Complexity**: Optimize for utility over aesthetics
5. **Event-Sourced History**: Every decision and reflection is captured

## System Architecture

### High-Level Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│   Web Client    │────▶│   Backend    │────▶│     Zep     │
│   (React/HTMX)  │     │   (Python)   │     │  (Memory)   │
└─────────────────┘     └──────────────┘     └─────────────┘
                               │                      
                               ├──────────────────────┐
                               ▼                      ▼
                        ┌──────────────┐     ┌──────────────┐
                        │   Claude/    │     │    Notion    │
                        │    GPT-4     │     │     API      │
                        └──────────────┘     └──────────────┘
```

### Component Specifications

#### Backend Service (Python + FastAPI)
- **Responsibility**: Orchestration, domain logic, API gateway
- **Key Libraries**: 
  - FastAPI for HTTP + async support
  - Pydantic for data validation
  - SQLAlchemy for PostgreSQL
  - httpx for async HTTP clients
  - Langchain for LLM orchestration
  - zep-python for memory management

#### Memory Layer (Zep)
- **Configuration**: Cloud-hosted or self-hosted Docker
- **Usage Pattern**: 
  - Store all conversations with metadata
  - Semantic search for relevant memories
  - Session management per day/week
  - Fact extraction for user preferences

#### Database (PostgreSQL)
- **Purpose**: Structured data, event log, cached responses
- **Not for**: Conversation history (that's in Zep)

## Domain Model

```python
from dataclasses import dataclass
from datetime import datetime, date, time
from enum import Enum
from typing import Optional, List
from uuid import UUID

# Enums
class GoalStatus(Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    ABANDONED = "abandoned"

class TimeHorizon(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

# Core Entities
@dataclass
class User:
    id: UUID
    email: str
    preferences: dict
    created_at: datetime

@dataclass
class Goal:
    id: UUID
    title: str
    description: str
    time_horizon: TimeHorizon
    status: GoalStatus
    parent_goal_id: Optional[UUID]
    created_at: datetime
    completed_at: Optional[datetime]

@dataclass
class MorningContext:
    energy_level: int  # 1-5
    top_of_mind: List[str]
    intended_focus: str
    blockers: List[str]

@dataclass
class EveningReflection:
    actual_focus: str
    wins: List[str]
    challenges: List[str]
    tomorrow_intent: str
    energy_pattern: List[tuple[time, int]]

@dataclass
class DailySession:
    id: UUID
    date: date
    morning_context: Optional[MorningContext]
    evening_reflection: Optional[EveningReflection]
    decisions: List['Decision']
    energy_pattern: List[tuple[time, int]]

@dataclass
class Decision:
    id: UUID
    session_id: UUID
    question: str
    context: str
    options_considered: List[str]
    chosen_option: str
    reasoning: str
    outcome: Optional[str]
    timestamp: datetime

# Event Types (Event Sourcing)
@dataclass
class PlannerEvent:
    timestamp: datetime
    session_id: UUID

@dataclass
class GoalCreated(PlannerEvent):
    goal: Goal

@dataclass
class TaskCompleted(PlannerEvent):
    task_id: str
    reflection: str

@dataclass
class AssumptionChallenged(PlannerEvent):
    original: str
    challenge: str
    response: str

@dataclass
class PatternIdentified(PlannerEvent):
    pattern: str
    evidence: List[str]
```

## UI Design Specification

### Design Philosophy
- **Keyboard-first**: All actions accessible via keyboard shortcuts
- **Conversation-centric**: Chat is the primary interface
- **Minimal Chrome**: Focus on content, not UI elements
- **Information Density**: Show relevant context without overwhelming

### Layout Structure

```
┌────────────────────────────────────────────────────────────┐
│ Personal Planner             [Daily] [Decide] [Review]     │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────────────┐  ┌────────────────────────────┐ │
│  │                      │  │                            │ │
│  │   Context Sidebar    │  │      Main Chat Area       │ │
│  │                      │  │                            │ │
│  │  Today: Wednesday    │  │  ┌────────────────────┐   │ │
│  │  Energy: ████░░     │  │  │  Good morning!     │   │ │
│  │                      │  │  │  What's on your    │   │ │
│  │  Active Goals:       │  │  │  mind today?       │   │ │
│  │  • System Design     │  │  └────────────────────┘   │ │
│  │  • Scala Mastery     │  │                            │ │
│  │                      │  │  ┌────────────────────┐   │ │
│  │  Recent Decisions:   │  │  │ [User input box]   │   │ │
│  │  • Tech stack choice │  │  └────────────────────┘   │ │
│  │  • Architecture      │  │                            │ │
│  │                      │  │                            │ │
│  └──────────────────────┘  └────────────────────────────┘ │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### Page Specifications

#### 1. Daily Check-in (/daily)

**Morning Flow:**
```
┌─────────────────────────────────────────┐
│  Good morning! Let's set up your day.   │
│                                          │
│  Yesterday you wanted to: [shows intent] │
│  Your tasks for today: [Notion tasks]   │
│                                          │
│  How's your energy? [1-5 slider]        │
│  What's top of mind? [text input]       │
│                                          │
│  [AI generates contextual day plan]      │
└─────────────────────────────────────────┘
```

**Evening Flow:**
```
┌─────────────────────────────────────────┐
│  Evening reflection                      │
│                                          │
│  You planned to: [morning intent]        │
│  What actually happened: [text input]    │
│                                          │
│  Wins: [text input]                      │
│  Challenges: [text input]                │
│  Tomorrow's focus: [text input]          │
│                                          │
│  [AI synthesizes patterns & insights]    │
└─────────────────────────────────────────┘
```

#### 2. Decision Journal (/decide)

```
┌─────────────────────────────────────────┐
│  Decision Helper                         │
│                                          │
│  What decision are you facing?           │
│  [text input]                            │
│                                          │
│  Context/Stakes: [text area]             │
│                                          │
│  Options you're considering:             │
│  □ Option A: [text]                      │
│  □ Option B: [text]                      │
│  [+ Add option]                          │
│                                          │
│  [AI shows similar past decisions]       │
│  [AI challenges assumptions]             │
│  [AI suggests unconsidered options]      │
└─────────────────────────────────────────┐
```

#### 3. Pattern Review (/review)

```
┌─────────────────────────────────────────┐
│  Weekly Pattern Analysis                 │
│                                          │
│  Energy Patterns:                        │
│  [Heatmap of energy by day/time]         │
│                                          │
│  Decision Patterns:                      │
│  • You tend to overcommit on Mondays     │
│  • Your best work happens 2-4pm          │
│  • Decisions made when tired often wrong │
│                                          │
│  Goal Progress:                          │
│  [Progress bars for active goals]        │
│                                          │
│  Recurring Blockers:                     │
│  • "Waiting on others" appeared 3x       │
│  • Energy crashes after meetings         │
└─────────────────────────────────────────┘
```

### UI Interaction Patterns

#### Command Palette (CMD+K)
- Quick access to any function
- Fuzzy search across all commands
- Recent commands at top

#### Keyboard Shortcuts
- `CMD+K`: Command palette
- `CMD+Enter`: Submit current form
- `CMD+D`: Quick decision capture
- `CMD+R`: Daily reflection
- `ESC`: Close any modal/return to chat

#### Chat Commands
Users can type these directly in chat:
- `/decide [question]` - Start decision flow
- `/task [description]` - Quick task to Notion
- `/energy [1-5]` - Log energy level
- `/pattern` - Request pattern analysis
- `/challenge` - Request AI to challenge current thinking

## API Specification

### Core Endpoints

```python
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime

app = FastAPI()

# Request/Response Models
class CheckInRequest(BaseModel):
    energy_level: int  # 1-5
    top_of_mind: List[str]
    intended_focus: str
    blockers: Optional[List[str]] = []

class ChatMessage(BaseModel):
    content: str
    include_context: bool = True
    challenge_mode: bool = False

class DecisionRequest(BaseModel):
    question: str
    context: str
    options: List[str]
    
# API Routes
@app.post("/api/daily/checkin")
async def morning_checkin(request: CheckInRequest):
    """Morning check-in with context from previous days"""
    # 1. Get relevant memories from Zep
    # 2. Fetch today's tasks from Notion
    # 3. Generate contextual plan with LLM
    # 4. Store in Zep and PostgreSQL
    pass

@app.post("/api/daily/reflection")
async def evening_reflection(reflection: dict):
    """Evening reflection and pattern extraction"""
    pass

@app.post("/api/chat")
async def chat_with_context(message: ChatMessage):
    """Main chat interface with memory retrieval"""
    pass

@app.post("/api/decisions")
async def create_decision(decision: DecisionRequest):
    """Create and analyze a decision"""
    pass

@app.get("/api/patterns/weekly")
async def get_weekly_patterns():
    """Analyze patterns from the past week"""
    pass

@app.post("/api/notion/sync")
async def sync_notion_tasks():
    """Sync tasks with Notion"""
    pass
```

## Core Service Implementation

### Memory Service (Zep Integration)

```python
from zep_python import ZepClient, Memory, Message, SearchPayload
from typing import List, Optional
import os

class MemoryService:
    def __init__(self):
        self.client = ZepClient(
            api_key=os.getenv("ZEP_API_KEY"),
            api_url=os.getenv("ZEP_API_URL", "https://api.getzep.com")
        )
        self.user_id = "primary_user"  # Single user app
        
    async def add_interaction(self, user_input: str, ai_response: str, metadata: dict):
        """Store a conversation turn with metadata"""
        memory = Memory(
            messages=[
                Message(role="user", content=user_input),
                Message(role="assistant", content=ai_response)
            ],
            metadata=metadata
        )
        await self.client.aadd_memory(
            session_id=f"{self.user_id}_{metadata.get('date')}",
            memory=memory
        )
        
    async def search_memories(self, query: str, limit: int = 10) -> List[Memory]:
        """Search relevant memories"""
        search = SearchPayload(
            text=query,
            search_scope="messages",
            search_type="similarity"
        )
        results = await self.client.asearch_memory(
            session_id=self.user_id,
            search_payload=search,
            limit=limit
        )
        return results
        
    async def get_context_for_date(self, target_date: date) -> dict:
        """Get all context relevant for a specific date"""
        # Get memories from past week
        memories = await self.search_memories(
            f"goals plans energy {target_date.isoformat()}",
            limit=20
        )
        
        # Get user facts/preferences
        facts = await self.client.aget_memory(
            session_id=f"{self.user_id}_facts"
        )
        
        return {
            "recent_memories": memories,
            "user_facts": facts,
            "date": target_date
        }
```

### Planning Service (Main Business Logic)

```python
from typing import List, Optional
import anthropic
from notion_client import AsyncClient as NotionClient
from datetime import date, datetime

class PlannerService:
    def __init__(self, memory_service: MemoryService):
        self.memory = memory_service
        self.llm = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.notion = NotionClient(auth=os.getenv("NOTION_TOKEN"))
        
    async def morning_checkin(self, energy: int, top_of_mind: List[str], 
                              intended_focus: str) -> dict:
        """Process morning check-in with full context"""
        
        # 1. Get relevant context
        context = await self.memory.get_context_for_date(date.today())
        
        # 2. Get today's tasks from Notion
        tasks = await self._get_todays_tasks()
        
        # 3. Build prompt with context
        prompt = self._build_morning_prompt(
            context=context,
            energy=energy,
            top_of_mind=top_of_mind,
            intended_focus=intended_focus,
            tasks=tasks
        )
        
        # 4. Get AI response with constructive challenge
        response = await self.llm.messages.create(
            model="claude-3-opus-20240229",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        
        # 5. Store the interaction
        await self.memory.add_interaction(
            user_input=f"Morning: Energy {energy}, Focus: {intended_focus}",
            ai_response=response.content[0].text,
            metadata={
                "type": "morning_checkin",
                "date": date.today().isoformat(),
                "energy": energy
            }
        )
        
        return {
            "plan": response.content[0].text,
            "tasks": tasks,
            "energy": energy
        }
    
    async def challenge_assumption(self, statement: str) -> str:
        """AI challenges user's assumptions based on history"""
        
        # Search for contradictions or patterns
        relevant_memories = await self.memory.search_memories(statement)
        
        prompt = f"""Based on the user's history:
        {relevant_memories}
        
        The user just said: "{statement}"
        
        Challenge this constructively. Point out:
        1. Any contradictions with past decisions
        2. Patterns that suggest this might not work
        3. Unconsidered alternatives
        
        Be direct but supportive. The goal is deeper understanding."""
        
        response = await self.llm.messages.create(
            model="claude-3-opus-20240229",
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    async def _get_todays_tasks(self) -> List[dict]:
        """Fetch today's tasks from Notion"""
        # Notion API query for tasks
        # Implementation depends on your Notion schema
        pass
```

## Deployment & Infrastructure

### Docker Configuration

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Requirements File

```txt
# requirements.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
sqlalchemy==2.0.23
asyncpg==0.29.0
httpx==0.25.2
anthropic==0.7.7
zep-python==1.4.0
notion-client==2.2.0
redis==5.0.1
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
alembic==1.12.1
pytest==7.4.3
pytest-asyncio==0.21.1
```

### Environment Configuration

```bash
# .env file
DATABASE_URL=postgresql://user:pass@localhost:5432/planner
REDIS_URL=redis://localhost:6379

# API Keys
ZEP_API_KEY=your_zep_key
ANTHROPIC_API_KEY=your_claude_key
NOTION_TOKEN=your_notion_integration_token

# Optional: OpenAI as fallback
OPENAI_API_KEY=your_openai_key

# Security (generate with: openssl rand -hex 32)
SECRET_KEY=your_secret_key_here

# Deployment
ENVIRONMENT=development
LOG_LEVEL=INFO
```

## Quick Start Guide

### 1. Clone and Setup

```bash
# Create project
mkdir personal-planner && cd personal-planner

# Set up Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your API keys
```

### 2. Database Setup

```bash
# Run PostgreSQL (via Docker)
docker run -d \
  --name planner-db \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=planner \
  -p 5432:5432 \
  postgres:15

# Run migrations
alembic upgrade head
```

### 3. Start Development Server

```bash
# Run with auto-reload
uvicorn main:app --reload

# Or use Docker Compose
docker-compose up
```

### 4. Access the Application

- Web UI: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## MVP Features Checklist

### Phase 1 (Week 1)
- [ ] Basic FastAPI setup with health endpoint
- [ ] PostgreSQL connection and models
- [ ] Zep memory integration
- [ ] Simple HTML interface

### Phase 2 (Week 2)
- [ ] Morning check-in flow
- [ ] Evening reflection flow  
- [ ] Chat with memory context
- [ ] LLM integration (Claude/GPT-4)

### Phase 3 (Week 3)
- [ ] Notion task sync
- [ ] Decision journaling
- [ ] Assumption challenging
- [ ] Basic pattern detection

### Phase 4 (Week 4)
- [ ] Weekly pattern analysis
- [ ] Energy tracking visualization
- [ ] Goal management
- [ ] Command palette

### Phase 5 (Week 5)
- [ ] Error handling
- [ ] Performance optimization
- [ ] UI polish
- [ ] Deployment to production

## Monitoring & Maintenance

### Key Metrics to Track
- Daily active usage (are you using it?)
- Response times for API calls
- Memory retrieval relevance scores
- Decision outcome tracking
- Pattern identification accuracy

### Backup Strategy
```bash
# Daily PostgreSQL backup
pg_dump planner > backup_$(date +%Y%m%d).sql

# Zep backup (if self-hosted)
docker exec zep-container zep-backup > zep_backup.json
```
