# Multi-Agent System Guide

This guide explains the multi-agent system implemented in Alto using [Google ADK's Multi-Agent architecture](https://google.github.io/adk-docs/agents/multi-agents/).

## Architecture Overview

Alto uses the **Coordinator/Dispatcher Pattern** from ADK to intelligently route user requests to specialized agents:

```
┌─────────────────────────────────────┐
│      Coordinator Agent              │
│  (Analyzes intent & routes)         │
└──────────┬──────────────────────────┘
           │
           ├─────────────┬──────────────┐
           │             │              │
      ┌────▼────┐   ┌───▼──────┐        │
      │Calendar │   │    Q&A    │       │
      │ Manager │   │Specialist │       │
      └─────────┘   └───────────┘       │
```

## Agent Hierarchy

### 1. **Coordinator Agent** (Root Agent)
- **Role**: Main entry point that analyzes user intent
- **Responsibility**: Routes requests to the appropriate specialist
- **Decision Logic**: 
  - Detects if user is asking about THEIR data → routes to Calendar Manager
  - Detects if user is asking general questions → routes to Q&A Specialist
  - Uses ADK's `transfer_to_agent` mechanism for routing

### 2. **Calendar Manager** (Specialist Agent)
- **Role**: Transaction analysis and calendar optimization
- **Capabilities**:
  - Analyzes transaction history and patterns
  - Identifies recurring payments
  - Suggests optimal payment dates
  - Calculates buffer impacts
  - Optimizes credit utilization
- **When to use**: User provides transaction data or asks about THEIR specific payments

### 3. **Q&A Specialist** (Specialist Agent)
- **Role**: General financial education and advice
- **Capabilities**:
  - Explains financial concepts
  - Answers budgeting questions
  - Provides general money management strategies
  - Educational guidance
- **When to use**: User asks "what is", "how does", or general knowledge questions

## How It Works

### Agent Communication Flow

1. **User sends a message** → Goes to Coordinator
2. **Coordinator analyzes intent** using its reasoning capabilities
3. **Coordinator uses `transfer_to_agent`** to route to the appropriate specialist
4. **Specialist handles the request** and returns the response
5. **Response flows back** through the coordinator to the user

### Example Routing Scenarios

#### Scenario 1: Transaction Analysis
```
User: "Can you analyze my September transactions and tell me when I should pay my rent?"

Coordinator Decision:
- Detects: "my transactions", "when should I pay"
- Action: transfer_to_agent(calendar_manager)
- Result: Calendar Manager analyzes data and provides payment recommendations
```

#### Scenario 2: General Question
```
User: "What is credit utilization and how does it affect my credit score?"

Coordinator Decision:
- Detects: "What is", educational question, no specific data
- Action: transfer_to_agent(qa_specialist)
- Result: Q&A Specialist explains the concept
```

#### Scenario 3: Payment Strategy
```
User: "I have a $1200 rent payment on the 15th. Should I move it earlier?"

Coordinator Decision:
- Detects: Specific payment, "should I move it", involves their data
- Action: transfer_to_agent(calendar_manager)
- Result: Calendar Manager analyzes buffer and provides recommendation
```

## Implementation Details

### Agent Initialization

The agents are initialized in `app/agent.py`:

```python
# Create specialist agents
calendar_agent = create_calendar_agent()
qa_agent = create_qa_agent()

# Create coordinator with sub_agents
root_agent = create_coordinator_agent()
root_agent.sub_agents = [calendar_agent, qa_agent]
```

### Agent Hierarchy Setup

ADK automatically establishes parent-child relationships:
- `calendar_agent.parent_agent` → `coordinator`
- `qa_agent.parent_agent` → `coordinator`

### Routing Mechanism

The coordinator uses ADK's **LLM-Driven Delegation** pattern:
- Analyzes user intent through its instruction
- Uses `transfer_to_agent` to delegate to specialists
- Specialists have access to shared session state
- Each agent can use its own planner and thinking config

## ADK Primitives Used

### 1. Agent Hierarchy
```python
root_agent.sub_agents = [calendar_agent, qa_agent]
```
Establishes parent-child relationships automatically.

### 2. LLM-Driven Delegation
The coordinator's instruction includes logic to:
- Analyze user intent
- Choose the appropriate specialist
- Transfer control using ADK's transfer mechanism

### 3. Shared Session State
All agents share the same session:
- `session.state` accessible to all agents
- Transaction data can be stored and accessed
- Conversation history maintained across agents

## Benefits of This Architecture

### 🎯 **Specialization**
- Each agent focuses on its specific domain
- More targeted and accurate responses
- Easier to optimize individual agents

### 🔧 **Maintainability**
- Clean separation of concerns
- Easy to update one agent without affecting others
- Clear responsibility boundaries

### 🔄 **Reusability**
- Specialist agents can be used independently
- Can add new specialists without changing existing ones
- Modular architecture

### 📈 **Scalability**
- Easy to add new specialist agents
- Can create sub-hierarchies if needed
- Supports complex workflows

## Adding New Agents

To add a new specialist agent:

1. **Create the agent file** in `app/agents/`:
```python
# app/agents/new_specialist.py
def create_new_specialist() -> LlmAgent:
    return LlmAgent(
        name="new_specialist",
        model=config.model,
        description="What this specialist does",
        instruction="Detailed instructions..."
    )
```

2. **Update the coordinator** to know about the new agent:
```python
# In coordinator_agent.py instruction
3. **new_specialist** - Use when the user wants to:
   - Specific use case 1
   - Specific use case 2
```

3. **Add to the hierarchy** in `app/agent.py`:
```python
new_agent = create_new_specialist()
root_agent.sub_agents = [calendar_agent, qa_agent, new_agent]
```

## Testing the System

### Test Calendar Routing
```bash
# Start the backend
make dev-backend

# Test with transaction data
curl -X POST http://localhost:8000/api/chat \
  -d '{"message": "Analyze my rent payment on the 15th", "user_id": "test"}'
```

### Test Q&A Routing
```bash
# General question
curl -X POST http://localhost:8000/api/chat \
  -d '{"message": "What is an emergency fund?", "user_id": "test"}'
```

### Monitor Routing Decisions
Check the logs to see which agent handled the request:
```
🤖 Multi-Agent System Initialized:
  Root Agent: coordinator
  Sub-Agents: ['calendar_manager', 'qa_specialist']
```

## Related Documentation

- [ADK Multi-Agent Systems](https://google.github.io/adk-docs/agents/multi-agents/)
- [ADK LLM Agents](https://google.github.io/adk-docs/agents/llm-agents/)
- [ADK Session & State](https://google.github.io/adk-docs/sessions-memory/session/)

## Troubleshooting

### Agent Not Routing Correctly
- Check coordinator's instruction for clear routing rules
- Verify sub_agents are properly assigned
- Check logs for transfer_to_agent calls

### Specialist Not Responding
- Verify agent is in the sub_agents list
- Check agent's instruction for clarity
- Ensure model has proper access

### Session State Issues
- Verify session is being passed correctly
- Check state keys match between agents
- Use `session.state` for shared data

## Future Enhancements

Potential additions to the multi-agent system:

1. **Budget Planning Agent** - Long-term financial planning
2. **Debt Management Agent** - Strategies for paying off debt
3. **Savings Goal Agent** - Tracking and optimizing savings goals
4. **Sequential Workflows** - Chain multiple agents for complex tasks
5. **Parallel Agents** - Process multiple analyses simultaneously

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    User Request                          │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│              Coordinator Agent (Root)                    │
│  ┌────────────────────────────────────────────────┐    │
│  │ • Analyzes intent                               │    │
│  │ • Decides routing                               │    │
│  │ • Uses transfer_to_agent                        │    │
│  └────────────────────────────────────────────────┘    │
└───────────────┬───────────────────┬─────────────────────┘
                │                   │
       ┌────────▼────────┐  ┌──────▼──────────┐
       │ Calendar Manager │  │  Q&A Specialist  │
       ├─────────────────┤  ├─────────────────┤
       │ • Transaction    │  │ • Financial ed. │
       │   analysis       │  │ • Concept expl. │
       │ • Payment opt.   │  │ • Best practices│
       │ • Buffer calc.   │  │ • Strategies    │
       └──────────────────┘  └─────────────────┘
                │                   │
                └─────────┬─────────┘
                          ▼
              ┌───────────────────────┐
              │   Shared Session      │
              │   • State             │
              │   • History           │
              │   • Context           │
              └───────────────────────┘
```

