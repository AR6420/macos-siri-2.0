# Claude Voice Assistant for macOS Tahoe 26.1 - Development Plan

> **Target Platform**: macOS Tahoe 26.1 (macOS 26.1)  
> **Hardware**: Mac Studio M3 Ultra, 256GB unified memory  
> **Distribution**: Open source (GitHub) + .dmg/.pkg installer  
> **License**: Apache 2.0

---

## Project Vision

Build an intelligent, privacy-first voice assistant for macOS that combines local AI processing with flexible cloud API support. The system uses "Hey Claude" wake word activation, whisper.cpp for speech-to-text, gpt-oss:120b (or any API) for intelligence, and native macOS APIs for system automation—all while maintaining complete user privacy through on-device processing.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Swift Menu Bar App                        │
│  (User Interface, Permissions Management, Status Indicator)  │
└──────────────────────┬──────────────────────────────────────┘
                       │ XPC Communication
┌──────────────────────▼──────────────────────────────────────┐
│                  Python Backend Service                       │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Wake Word    │  │  Whisper     │  │  LLM Client  │     │
│  │ Detection    │→ │  Speech-to-  │→ │  (Flexible)  │     │
│  │ (Porcupine)  │  │  Text        │  │              │     │
│  └──────────────┘  └──────────────┘  └──────┬───────┘     │
│                                              │              │
│  ┌──────────────────────────────────────────▼───────────┐  │
│  │           MCP Server (FastMCP 2.0)                   │  │
│  │  - execute_applescript                               │  │
│  │  - control_application (Accessibility API)           │  │
│  │  - file_operations                                   │  │
│  │  - send_message                                      │  │
│  │  - web_search                                        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Multi-Agent Development Strategy

This project is designed for parallel development with **7 specialized agents** working on distinct subsystems. Each agent has clear input/output contracts to enable independent development with minimal integration friction.

### Agent Coordination Principles

1. **Clear Interface Contracts**: Each subsystem exposes well-defined APIs
2. **Mock/Stub Early**: Agents create mocks for dependencies to work independently
3. **Integration Points**: Weekly integration sprints to merge subsystems
4. **Shared Configuration**: All agents use `config.yaml` for settings
5. **Logging Standard**: All components log to `/tmp/voice-assistant/logs/`

---

## Agent 1: Swift Menu Bar Application

**Responsibility**: Native macOS UI, permissions management, system integration

**Priority**: HIGH (User-facing, critical for distribution)

### Tasks

1. Create Xcode project with Swift Package Manager
2. Implement menu bar icon with status indicator (idle/listening/processing)
3. Build permissions management UI:
   - Check and request Microphone permission
   - Check and request Accessibility permission
   - Check and request Input Monitoring permission
   - Check and request Full Disk Access (optional, for Messages)
4. Implement Preferences window:
   - LLM backend selection (Local/OpenAI/Anthropic/Custom)
   - API key management (stored in macOS Keychain)
   - Wake word sensitivity slider
   - Hotkey configuration
5. Setup XPC service to communicate with Python backend
6. Handle app lifecycle (launch at login, quit, update checks)
7. Implement crash reporting and error dialogs
8. Create "About" window with version info and credits

### Key Files

```
swift-app/
├── VoiceAssistant.xcodeproj
├── Sources/
│   ├── App/
│   │   ├── AppDelegate.swift           # Main app lifecycle
│   │   ├── MenuBarController.swift     # Status menu management
│   │   └── PreferencesWindow.swift     # Settings UI
│   ├── Permissions/
│   │   └── PermissionManager.swift     # TCC permission handling
│   ├── IPC/
│   │   └── PythonService.swift         # XPC to Python backend
│   └── Models/
│       └── Configuration.swift         # Shared config structures
└── Resources/
    ├── Assets.xcassets/                # Icons (idle, listening, processing)
    ├── Info.plist
    └── LaunchAgents/
        └── com.voiceassistant.plist    # launchd configuration
```

### Dependencies

- No external Swift packages initially
- Use native Cocoa frameworks: AppKit, Foundation, Security (Keychain)

### Interface Contract

**To Python Backend** (via XPC):
```swift
protocol VoiceAssistantService {
    func startListening()
    func stopListening()
    func getStatus() -> ServiceStatus
    func updateConfig(_ config: Configuration)
}

enum ServiceStatus {
    case idle
    case listening
    case processing
    case error(String)
}
```

**From Python Backend** (callbacks):
```swift
protocol VoiceAssistantDelegate {
    func didStartListening()
    func didDetectWakeWord()
    func didReceiveTranscription(_ text: String)
    func didReceiveResponse(_ text: String)
    func didEncounterError(_ error: Error)
}
```

### Testing Strategy

- Unit tests for permission checking logic
- UI tests for preferences window
- Manual testing on macOS Tahoe 26.1
- Test with SIP enabled/disabled scenarios

### Acceptance Criteria

- [ ] Menu bar icon appears and responds to clicks
- [ ] Permissions window accurately detects granted/denied permissions
- [ ] Preferences save to and load from UserDefaults
- [ ] API keys store securely in Keychain
- [ ] XPC communication established with Python service
- [ ] App launches at login when enabled
- [ ] Status indicator updates based on backend state

---

## Agent 2: Audio Pipeline & Wake Word Detection

**Responsibility**: Continuous audio monitoring, wake word detection, audio buffering

**Priority**: HIGH (Core functionality)

### Tasks

1. Setup PyAudio for microphone capture
2. Implement circular buffer (3 seconds) for pre-wake-word audio
3. Integrate Porcupine wake word detection:
   - Load custom "Hey Claude" wake word model (.ppn file)
   - Process audio frames in real-time
   - Detect wake word with configurable sensitivity
4. Implement VAD (Voice Activity Detection) using Silero
5. Create audio pipeline manager that:
   - Continuously monitors microphone
   - Buffers recent audio
   - Detects wake word
   - Captures full utterance after wake word
   - Passes complete audio to STT pipeline
6. Handle hotkey trigger (Cmd+Shift+Space) as alternative to wake word
7. Implement audio device selection and fallback

### Key Files

```
python-service/src/voice_assistant/audio/
├── __init__.py
├── wake_word.py           # Porcupine integration
├── audio_buffer.py        # Circular buffer implementation
├── vad.py                 # Voice Activity Detection (Silero)
├── audio_pipeline.py      # Main audio processing orchestrator
└── device_manager.py      # Audio device selection
```

### Dependencies

```python
pvporcupine==3.0.0
pyaudio==0.2.14
torch==2.0.0
numpy==1.24.0
```

### Interface Contract

**Input**:
- Configuration from `config.yaml`:
  - `wake_word.enabled`: bool
  - `wake_word.sensitivity`: float (0.0-1.0)
  - `wake_word.model_path`: str

**Output**:
```python
class AudioEvent:
    type: str  # "wake_word" | "hotkey" | "audio_ready"
    audio_data: np.ndarray  # Audio samples (16kHz, mono, int16)
    timestamp: float
    duration_seconds: float

# Callback interface
class AudioEventHandler(Protocol):
    def on_wake_word_detected(self, event: AudioEvent) -> None: ...
    def on_audio_ready(self, event: AudioEvent) -> None: ...
    def on_error(self, error: Exception) -> None: ...
```

### Testing Strategy

- Unit tests for circular buffer logic
- Integration test: Play "Hey Claude" audio file and verify detection
- Test VAD with silence/speech audio samples
- Performance test: CPU usage should be <5% when idle
- Test audio device disconnect/reconnect scenarios

### Acceptance Criteria

- [ ] Wake word "Hey Claude" detected with <1s latency
- [ ] Circular buffer captures 3 seconds pre-wake-word audio
- [ ] VAD correctly segments speech vs silence
- [ ] Hotkey (Cmd+Shift+Space) triggers audio capture
- [ ] CPU usage <5% during continuous monitoring
- [ ] Gracefully handles microphone permission denial
- [ ] Works with multiple audio input devices

---

## Agent 3: Speech-to-Text (Whisper Integration)

**Responsibility**: Convert audio to text using whisper.cpp with Core ML acceleration

**Priority**: HIGH (Core functionality)

### Tasks

1. Setup whisper.cpp as subprocess integration
2. Download and compile Core ML optimized models:
   - small.en (recommended)
   - base.en (faster)
   - medium.en (more accurate)
3. Implement Python wrapper for whisper.cpp:
   - Convert numpy audio to WAV file
   - Execute whisper.cpp with correct parameters
   - Parse output and extract transcription
4. Add VAD preprocessing to extract speech segments
5. Implement caching for repeated audio (dev/testing optimization)
6. Add language detection support (future enhancement)
7. Handle transcription errors and retries

### Key Files

```
python-service/src/voice_assistant/stt/
├── __init__.py
├── whisper_client.py      # Main Whisper integration
├── audio_processor.py     # Pre-processing (VAD, normalization)
└── model_manager.py       # Model download and management
```

### whisper.cpp Integration

**Installation script** (`scripts/setup_whisper.sh`):
```bash
#!/bin/bash
git clone https://github.com/ggml-org/whisper.cpp.git
cd whisper.cpp
./models/download-ggml-model.sh small.en
pip3 install ane_transformers openai-whisper coremltools
./models/generate-coreml-model.sh small.en
cmake -B build -DWHISPER_COREML=1 -DWHISPER_METAL=1
cmake --build build -j --config Release
```

### Dependencies

```python
torch==2.0.0
numpy==1.24.0
scipy==1.11.0
```

### Interface Contract

**Input**:
```python
@dataclass
class AudioInput:
    samples: np.ndarray      # Audio data (16kHz, mono, int16)
    sample_rate: int = 16000
    language: str = "en"

class WhisperSTT:
    def transcribe(self, audio: AudioInput) -> TranscriptionResult:
        """Transcribe audio to text"""
```

**Output**:
```python
@dataclass
class TranscriptionResult:
    text: str                # Transcribed text
    language: str            # Detected language
    confidence: float        # 0.0-1.0
    duration_ms: int         # Processing time
    segments: List[Segment]  # Optional: word-level timing
```

### Testing Strategy

- Test with sample audio files (various accents, noise levels)
- Benchmark latency on M3 Ultra: Target <500ms for 5-second audio
- Test with different whisper models (base/small/medium)
- Integration test with audio pipeline output
- Test error handling (corrupted audio, empty audio)

### Acceptance Criteria

- [ ] Transcribes 5-second clips in <500ms on M3 Ultra
- [ ] Accuracy >95% on clean speech (tested with LibriSpeech dataset)
- [ ] Gracefully handles silence or noise-only audio
- [ ] Core ML acceleration working (verify in Activity Monitor)
- [ ] Model files cached and reused across runs
- [ ] Returns confidence scores for quality filtering

---

## Agent 4: LLM Client (Flexible Multi-Provider)

**Responsibility**: Abstract LLM interface supporting local and cloud providers

**Priority**: HIGH (Core intelligence)

### Tasks

1. Design provider abstraction layer (Strategy pattern)
2. Implement LocalGPTOSSProvider:
   - MLX integration for gpt-oss:120b
   - Connection pooling for localhost:8080
   - Streaming support for progressive responses
3. Implement OpenAIProvider:
   - Standard OpenAI API client
   - Support for GPT-4, GPT-4o, etc.
4. Implement AnthropicProvider:
   - Claude API integration
   - Support for Sonnet, Opus models
5. Implement OpenRouterProvider:
   - Generic OpenAI-compatible API wrapper
   - Support for any model via OpenRouter
6. Create ProviderFactory for dynamic provider selection
7. Implement retry logic with exponential backoff
8. Add response streaming for better UX
9. Implement conversation context management (message history)

### Key Files

```
python-service/src/voice_assistant/llm/
├── __init__.py
├── base.py                # Abstract LLMProvider base class
├── providers/
│   ├── __init__.py
│   ├── local_gpt_oss.py   # Local gpt-oss:120b via MLX
│   ├── openai.py          # OpenAI API
│   ├── anthropic.py       # Claude API
│   └── openrouter.py      # OpenRouter generic provider
├── factory.py             # Provider selection logic
└── context.py             # Conversation history management
```

### Dependencies

```python
httpx==0.27.0              # Async HTTP client
anthropic==0.25.0
openai==1.0.0
mlx-lm==0.7.0              # For local MLX
tenacity==8.2.0            # Retry logic
```

### Interface Contract

**Abstract Base**:
```python
class LLMProvider(ABC):
    @abstractmethod
    async def complete(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> CompletionResult:
        """Generate completion from messages"""
    
    @abstractmethod
    async def stream_complete(
        self,
        messages: List[Message],
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream completion tokens"""

@dataclass
class Message:
    role: str  # "system" | "user" | "assistant"
    content: str

@dataclass
class CompletionResult:
    content: str
    model: str
    tokens_used: int
    finish_reason: str
    tool_calls: Optional[List[ToolCall]] = None
```

**Provider Factory**:
```python
class ProviderFactory:
    @staticmethod
    def create(backend: str, config: Dict) -> LLMProvider:
        """
        backend options:
        - "local_gpt_oss"
        - "openai_gpt4"
        - "anthropic_claude"
        - "openrouter"
        """
```

### Configuration Example

```yaml
llm:
  backend: local_gpt_oss
  
  local_gpt_oss:
    base_url: http://localhost:8080
    model: gpt-oss:120b
    timeout: 120
    
  openai:
    api_key_env: OPENAI_API_KEY
    model: gpt-4o
    timeout: 60
    
  anthropic:
    api_key_env: ANTHROPIC_API_KEY
    model: claude-sonnet-4-20250514
    timeout: 60
```

### Testing Strategy

- Unit tests for each provider with mocked HTTP responses
- Integration tests with real APIs (use test accounts)
- Test provider switching at runtime
- Benchmark latency for each provider on M3 Ultra
- Test error handling (network failures, API errors, timeouts)
- Test with/without tool calling

### Acceptance Criteria

- [ ] All 4 providers implemented and tested
- [ ] Provider selection from config.yaml works
- [ ] Streaming responses work for providers that support it
- [ ] Proper error messages for API failures
- [ ] Retry logic handles transient failures (3 retries with backoff)
- [ ] Conversation context maintained across turns
- [ ] Tool calling works for compatible providers

---

## Agent 5: MCP Server & macOS Automation Tools

**Responsibility**: Tool execution layer connecting LLM to macOS automation

**Priority**: MEDIUM-HIGH (Enables automation capabilities)

### Tasks

1. Setup FastMCP 2.0 server
2. Implement core automation tools:
   - `execute_applescript`: Run AppleScript code
   - `control_application`: Accessibility API wrapper
   - `file_operation`: File system operations
   - `send_message`: iMessage/SMS automation
   - `web_search`: Web search integration
   - `get_system_info`: System status queries
3. Create PyObjC wrappers for macOS Accessibility APIs
4. Implement AppleScript bridge with error handling
5. Add tool result validation and safety checks
6. Create tool documentation (for LLM consumption)
7. Implement tool execution logging

### Key Files

```
python-service/src/voice_assistant/mcp/
├── __init__.py
├── server.py              # FastMCP server definition
├── tools/
│   ├── __init__.py
│   ├── applescript.py     # AppleScript execution
│   ├── accessibility.py   # UI automation via Accessibility API
│   ├── files.py           # File operations
│   ├── messages.py        # iMessage automation
│   └── system.py          # System information
└── validation.py          # Tool safety checks
```

### Dependencies

```python
fastmcp==2.0.0
pyobjc-framework-Cocoa==11.0
pyobjc-framework-ApplicationServices==11.0
```

### Tool Definitions

**1. execute_applescript**:
```python
@mcp.tool()
async def execute_applescript(script: str) -> str:
    """
    Execute AppleScript code on macOS.
    
    Args:
        script: AppleScript code to execute
        
    Returns:
        Script output or error message
        
    Example:
        script: 'tell application "Safari" to open location "https://example.com"'
    """
```

**2. control_application**:
```python
@mcp.tool()
async def control_application(
    app_name: str,
    action: str,
    params: Optional[Dict] = None
) -> str:
    """
    Control macOS applications via Accessibility API.
    
    Args:
        app_name: Application name (e.g. "Safari", "Messages")
        action: Action to perform ("click_button", "fill_field", "get_text")
        params: Action-specific parameters
        
    Returns:
        Action result or error message
        
    Examples:
        app_name: "Safari"
        action: "click_button"
        params: {"button_title": "Search"}
    """
```

**3. file_operation**:
```python
@mcp.tool()
async def file_operation(
    operation: str,
    path: str,
    content: Optional[str] = None
) -> str:
    """
    Perform file system operations.
    
    Args:
        operation: "read", "write", "list", "delete", "move", "copy"
        path: File or directory path (supports ~ expansion)
        content: Content for write operations
        
    Returns:
        Operation result
        
    Security: Cannot access system directories or files outside home folder
    """
```

**4. send_message**:
```python
@mcp.tool()
async def send_message(
    recipient: str,
    message: str,
    platform: str = "imessage"
) -> str:
    """
    Send message via Messages app.
    
    Args:
        recipient: Phone number or contact name
        message: Message text
        platform: "imessage" or "sms"
        
    Returns:
        Success confirmation or error
        
    Note: Requires Messages app to be running
    """
```

**5. web_search**:
```python
@mcp.tool()
async def web_search(
    query: str,
    num_results: int = 5
) -> str:
    """
    Search the web and return summarized results.
    
    Args:
        query: Search query
        num_results: Number of results to return
        
    Returns:
        Search results summary
    """
```

### Accessibility API Implementation

**Example**: Click button in application
```python
from ApplicationServices import *
from AppKit import NSWorkspace

def click_button(app_name: str, button_title: str) -> bool:
    """Click button in application using Accessibility API"""
    
    # Find running application
    workspace = NSWorkspace.sharedWorkspace()
    for app in workspace.runningApplications():
        if app.localizedName() == app_name:
            app_element = AXUIElementCreateApplication(app.processIdentifier())
            
            # Find button recursively
            button = find_element_by_title(app_element, "AXButton", button_title)
            if button:
                AXUIElementPerformAction(button, kAXPressAction)
                return True
    
    return False
```

### Testing Strategy

- Unit tests for each tool with mocked system calls
- Integration tests on real macOS system
- Test permission handling (graceful failures when denied)
- Test AppleScript error scenarios
- Verify Accessibility API works with various apps
- Test file operations with sandboxing restrictions

### Acceptance Criteria

- [ ] All 6 tools implemented and tested
- [ ] AppleScript execution works with error handling
- [ ] Accessibility API can click buttons in Safari, Finder
- [ ] File operations respect security boundaries
- [ ] Messages automation works (with confirmation requirement)
- [ ] Web search returns relevant results
- [ ] Tools fail gracefully when permissions missing
- [ ] Tool results are properly formatted for LLM consumption

---

## Agent 6: AI Orchestration & Response Pipeline

**Responsibility**: Coordinate between STT → LLM → MCP → TTS pipeline

**Priority**: HIGH (Ties everything together)

### Tasks

1. Implement main orchestration class `VoiceAssistant`
2. Connect audio pipeline → STT → LLM → MCP → TTS
3. Implement conversation state management
4. Add tool calling logic:
   - Parse LLM responses for tool calls
   - Execute tools via MCP client
   - Feed results back to LLM
   - Handle multi-step tool execution
5. Implement response streaming for better UX
6. Add error recovery and fallback logic
7. Implement timeout handling at each stage
8. Create metrics/logging for performance monitoring

### Key Files

```
python-service/src/voice_assistant/
├── __init__.py
├── orchestrator.py        # Main VoiceAssistant class
├── state.py               # Conversation state management
├── pipeline.py            # STT → LLM → MCP → TTS coordination
└── metrics.py             # Performance tracking
```

### Main Orchestrator Class

```python
class VoiceAssistant:
    """Main orchestrator coordinating all subsystems"""
    
    def __init__(self, config: Configuration):
        self.audio_pipeline = AudioPipeline(config)
        self.stt = WhisperSTT(config)
        self.llm = ProviderFactory.create(config.llm_backend, config)
        self.mcp_client = MCPClient(config)
        self.tts = MacOSTTS(config)
        self.state = ConversationState()
    
    async def start(self):
        """Start listening for wake word / hotkey"""
        await self.audio_pipeline.start(
            on_wake_word=self._handle_wake_word,
            on_audio_ready=self._handle_audio
        )
    
    async def _handle_audio(self, audio_event: AudioEvent):
        """Main processing pipeline"""
        
        # 1. Transcribe audio
        transcription = await self.stt.transcribe(audio_event.audio_data)
        
        # 2. Get LLM response (with tools)
        messages = self.state.get_messages()
        messages.append(Message(role="user", content=transcription.text))
        
        tools = await self.mcp_client.list_tools()
        result = await self.llm.complete(messages, tools=tools)
        
        # 3. Execute tool calls if present
        if result.tool_calls:
            for tool_call in result.tool_calls:
                tool_result = await self.mcp_client.call_tool(
                    tool_call.name,
                    tool_call.arguments
                )
                messages.append(Message(
                    role="tool",
                    content=str(tool_result)
                ))
            
            # Get final response with tool results
            result = await self.llm.complete(messages)
        
        # 4. Speak response
        await self.tts.speak(result.content)
        
        # 5. Update conversation state
        self.state.add_exchange(transcription.text, result.content)
```

### Conversation State Management

```python
class ConversationState:
    """Manage conversation history and context"""
    
    def __init__(self, max_turns: int = 10):
        self.messages: List[Message] = []
        self.max_turns = max_turns
        self.metadata: Dict = {}
    
    def add_exchange(self, user_msg: str, assistant_msg: str):
        """Add user-assistant exchange"""
        self.messages.append(Message(role="user", content=user_msg))
        self.messages.append(Message(role="assistant", content=assistant_msg))
        
        # Keep only recent turns
        if len(self.messages) > self.max_turns * 2:
            self.messages = self.messages[-(self.max_turns * 2):]
    
    def get_messages(self) -> List[Message]:
        """Get messages for LLM context"""
        return self.messages.copy()
    
    def clear(self):
        """Clear conversation history"""
        self.messages.clear()
```

### Error Recovery Strategy

```python
class ErrorRecoveryHandler:
    """Handle errors at each pipeline stage"""
    
    async def handle_stt_error(self, error: Exception) -> str:
        """Fallback: Ask user to repeat"""
        await self.tts.speak("Sorry, I didn't catch that. Could you repeat?")
        return "repeat_request"
    
    async def handle_llm_error(self, error: Exception) -> str:
        """Fallback: Switch to cloud API or apologize"""
        if self.config.has_fallback_api:
            return await self._try_fallback_llm()
        else:
            await self.tts.speak("I'm having trouble processing that right now.")
            return "error"
    
    async def handle_tool_error(self, error: Exception) -> str:
        """Inform LLM that tool failed"""
        return f"Tool execution failed: {str(error)}"
```

### Dependencies

```python
# All dependencies from other agents
asyncio
typing
dataclasses
```

### Testing Strategy

- Integration tests covering full pipeline
- Test error scenarios at each stage
- Test tool calling with multiple tools
- Test conversation context management
- Performance testing: Measure end-to-end latency
- Test concurrent request handling

### Acceptance Criteria

- [ ] Full pipeline works: wake word → response spoken
- [ ] Tool calling executes and results fed back to LLM
- [ ] Conversation context maintained across turns
- [ ] Error recovery works at each stage
- [ ] End-to-end latency <3s for simple queries
- [ ] Metrics logged for each pipeline stage
- [ ] Graceful handling of interruptions (stop speaking)

---

## Agent 7: Configuration, Packaging & Distribution

**Responsibility**: Project structure, build system, installers, distribution

**Priority**: MEDIUM (Needed for distribution)

### Tasks

1. Setup project structure and dependency management
2. Create comprehensive `config.yaml` with all settings
3. Implement configuration loading and validation
4. Setup Poetry for Python dependency management
5. Create Xcode build configurations (Debug/Release)
6. Implement installer creation:
   - `.dmg` installer with drag-to-Applications
   - `.pkg` installer with proper signing
7. Setup code signing with Apple Developer certificates
8. Create GitHub Actions workflows:
   - Build and test on push
   - Create releases with installers
9. Write comprehensive README.md
10. Create user documentation
11. Setup logging infrastructure

### Project Structure

```
macos-voice-assistant/
├── .github/
│   └── workflows/
│       ├── build.yml           # Build and test
│       └── release.yml         # Create releases
├── swift-app/                  # Swift menu bar app (Agent 1)
│   ├── VoiceAssistant.xcodeproj
│   └── Sources/
├── python-service/             # Python backend (Agents 2-6)
│   ├── pyproject.toml
│   ├── config.yaml
│   └── src/voice_assistant/
├── scripts/
│   ├── setup_whisper.sh        # Setup whisper.cpp
│   ├── build_dmg.sh            # Create .dmg installer
│   └── build_pkg.sh            # Create .pkg installer
├── docs/
│   ├── SETUP.md                # Installation guide
│   ├── USAGE.md                # User guide
│   ├── DEVELOPMENT.md          # Developer guide
│   └── API.md                  # API documentation
├── tests/
│   ├── integration/            # End-to-end tests
│   └── fixtures/               # Test audio files
├── README.md
├── LICENSE                     # Apache 2.0
├── CONTRIBUTING.md
└── CLAUDE.md                   # This file
```

### Configuration File (config.yaml)

```yaml
# Voice Assistant Configuration

app:
  version: "1.0.0"
  log_level: INFO
  log_dir: /tmp/voice-assistant/logs
  data_dir: ~/Library/Application Support/VoiceAssistant

llm:
  backend: local_gpt_oss  # local_gpt_oss | openai_gpt4 | anthropic_claude | openrouter
  
  local_gpt_oss:
    base_url: http://localhost:8080
    model: gpt-oss:120b
    timeout: 120
    max_tokens: 1024
    temperature: 0.7
    
  openai:
    api_key_env: OPENAI_API_KEY
    model: gpt-4o
    base_url: https://api.openai.com/v1
    timeout: 60
    max_tokens: 1024
    temperature: 0.7
    
  anthropic:
    api_key_env: ANTHROPIC_API_KEY
    model: claude-sonnet-4-20250514
    timeout: 60
    max_tokens: 1024
    temperature: 0.7
    
  openrouter:
    api_key_env: OPENROUTER_API_KEY
    base_url: https://openrouter.ai/api/v1
    model: openai/gpt-oss-120b
    timeout: 60

audio:
  wake_word:
    enabled: true
    model_path: ~/.voice-assistant/wake_word.ppn
    sensitivity: 0.5
    access_key_env: PORCUPINE_ACCESS_KEY
  
  input_device: default  # or specific device name
  sample_rate: 16000
  channels: 1
  buffer_duration_seconds: 3

stt:
  engine: whisper_cpp
  model: small.en
  whisper_cpp_path: ~/.voice-assistant/whisper.cpp
  language: en

tts:
  engine: macos_native
  voice: Samantha
  rate: 200
  volume: 0.8

mcp:
  server_path: ~/.voice-assistant/mcp-server
  tools_enabled:
    - execute_applescript
    - control_application
    - file_operation
    - send_message
    - web_search
    - get_system_info

conversation:
  max_history_turns: 10
  context_window_tokens: 4096

performance:
  enable_metrics: true
  metrics_log_interval_seconds: 60
```

### Poetry Configuration (pyproject.toml)

```toml
[tool.poetry]
name = "macos-voice-assistant"
version = "1.0.0"
description = "Intelligent voice assistant for macOS Tahoe"
authors = ["Your Name <email@example.com>"]
license = "Apache-2.0"
readme = "README.md"

[tool.poetry.dependencies]
python = "^3.9"
pyobjc-framework-Cocoa = "^11.0"
pyobjc-framework-ApplicationServices = "^11.0"
pvporcupine = "^3.0.0"
pyaudio = "^0.2.14"
torch = "^2.0.0"
mlx-lm = "^0.7.0"
fastmcp = "^2.0.0"
httpx = "^0.27.0"
pyyaml = "^6.0"
anthropic = "^0.25.0"
openai = "^1.0.0"
tenacity = "^8.2.0"
numpy = "^1.24.0"
scipy = "^1.11.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.0.0"
pytest-asyncio = "^0.21.0"
black = "^23.0.0"
mypy = "^1.0.0"
ruff = "^0.1.0"

[tool.poetry.scripts]
voice-assistant = "voice_assistant.main:main"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

### DMG Creation Script

```bash
#!/bin/bash
# scripts/build_dmg.sh

APP_NAME="Voice Assistant"
VERSION="1.0.0"
DMG_NAME="VoiceAssistant-${VERSION}.dmg"
TEMP_DMG="temp.dmg"

# Build Swift app
cd swift-app
xcodebuild -scheme VoiceAssistant -configuration Release

# Create DMG
create-dmg \
  --volname "${APP_NAME}" \
  --window-pos 200 120 \
  --window-size 800 400 \
  --icon-size 100 \
  --icon "${APP_NAME}.app" 175 120 \
  --hide-extension "${APP_NAME}.app" \
  --app-drop-link 625 120 \
  "${DMG_NAME}" \
  "build/Release/${APP_NAME}.app"

echo "DMG created: ${DMG_NAME}"
```

### GitHub Actions Workflow

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: macos-14
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install Poetry
        run: pip install poetry
      
      - name: Install dependencies
        run: cd python-service && poetry install
      
      - name: Setup whisper.cpp
        run: ./scripts/setup_whisper.sh
      
      - name: Build Swift app
        run: |
          cd swift-app
          xcodebuild -scheme VoiceAssistant -configuration Release
      
      - name: Create DMG
        run: ./scripts/build_dmg.sh
      
      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          files: |
            VoiceAssistant-*.dmg
            VoiceAssistant-*.pkg
```

### Testing Strategy

- Test installation on clean macOS Tahoe system
- Verify all permissions requested correctly
- Test configuration loading and validation
- Test build on multiple macOS versions
- Verify code signing and notarization

### Acceptance Criteria

- [ ] Project builds successfully from clean checkout
- [ ] `config.yaml` loads and validates properly
- [ ] `.dmg` installer created and signed
- [ ] `.pkg` installer created and signed
- [ ] GitHub Actions workflow runs successfully
- [ ] README.md is comprehensive and accurate
- [ ] Documentation covers installation, usage, troubleshooting
- [ ] Logging infrastructure works across all components

---

## Development Phases

### Phase 1: Core Infrastructure (Week 1-2)

**Goal**: Get basic voice → text → response pipeline working

**Agents**: 2, 3, 4, 6
- Agent 2: Wake word detection with Porcupine
- Agent 3: Whisper STT integration
- Agent 4: Local gpt-oss:120b provider
- Agent 6: Basic orchestration (no tools yet)

**Milestone**: Say "Hey Claude, what time is it?" and get spoken response

### Phase 2: System Integration (Week 3-4)

**Goal**: Add native macOS UI and automation tools

**Agents**: 1, 5
- Agent 1: Swift menu bar app with basic UI
- Agent 5: MCP server with 2-3 core tools

**Milestone**: Launch app from menu bar, use tools like "open Safari"

### Phase 3: Cloud API Support (Week 5)

**Goal**: Add flexibility with cloud providers

**Agents**: 4
- Agent 4: OpenAI and Anthropic providers

**Milestone**: Switch between local and cloud in preferences

### Phase 4: Polish & Distribution (Week 6-7)

**Goal**: Create distributable installer

**Agents**: 7
- Agent 7: DMG/PKG creation, documentation

**Milestone**: Install .dmg on clean Mac and have working voice assistant

### Phase 5: Advanced Features (Week 8+)

**Goal**: Enhanced capabilities

**All Agents**: Refinements based on testing
- Response streaming
- Better error recovery
- More automation tools
- Advanced conversation context

---

## Integration Points & Contracts

### Audio Pipeline → STT
```python
# audio/audio_pipeline.py produces:
AudioEvent(
    type="audio_ready",
    audio_data=np.ndarray,  # 16kHz, mono, int16
    timestamp=time.time(),
    duration_seconds=5.2
)

# stt/whisper_client.py consumes:
def transcribe(audio: AudioEvent) -> TranscriptionResult
```

### STT → LLM Client
```python
# stt returns:
TranscriptionResult(
    text="Open Safari and search for weather",
    confidence=0.95,
    duration_ms=450
)

# llm/base.py consumes:
messages = [Message(role="user", content=result.text)]
```

### LLM Client → MCP Server
```python
# llm returns:
CompletionResult(
    content="I'll open Safari for you.",
    tool_calls=[
        ToolCall(name="execute_applescript", arguments={...})
    ]
)

# mcp/server.py exposes:
@mcp.tool()
async def execute_applescript(script: str) -> str
```

### Orchestrator → Swift App
```python
# Swift app calls Python service via XPC:
pythonService.startListening()

# Python service sends callbacks:
delegate.didReceiveTranscription("Hello Claude")
delegate.didReceiveResponse("Hello! How can I help?")
```

---

## Testing Strategy

### Unit Tests
- Each agent writes unit tests for their modules
- Mock external dependencies (APIs, system calls)
- Target: 80% code coverage

### Integration Tests
```python
# tests/integration/test_full_pipeline.py
async def test_full_voice_pipeline():
    """Test wake word → transcription → LLM → tool → response"""
    
    # 1. Simulate wake word audio
    audio = load_test_audio("hey_claude_open_safari.wav")
    
    # 2. Process through pipeline
    assistant = VoiceAssistant(test_config)
    result = await assistant.process_audio(audio)
    
    # 3. Verify result
    assert "Safari" in result.transcription
    assert result.tool_calls[0].name == "execute_applescript"
    assert result.success == True
```

### Manual Testing Checklist
- [ ] Wake word detection works reliably
- [ ] Hotkey (Cmd+Shift+Space) triggers correctly
- [ ] Speech transcription accurate
- [ ] LLM responses relevant
- [ ] Tools execute successfully
- [ ] TTS speaks clearly
- [ ] Menu bar icon updates status
- [ ] Preferences save/load correctly
- [ ] App survives Mac restart
- [ ] Performance acceptable on M3 Ultra

---

## Performance Targets

| Metric | Target | Measured On |
|--------|--------|-------------|
| Wake word detection latency | <500ms | M3 Ultra |
| STT transcription (5s audio) | <500ms | whisper.cpp small.en |
| LLM response (local) | <2s | gpt-oss:120b 8-bit |
| LLM response (cloud) | <5s | Claude Sonnet 4 |
| Tool execution | <1s | AppleScript/Accessibility |
| TTS start speaking | <500ms | macOS native |
| **Total end-to-end** | **<5s** | Wake word → response spoken |
| Idle CPU usage | <5% | Continuous wake word monitoring |
| Memory usage (idle) | <200MB | Without LLM loaded |
| Memory usage (with LLM) | <75GB | gpt-oss:120b loaded |

---

## Security & Privacy

### Principles
1. **Privacy-first**: All voice data processed locally by default
2. **User consent**: Explicit permission for each capability
3. **Secure storage**: API keys in macOS Keychain
4. **Minimal permissions**: Request only what's needed
5. **Transparent**: User knows when cloud APIs used

### Permission Handling
```python
# Check before use
if not has_microphone_permission():
    request_microphone_permission()
    return

if not has_accessibility_permission():
    show_accessibility_instructions()
    return
```

### API Key Storage
```swift
// Swift: Store in Keychain
KeychainManager.save(apiKey: key, for: "OPENAI_API_KEY")

// Python: Retrieve from Keychain
api_key = keyring.get_password("VoiceAssistant", "OPENAI_API_KEY")
```

---

## Documentation Requirements

### README.md
- Project overview
- Features list
- Installation instructions
- Quick start guide
- Screenshots/demo video
- Link to detailed docs

### SETUP.md
- System requirements
- Dependency installation
- whisper.cpp setup
- LLM backend setup (local + cloud)
- Porcupine wake word training
- Troubleshooting guide

### USAGE.md
- How to activate voice assistant
- Example voice commands
- Switching LLM backends
- Available automation tools
- Tips for best results

### DEVELOPMENT.md
- Project architecture
- How to build from source
- Testing guide
- Contributing guidelines
- Agent responsibilities (this doc)

---

## Success Criteria

The project is complete when:

1. **Core Functionality**:
   - [ ] Wake word "Hey Claude" activates assistant
   - [ ] Hotkey Cmd+Shift+Space activates assistant
   - [ ] Voice commands transcribed accurately
   - [ ] LLM provides intelligent responses
   - [ ] Tools execute successfully
   - [ ] Responses spoken clearly

2. **User Experience**:
   - [ ] Native macOS app with menu bar presence
   - [ ] Intuitive preferences window
   - [ ] Clear permission requests with explanations
   - [ ] Visual feedback (icon changes during listening/processing)
   - [ ] End-to-end latency <5 seconds

3. **Flexibility**:
   - [ ] Works with local gpt-oss:120b
   - [ ] Works with OpenAI API
   - [ ] Works with Anthropic API
   - [ ] Easy switching between backends
   - [ ] Configurable via preferences UI and config.yaml

4. **Distribution**:
   - [ ] Creates installable .dmg file
   - [ ] Code signed and notarized
   - [ ] GitHub releases automated
   - [ ] Comprehensive documentation
   - [ ] Installation tested on clean macOS Tahoe

5. **Performance**:
   - [ ] Meets all performance targets (see table above)
   - [ ] Stable under extended use
   - [ ] Handles errors gracefully
   - [ ] Resource usage acceptable

---

## Known Limitations

1. **macOS Only**: Only works on macOS 26.1 (Tahoe) and later
2. **Apple Silicon Recommended**: Intel Macs may have reduced performance
3. **Accessibility Required**: Some features need Accessibility permission
4. **Messages Confirmation**: Sending messages requires user confirmation (iOS security)
5. **Background Limits**: Some operations limited when screen locked
6. **App-Specific**: Not all apps support Accessibility API equally

---

## Future Enhancements (Post-Launch)

1. **Multi-language support**: Beyond English
2. **Custom wake words**: User-trained wake words
3. **Response streaming**: Speak while generating
4. **Context awareness**: Screen content understanding
5. **Plugin system**: Community-contributed tools
6. **iOS companion**: Control from iPhone
7. **Home Assistant integration**: Smart home control
8. **Calendar integration**: Meeting awareness
9. **Email automation**: Read/send emails
10. **Advanced scheduling**: Time-based automation

---

## Questions & Clarifications

If any agent has questions during development:

1. **Check this document first** - Most decisions documented here
2. **Check interface contracts** - Verify your component's inputs/outputs
3. **Create stub/mock** - If dependency not ready, mock it
4. **Document assumptions** - Add comments explaining decisions
5. **Ask in integration meetings** - Weekly sync to resolve blockers

---

## Claude Code Usage Instructions

**For Claude Code developers:**

1. **Read this entire document** before starting your assigned agent
2. **Reference the interface contracts** when building your component
3. **Create tests first** (TDD approach) to validate your work
4. **Use the provided file structure** - Don't deviate without discussion
5. **Log everything** - Help with debugging integration issues
6. **Document public APIs** - Other agents depend on your contracts
7. **Think about errors** - Handle failure gracefully
8. **Performance matters** - Profile your code on M3 Ultra
9. **Security first** - Never log API keys or sensitive data
10. **Integration is key** - Your component must work with others

**When starting your agent's work:**
```
I am Agent [N]: [Agent Name]

I have read CLAUDE.md and understand:
- My responsibilities: [list key tasks]
- My dependencies: [list what I need from other agents]
- My deliverables: [list what I provide to other agents]
- My acceptance criteria: [list success metrics]

Starting development now with priority on: [highest priority task]
```

This structure ensures all agents can work in parallel while maintaining integration points. Good luck! 🚀

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-17  
**Status**: Ready for Development
