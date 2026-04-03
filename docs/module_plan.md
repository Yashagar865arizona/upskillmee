# MessageService Module Breakdown Plan

## Current Issues
- `message_service.py` has grown too large (1299 lines)
- Complex indentation and nesting makes it error-prone
- Difficult to maintain and debug

## Proposed Module Split

### 1. Core Message Service (`message_service.py`)
- Main class and initialization
- Core message handling
- Database operations for messages
- Basic user context management

### 2. Learning Plan Service (`learning_plan_service.py`)
- Extraction and parsing of learning plans
- Validation of plan structure
- Plan formatting and conversion

### 3. AI Integration Service (`ai_integration_service.py`)
- AI API client setup
- Model selection logic
- Response processing
- Timeout and error handling

### 4. Context Management (`context_service.py`) 
- Chat history handling
- User snapshot creation
- Profile information extraction
- Metric calculations

### 5. WebSocket Handler (`websocket_handler.py`)
- WebSocket message processing
- Connection management
- Response formatting

## Implementation Plan

1. Create new module files
2. Extract related functions to each module
3. Ensure proper imports between modules
4. Update main app imports
5. Test each component independently

## Specific Functions to Move

### To `learning_plan_service.py`:
- `_extract_learning_plan`
- Plan-related parts of `process_message`
- `_clean_json_string`
- `_should_create_plan`

### To `ai_integration_service.py`:
- `_get_ai_response`
- `_get_system_prompt`
- `_convert_to_chat_completion_messages`

### To `context_service.py`:
- `_get_user_snapshot`
- `_get_relevant_history`
- `_prepare_context_with_history`
- `_get_career_path`
- `_get_profile_interests`

### To `websocket_handler.py`:
- `handle_websocket_message`
- `handle_message`

This breakdown maintains functionality while making each component more manageable and testable. 