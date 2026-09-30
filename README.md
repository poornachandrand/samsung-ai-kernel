\# Samsung AI Kernel



\## Overview



Samsung AI Kernel is an event-driven AI execution kernel designed to connect an AI reasoning layer with reliable, observable tool execution.



The system provides:



\- Task lifecycle management

\- Event-driven execution

\- Tool orchestration

\- Retry and recovery

\- Checkpointing

\- Cancellation

\- User correction and interruption handling

\- Duplicate and stale-result protection

\- Multi-tool execution

\- Failure isolation

\- Gemini integration

\- LiveKit realtime agent integration



The project is designed so that the AI model can decide what should happen while the Kernel controls how tool execution is performed safely and consistently.



\## Architecture



```text

&#x20;                   ┌─────────────────────────┐

&#x20;                   │        LiveKit          │

&#x20;                   │   Room / Participant    │

&#x20;                   └────────────┬────────────┘

&#x20;                                │

&#x20;                                ▼

&#x20;                   ┌─────────────────────────┐

&#x20;                   │  GeminiLiveKitLLM       │

&#x20;                   │       Adapter           │

&#x20;                   └────────────┬────────────┘

&#x20;                                │

&#x20;                                ▼

&#x20;                   ┌─────────────────────────┐

&#x20;                   │    Gemini Kernel        │

&#x20;                   │   GeminiKernelBridge    │

&#x20;                   └────────────┬────────────┘

&#x20;                                │

&#x20;                                ▼

&#x20;                   ┌─────────────────────────┐

&#x20;                   │      Samsung Kernel     │

&#x20;                   │                         │

&#x20;                   │ Tasks                   │

&#x20;                   │ Events                  │

&#x20;                   │ Dispatcher              │

&#x20;                   │ Retry / Recovery        │

&#x20;                   │ Checkpoints             │

&#x20;                   │ Cancellation            │

&#x20;                   │ Result validation       │

&#x20;                   └────────────┬────────────┘

&#x20;                                │

&#x20;               ┌────────────────┼────────────────┐

&#x20;               ▼                ▼                ▼

&#x20;         Smart Home       Flight Search     Hotel Search



\## Core Kernel



The main execution engine is implemented in `kernel.py`.



The Kernel manages:



1\. Task creation

2\. Task identity

3\. Tool execution

4\. Retry behavior

5\. Event emission

6\. Checkpoints

7\. Cancellation

8\. User correction

9\. Result validation

10\. Task isolation



The Kernel remains the authoritative execution layer.



\## Event System



`kernel\_events.py` defines the event model.



Important lifecycle events include:



\- `TASK\_STARTED`

\- `TOOL\_STARTED`

\- `TOOL\_COMPLETED`

\- `TOOL\_FAILED`

\- `CHECKPOINT\_SAVED`

\- `TASK\_CANCELLED`

\- `TASK\_COMPLETED`

\- `TASK\_FAILED`



`event\_dispatcher.py` routes events to registered handlers.



Both synchronous and asynchronous subscribers are supported.



Handler failures are isolated so that one subscriber cannot break the Kernel event pipeline.



\## Retry and Recovery



Retryable tool failures are automatically retried by the Kernel.



Example:



```text

Attempt 1 → temporary failure

Attempt 2 → temporary failure

Attempt 3 → success

```



The regression suite verifies that:



\- Retryable failures are recorded

\- Retry attempts generate the appropriate events

\- Successful recovery produces the correct final result

\- Task identity remains consistent



\---



\## Checkpointing



Multi-step workflows can save checkpoints after successful steps.



Example:



```text

Task

&#x20;│

&#x20;├── Flight Search

&#x20;│      └── checkpoint: flight\_search\_complete

&#x20;│

&#x20;└── Hotel Search

&#x20;       └── checkpoint: hotel\_search\_complete

```



Checkpoint data stores workflow progress and the output required for inspection or continuation.



\---



\## Cancellation and User Correction



The Kernel supports cancellation of the current task and user correction/interruption.



Example:



```text

Original request

&#x20;     │

&#x20;     ▼

Original task

&#x20;     │

&#x20;     ▼

TASK\_CANCELLED

&#x20;     │

&#x20;     ▼

Corrected request

&#x20;     │

&#x20;     ▼

New task

&#x20;     │

&#x20;     ▼

TASK\_COMPLETED

```



The corrected task receives a new task ID.



The dispatcher regression tests verify cancellation and correction event propagation.



\---



\## Duplicate and Late Result Protection



The Kernel protects the current task from stale results.



If an older task produces a late result after a newer task becomes active, the stale result cannot replace the current task's state.



This provides task isolation across interrupted or overlapping workflows.



\---



\## Multi-Tool Execution



The Kernel supports multiple tools within the same task.



\### Smart Home



```text

smart\_home

```



Controls or queries a smart-home device.



\### Flight Search



```text

flight\_search

```



Searches for flights between an origin and destination.



\### Hotel Search



```text

hotel\_search

```



Searches for hotels in a destination.



The internal Kernel also contains:



```text

flaky\_flight\_search

```



This tool intentionally produces temporary retryable failures and is used to verify the Kernel's recovery behavior.



\---



\## Failure Isolation



Independent tool failures are isolated.



For example:



```text

Task

&#x20;├── Flight Search → SUCCESS

&#x20;└── Hotel Search  → SUCCESS

```



A failure in one independent tool does not automatically invalidate the other tool execution.



Example:



```text

Task

&#x20;├── Invalid Smart Home request → FAILURE

&#x20;└── Hotel Search               → SUCCESS

```



The regression suite verifies that the valid operation can still complete after an independent tool failure.



\---



\## Gemini Integration



`gemini\_kernel.py` provides the Gemini-to-Kernel bridge.



The bridge is responsible for:



\- Sending model requests

\- Providing tool definitions

\- Handling model responses

\- Detecting function calls

\- Converting model responses into Kernel-compatible structures

\- Supporting model recovery/fallback behavior



The configured Gemini model is:



```text

gemini-3.8-flash

```



The LiveKit Gemini adapter is implemented in:



```text

livekit\_gemini\_adapter.py

```



\---



\## LiveKit Integration



LiveKit provides the realtime agent layer.



Main integration files:



```text

livekit\_agent.py

livekit\_gemini\_adapter.py

livekit\_kernel\_tools.py

dispatch\_livekit\_agent.py

```



The LiveKit agent:



1\. Receives a LiveKit job

2\. Connects to the LiveKit room

3\. Creates the Gemini Kernel bridge

4\. Exposes Kernel-backed tools to LiveKit

5\. Starts an `AgentSession`

6\. Connects the session to the Kernel-backed tools



The verified tool execution path is:



```text

LiveKit

&#x20;  ↓

AgentSession

&#x20;  ↓

LiveKit Kernel Tool

&#x20;  ↓

Samsung Kernel

&#x20;  ↓

Tool

&#x20;  ↓

ToolResult

```



\---



\## LiveKit Tools



The LiveKit layer exposes:



```text

smart\_home

flight\_search

hotel\_search

```



All actual tool execution remains inside the Samsung Kernel.



This keeps the Kernel as the central execution authority rather than duplicating reliability-critical business logic inside the LiveKit layer.



\---



\## Extensions



The `extensions/` directory contains additional capability modules:



```text

extensions/

├── doctor\_appointment.py

├── employee\_planner.py

├── food\_ordering.py

├── kitchen\_assistant.py

├── smart\_home.py

└── study\_helper.py

```



These modules are kept separate from the core Kernel and tool execution layer.



\---



\## Project Structure



```text

SAMSUNG/

│

├── kernel.py

├── kernel\_events.py

├── event\_dispatcher.py

│

├── tool\_base.py

├── tool\_interface.py

├── tools.py

├── flight\_search.py

│

├── gemini\_kernel.py

├── gemini\_client.py

├── gemini\_smart\_home.py

│

├── livekit\_agent.py

├── livekit\_gemini\_adapter.py

├── livekit\_kernel\_tools.py

├── dispatch\_livekit\_agent.py

│

├── inspect\_livekit\_room.py

│

├── extensions/

│

├── test\_\*.py

│

├── .gitignore

└── README.md

```



\---



\## Requirements



The project was verified with:



```text

Python 3.14

livekit-agents 1.8.3

google-genai 2.25.0

python-dotenv 1.2.3

```



\---



\## Environment Variables



Create a `.env` file containing:



```env

LIVEKIT\_URL=your\_livekit\_url

LIVEKIT\_API\_KEY=your\_livekit\_api\_key

LIVEKIT\_API\_SECRET=your\_livekit\_api\_secret

GEMINI\_API\_KEY=your\_gemini\_api\_key

```



Never commit `.env`.



The repository `.gitignore` excludes:



```text

.env

\_\_pycache\_\_/

\*.pyc

```



\---



\## Installation



Install the required packages:



```powershell

python -m pip install "livekit-agents" "google-genai" "python-dotenv"

```



\---



\## Running the Kernel Tests



Examples:



```powershell

python .\\test\_kernel\_end\_to\_end.py

```



```powershell

python .\\test\_retry\_recovery.py

```



```powershell

python .\\test\_multi\_tool\_integration.py

```



```powershell

python .\\test\_duplicate\_late\_results.py

```



\---



\## Running Dispatcher Tests



```powershell

python .\\test\_event\_dispatcher.py

python .\\test\_event\_dispatcher\_async.py

python .\\test\_event\_dispatcher\_failure.py

python .\\test\_event\_dispatcher\_lifecycle.py

python .\\test\_kernel\_dispatcher\_cancel.py

python .\\test\_kernel\_dispatcher\_correction.py

python .\\test\_kernel\_dispatcher\_failure.py

python .\\test\_kernel\_dispatcher\_lifecycle.py

```



\---



\## Running LiveKit



Start the LiveKit agent:



```powershell

python .\\livekit\_agent.py dev

```



The configured agent name is:



```text

samsung-ai-kernel

```



Connect a participant:



```powershell

python .\\test\_livekit\_participant.py

```



Create an explicit agent dispatch:



```powershell

python .\\dispatch\_livekit\_agent.py

```



\---



\## Verification



The project has been regression-tested for:



\- Kernel lifecycle

\- Event lifecycle

\- Event dispatcher

\- Dispatcher cancellation

\- Dispatcher correction

\- Retry and recovery

\- Checkpointing

\- Multi-tool execution

\- Failure isolation

\- Duplicate results

\- Late/stale results

\- LiveKit connection

\- LiveKit room creation

\- LiveKit participant connection

\- LiveKit AgentSession

\- LiveKit → Kernel tool execution



The production Python modules also compile successfully with Python's bytecode compiler.



\---



\## Gemini API Quota Note



During final LiveKit integration testing, the Gemini API returned:



```text

HTTP 429 RESOURCE\_EXHAUSTED

```



The response identified the free-tier request quota for the configured Gemini model.



This is an external API quota limitation rather than a LiveKit or Kernel execution error.



The following components were successfully verified independently:



\- LiveKit worker registration

\- LiveKit job dispatch

\- LiveKit room connection

\- LiveKit participant connection

\- AgentSession startup

\- LiveKit tool registration

\- LiveKit → Kernel tool execution

\- Kernel event generation

\- Kernel tool results



When sufficient Gemini API quota is available, the same integration can continue through the Gemini generation stage.



\---



\## Design Principle



The central design principle is:



> Let the AI reason about what should happen, while the Kernel controls how execution happens.



This separation allows the AI model and realtime interface to evolve without moving reliability-critical execution logic into the model layer.



\---



\## Project Status



\### Core Kernel



```text

READY

```



\### Reliability Layer



```text

READY

```



\### Gemini Bridge



```text

INTEGRATED

```



\### LiveKit Integration



```text

INTEGRATED

```



\### Live Gemini API



```text

CURRENTLY LIMITED BY GEMINI FREE-TIER QUOTA

```



\## Demo Flow



A typical Samsung AI Kernel request follows this flow:



```text

User

&#x20;│

&#x20;▼

LiveKit Room

&#x20;│

&#x20;▼

Gemini

&#x20;│

&#x20;│ decides required action

&#x20;▼

Samsung AI Kernel

&#x20;│

&#x20;├── Create / validate task

&#x20;├── Execute tool

&#x20;├── Retry when applicable

&#x20;├── Emit lifecycle events

&#x20;├── Save checkpoints

&#x20;└── Validate result

&#x20;│

&#x20;▼

ToolResult

&#x20;│

&#x20;▼

Gemini / LiveKit

&#x20;│

&#x20;▼

User

```



For an interrupted or corrected request:



```text

User Request

&#x20;    │

&#x20;    ▼

Task A

&#x20;    │

&#x20;    ├── execution

&#x20;    │

&#x20;    ▼

User Correction

&#x20;    │

&#x20;    ▼

Task A → CANCELLED

&#x20;    │

&#x20;    ▼

Task B → NEW TASK

&#x20;    │

&#x20;    ▼

Corrected Execution

&#x20;    │

&#x20;    ▼

TASK\_COMPLETED

```



This architecture keeps task state and tool execution controlled by the Kernel while allowing Gemini and LiveKit to provide the reasoning and realtime interaction layers.



\---



\## Security



API credentials are loaded through environment variables.



Sensitive configuration should be stored in `.env` and must never be committed to Git.



Before committing the project, verify:



```powershell

git status

```



and confirm that `.env` is not listed as a tracked or staged file.



\---



\## Author / Team



Samsung AI Kernel was developed as part of the Samsung AI Kernel / GenAI development project.



The implementation focuses on reliable AI tool execution, event-driven orchestration, Gemini integration, and realtime LiveKit interaction.
