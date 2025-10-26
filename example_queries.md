# Example Queries for Multi-Agent System

This document provides example queries to test the multi-agent routing system.

## Calendar Management Queries

These queries should route to the **Calendar Manager** agent:

### Transaction Analysis
```
"Can you analyze my September transactions and tell me if I should adjust any payment dates?"
```

### Payment Timing
```
"I have a $1200 rent payment scheduled for the 15th. Should I move it earlier based on my cashflow?"
```

### Budget Optimization
```
"Looking at my transaction history, when is the best time to make my credit card payment to optimize my utilization?"
```

### Spending Patterns
```
"What patterns do you see in my spending from the transaction data?"
```

### Buffer Protection
```
"My account balance is low. Can you suggest which payments I should reschedule to avoid overdrafts?"
```

### Recurring Payments
```
"Analyze my recurring subscriptions and tell me which ones are most impacting my cashflow."
```

## Q&A / Educational Queries

These queries should route to the **Q&A Specialist** agent:

### Financial Concepts
```
"What is credit utilization and how does it affect my credit score?"
```

### Budgeting Strategies
```
"What are some effective budgeting methods I can use to track my spending?"
```

### Savings Goals
```
"How should I approach building an emergency fund? What's a good target amount?"
```

### Credit Management
```
"Why is it important to keep credit utilization below 30%?"
```

### Payment Strategies
```
"What's the difference between the avalanche and snowball methods for paying off debt?"
```

### Financial Planning
```
"How do I calculate how much I should save for retirement?"
```

### Best Practices
```
"What are some best practices for managing multiple credit cards?"
```

## Complex Scenarios

### Mixed Intent (Should Route to Calendar Manager)
```
"I want to avoid overdrafts. Here's my transaction data for September: [data]. What should I do?"
```
*Routes to Calendar Manager because transaction data is provided.*

### Follow-up Questions
```
User: "What is credit utilization?"
AI: [Q&A Specialist explains]

User: "Based on my transactions, when should I pay my credit card?"
AI: [Routes to Calendar Manager for specific analysis]
```

## Testing with Transaction Data

### Sample Transaction Data Format
```json
{
  "message": "Analyze these transactions and optimize my payment schedule",
  "transaction_data": {
    "current_balance": 1342.55,
    "transactions": [
      {
        "date": "2023-09-01",
        "amount": 2400,
        "name": "Paycheck - ACME Corp",
        "type": "income"
      },
      {
        "date": "2023-09-15",
        "amount": 1200,
        "name": "Rent Payment",
        "type": "expense"
      },
      {
        "date": "2023-09-10",
        "amount": 78.25,
        "name": "Electric Bill",
        "type": "expense"
      }
    ]
  }
}
```

## Expected Routing Behavior

| Query Type | Example Keywords | Routes To |
|-----------|------------------|-----------|
| Transaction analysis | "my transactions", "analyze my", "my payments" | Calendar Manager |
| Payment scheduling | "when should I pay", "should I move", "reschedule" | Calendar Manager |
| Financial education | "what is", "how does", "explain" | Q&A Specialist |
| Best practices | "best way to", "strategies for", "how to" | Q&A Specialist |
| Budget help | "budget method", "track spending", "saving tips" | Q&A Specialist |
| Data-driven advice | "based on my data", "looking at my", "my balance" | Calendar Manager |

## Testing via Frontend

1. **Start the backend:**
   ```bash
   make dev-backend
   ```

2. **Start the frontend:**
   ```bash
   make dev-frontend
   ```

3. **Open browser:** Navigate to `http://localhost:3000`

4. **Try queries:** Use the example queries above in the chat interface

5. **Check routing:** Look at backend logs to see which agent handled each request:
   ```
   🤖 Multi-Agent System Initialized:
     Root Agent: coordinator
     Sub-Agents: ['calendar_manager', 'qa_specialist']
   ```

## Testing via API

### Calendar Management Request
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Analyze my rent payment on the 15th and suggest the best timing",
    "user_id": "test_user",
    "session_id": "test_session"
  }'
```

### Q&A Request
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is an emergency fund and how much should I save?",
    "user_id": "test_user",
    "session_id": "test_session"
  }'
```

## Observing Agent Behavior

### Backend Logs
Watch for these indicators in the logs:

```
✅ Routing to: calendar_manager
   Reason: User provided transaction data

✅ Routing to: qa_specialist  
   Reason: Educational question about financial concepts
```

### Response Structure
- **Calendar Manager** responses include:
  - Specific dates and amounts
  - Buffer calculations
  - Payment recommendations
  - Risk assessments

- **Q&A Specialist** responses include:
  - Conceptual explanations
  - Best practice advice
  - Step-by-step guidance
  - Educational content

## Tips for Testing

1. **Start with clear intent:** Use unambiguous queries first
2. **Test edge cases:** Try queries that could go either way
3. **Use transaction data:** Include actual data for calendar queries
4. **Check session state:** Verify context is maintained across messages
5. **Monitor logs:** Watch backend output for routing decisions

## Common Patterns

### Pattern 1: Research → Apply
```
Step 1: "What is credit utilization?" (Q&A)
Step 2: "Now analyze my credit card transactions and optimize my payment timing" (Calendar)
```

### Pattern 2: Data Analysis → Deeper Questions
```
Step 1: "Analyze my September transactions" (Calendar)
Step 2: "Why is it important to maintain a buffer?" (Q&A)
```

### Pattern 3: Multiple Data Points
```
"I have rent ($1200 on 15th), car payment ($450 on 10th), and utilities ($200 on 5th). 
My paycheck ($2400) comes on the 1st. How should I optimize this schedule?"
```
*Should route to Calendar Manager due to specific amounts and dates.*

