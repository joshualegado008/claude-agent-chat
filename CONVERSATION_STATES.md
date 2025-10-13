# Conversation State Management

This document describes the lifecycle and state management of conversations in the Claude Agent Chat system.

## Overview

Conversations progress through different states as users interact with them. The system uses four distinct states to track conversation status: `active`, `paused`, `completed`, and `archived`.

## State Definitions

### 1. **active**
A conversation that is in progress or can be continued.

**Characteristics:**
- New conversations start with this status
- Can be resumed at any time
- No user-initiated interruption
- Conversation hasn't reached max_turns limit

**Transitions to:**
- `paused` - User explicitly pauses or WebSocket disconnects
- `completed` - Reaches max_turns or user stops
- `archived` - User archives for organization

**UI Display:**
- **Badge**: Yellow/amber with "active" text
- **Homepage**: Shows "active" badge
- **Conversation Page**: "Continue Conversation" button

---

### 2. **paused**
A conversation that was explicitly paused by the user or disconnected mid-stream.

**Characteristics:**
- User clicked "Pause" button
- OR WebSocket disconnected unexpectedly (browser closed, network issue)
- Can be resumed from the exact point it was paused
- Intentional temporary suspension

**Transitions to:**
- `active` - User clicks "Resume" button
- `completed` - User clicks "Stop" or reaches max_turns after resuming
- `archived` - User archives for organization

**UI Display:**
- **Badge**: Blue with "paused" text
- **Homepage**: Shows "paused" badge in blue
- **Conversation Page**: "This conversation is paused" with "Resume Conversation" button

**Code Locations:**
- Web UI pause: `web/backend/websocket_handler.py:423-431`
- Terminal interrupt: `coordinator_with_memory.py:724-726`
- WebSocket disconnect cleanup: `web/backend/websocket_handler.py:544-547`

---

### 3. **completed**
A conversation that has finished either naturally or by user action.

**Characteristics:**
- Reached max_turns limit (typically 20 turns)
- OR user explicitly clicked "Stop" button
- Cannot be resumed (terminal state)
- All data preserved for review

**Transitions to:**
- `archived` - User archives for organization (only state change possible)

**UI Display:**
- **Badge**: Green with "completed" text
- **Homepage**: Shows "completed" badge in green
- **Conversation Page**: "Conversation Complete" message

**Code Locations:**
- Max turns reached: `web/backend/websocket_handler.py:540-543`
- User clicks Stop: `web/backend/websocket_handler.py:443-453`
- Natural completion: `web/backend/websocket_handler.py:401-409`

---

### 4. **archived**
A conversation that has been archived by the user for organizational purposes.

**Characteristics:**
- Hidden from main conversation list by default
- Preserves all conversation data
- Can be un-archived if needed
- Currently not fully implemented in UI

**Transitions to:**
- `active` or `completed` - Un-archive action (future feature)

---

## State Transition Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         NEW CONVERSATION                         │
│                         (status='active')                        │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │         RUNNING              │
        │       (status='active')      │
        └─┬──────────────────────────┬─┘
          │                          │
          │ User clicks Pause        │ Reaches max_turns
          │ OR WebSocket disconnect  │ OR User clicks Stop
          ▼                          ▼
┌──────────────────┐         ┌─────────────────────┐
│     PAUSED       │         │     COMPLETED       │
│ (status='paused')│         │  (status='completed'│
└─┬────────────────┘         └──────────┬──────────┘
  │                                     │
  │ User clicks Resume                  │
  │                                     │
  └───────┐             ┌──────────────┘
          │             │
          ▼             ▼
    ┌────────────────────────┐
    │  Resume & Continue     │
    │   (status='active')    │
    └──────────┬─────────────┘
               │
               │ Reaches max_turns
               │ OR User clicks Stop
               ▼
       ┌───────────────┐
       │   COMPLETED   │
       └───────────────┘
```

## Key Behavioral Rules

### Pause vs Stop

| Action | Database Status | Can Resume? | User Intent |
|--------|----------------|-------------|-------------|
| **Pause** | `paused` | ✅ Yes | Temporary break, will resume later |
| **Stop** | `completed` | ❌ No | Permanent end, done with conversation |

### Status Priority in Cleanup (WebSocket disconnect)

When a WebSocket connection closes, the cleanup logic follows this priority:

1. **Already stopped** → Don't change status (already finalized as `completed`)
2. **Reached max_turns** → Set to `completed`
3. **User paused** → Keep as `paused` (don't override)
4. **Mid-conversation disconnect** → Set to `paused` (can resume later)

### Resume Behavior

Both `active` and `paused` conversations show a "Continue/Resume" button:

- **active**: "Continue Conversation" (standard continuation)
- **paused**: "Resume Conversation" (explicitly resuming from pause)

## UI Badge Styles

### Homepage (`web/frontend/app/page.tsx:153-165`)

```typescript
// Completed - Green
bg-green-900/50 text-green-300 border border-green-700

// Paused - Blue
bg-blue-900/50 text-blue-300 border border-blue-700

// Active - Yellow
bg-yellow-900/50 text-yellow-300 border border-yellow-700
```

### Badge Text

- `completed` → "completed"
- `paused` → "paused"
- `active` → "active"

## Database Schema

**Table:** `conversations`
**Column:** `status` (VARCHAR(20))
**Constraint:** `CHECK (status IN ('active', 'paused', 'completed', 'archived'))`

**Migration:** See `migrations/002_add_paused_status.sql`

## Implementation Files

### Backend
- `init.sql:16-20` - Database schema and constraint
- `web/backend/websocket_handler.py:423-551` - Pause/Stop/Cleanup logic
- `coordinator_with_memory.py:725` - Terminal interrupt handling
- `conversation_manager_persistent.py:277-289` - Status finalization

### Frontend
- `web/frontend/app/page.tsx:153-165` - Homepage badges
- `web/frontend/app/conversation/[id]/page.tsx:112-113, 194-216` - Continue button logic
- `web/frontend/components/ConversationControls.tsx:83-91` - Pause/Stop UI

## Testing Scenarios

### Test 1: User Pauses Conversation
1. Start conversation
2. Click "Pause" button
3. Check database: `status = 'paused'`
4. Reload homepage: Blue "paused" badge
5. Open conversation: "Resume Conversation" button

### Test 2: User Stops Conversation
1. Start conversation
2. Click "Stop" button
3. Check database: `status = 'completed'`
4. Reload homepage: Green "completed" badge
5. Open conversation: "Conversation Complete" message, no resume button

### Test 3: Browser Closes Mid-Conversation
1. Start conversation
2. Close browser tab (WebSocket disconnects)
3. Check database: `status = 'paused'`
4. Reload homepage: Blue "paused" badge
5. Open conversation: "Resume Conversation" button works

### Test 4: Conversation Reaches Max Turns
1. Let conversation run to 20 turns
2. Check database: `status = 'completed'`
3. Homepage: Green "completed" badge
4. Cannot resume

## Migration Instructions

To apply the 'paused' status to an existing database:

```bash
# Option 1: Using psql
psql -U agent_user -d agent_conversations -f migrations/002_add_paused_status.sql

# Option 2: Using Docker
docker exec -i agent-chat-postgres psql -U agent_user -d agent_conversations < migrations/002_add_paused_status.sql

# Option 3: Restart database (applies init.sql automatically)
docker-compose down
docker-compose up -d
```

## Troubleshooting

### Q: Old conversations show "active" but can't be resumed
**A:** These are likely conversations that were interrupted before the 'paused' status was added. They can be resumed normally—the "active" status is correct for continuable conversations.

### Q: Conversation shows "paused" but I didn't pause it
**A:** This happens when the browser/WebSocket disconnected unexpectedly (network issue, browser crash, etc.). This is intentional—the conversation is marked as paused so you can resume it.

### Q: Can I change a conversation from 'completed' back to 'active'?
**A:** No, 'completed' is a terminal state. The conversation reached max_turns or was explicitly stopped by the user. To continue the discussion, start a new conversation.

## Future Enhancements

1. **Archive functionality**: Add UI to archive/un-archive conversations
2. **Status history**: Track when conversations change status
3. **Auto-pause timeout**: Automatically pause conversations inactive for >30 minutes
4. **Batch status updates**: UI to mark multiple conversations as archived
5. **Status filters**: Filter homepage by status (show only paused, etc.)
