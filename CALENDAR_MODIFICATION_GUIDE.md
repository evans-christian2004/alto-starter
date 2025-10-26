# Calendar Modification System Guide

## Overview

The Alto Financial Assistant now includes an intelligent calendar modification system that allows the AI agent to optimize payment schedules and suggest planned transactions to improve your cashflow.

## How It Works

### 1. AI-Powered Calendar Optimization

When you ask Alto to optimize your payment schedule, the agent:
- Analyzes your transaction data
- Identifies problematic timing (overdraft risks, high credit utilization)
- Suggests moving payments to better dates
- Can add planned future transactions
- Provides clear reasoning for each recommendation

### 2. Visual Indicators

The calendar displays modifications with clear visual cues:

#### 🔵 **Moved Transactions (Cyan)**
- Days with AI-optimized transactions show a cyan background
- Moved transactions have a cyan highlight and an arrow icon (→)
- Click on a date to see the original date and optimization reason

#### 💜 **Planned Transactions (Purple)**
- Future planned transactions show a purple background
- Planned transactions have a purple highlight and sparkle icon (✨)
- Marked with 📅 emoji for easy identification

### 3. Legend
When modifications exist, a legend appears in the calendar header showing:
- Icon meanings
- Count of moved vs planned transactions

## Using the System

### Example Queries

**Basic Calendar Optimization:**
```
"Can you optimize my payment schedule to avoid overdrafts?"
```

**Specific Concerns:**
```
"I'm worried about overdrafting. Can you suggest a better payment schedule?"
```

**Credit Utilization:**
```
"Help me plan my credit card payments to keep utilization under 30%"
```

**Recurring Payments:**
```
"Analyze my subscriptions and suggest better payment timing"
```

### What the Agent Can Do

1. **Move Existing Transactions**
   - Rent payments
   - Utility bills
   - Subscription payments
   - Credit card payments
   
2. **Add Planned Transactions**
   - Future savings transfers
   - Upcoming bills
   - Planned purchases
   - Credit card payments

3. **Provide Recommendations**
   - Buffer calculations (balance after payments)
   - Overdraft risk analysis
   - Credit utilization impact
   - Optimal payment dates

## Technical Details

### Agent Tools

The agent has access to these calendar modification tools:

1. `move_transaction()` - Suggest moving a payment to a new date
2. `add_planned_transaction()` - Add a planned future payment
3. `get_calendar_modifications()` - See all current modifications
4. `clear_calendar_modifications()` - Reset calendar to original dates

### Data Storage

- Modifications are stored in `app/data/calendar_modifications.json`
- The frontend polls for updates every 3 seconds
- Each modification includes reasoning from the AI

### Calendar Display

The calendar automatically:
- Applies modifications to the displayed dates
- Shows visual indicators (colors, icons, badges)
- Maintains original date information
- Displays AI reasoning when you click on a modified transaction

## Example Workflow

1. **User asks:** "Can you optimize my payment schedule?"

2. **Agent responds:**
   - Calls `get_user_transactions()` to analyze data
   - Identifies issues (e.g., rent payment on 15th risks overdraft)
   - Uses `move_transaction()` to suggest improvements
   - Explains the reasoning

3. **Calendar updates:**
   - Transactions move to suggested dates
   - Days with changes show cyan highlighting
   - Legend shows count of modifications

4. **User reviews:**
   - Clicks on modified dates to see details
   - Reads AI reasoning for each change
   - Can ask follow-up questions

## Resetting the Calendar

To clear all modifications and return to original dates:
```
"Clear all calendar modifications"
```

Or delete the file:
```bash
rm app/data/calendar_modifications.json
```

## API Endpoint

The frontend fetches modifications from:
```
GET /api/calendar-modifications
```

Returns:
```json
{
  "modifications": [
    {
      "modification_id": "mod_1",
      "transaction_id": "txn_010",
      "merchant_name": "Avalon Apartments",
      "original_date": "2023-09-15",
      "new_date": "2023-09-05",
      "amount": 1200.00,
      "reason": "Moving rent payment earlier to avoid overdraft risk after utilities payment",
      "status": "suggested"
    }
  ],
  "last_updated": "2024-01-20T10:30:00.000Z"
}
```

## Best Practices

1. **Ask Specific Questions**: "Help me avoid overdrafts in September" is better than "Optimize my calendar"

2. **Review Modifications**: Click on moved transactions to understand the reasoning

3. **Iterate**: Ask follow-up questions like "What if I move my rent payment to the 1st instead?"

4. **Clear Old Modifications**: Reset the calendar when starting a new analysis

## Future Enhancements

Potential future features:
- User approval flow (approve/reject modifications)
- Modification history tracking
- Calendar export to external calendar apps
- Automated alerts when risky dates are detected
- Multi-month optimization view

## Troubleshooting

**Modifications not showing?**
- Check that the backend is running (`make dev-backend`)
- Verify the modifications file exists: `app/data/calendar_modifications.json`
- Check browser console for API errors

**Agent not using tools?**
- Make sure you're asking about transactions/payments
- Try explicitly asking: "Use my transaction data to optimize my calendar"
- Check backend logs for tool execution

**Calendar not updating?**
- The frontend polls every 3 seconds
- Refresh the page to force an update
- Check that the API endpoint is accessible: `http://localhost:3000/api/calendar-modifications`

