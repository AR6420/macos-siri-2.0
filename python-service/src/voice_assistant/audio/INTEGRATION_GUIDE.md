# Audio Pipeline Integration Guide

Quick guide for integrating the audio pipeline with other modules.

## For Agent 3 (Speech-to-Text / Whisper)

### What You Receive

```python
from voice_assistant.audio import AudioEvent

# Your callback will receive:
async def on_audio_ready(event: AudioEvent):
    # event.type = "audio_ready"
    # event.audio_data = np.ndarray (shape: [N], dtype: int16, mono, 16kHz)
    # event.duration_seconds = float (e.g., 5.2)
    # event.timestamp = float (Unix timestamp)
    # event.metadata = {"sample_rate": 16000, "channels": 1}
```

### What You Should Do

```python
# 1. Validate the audio
assert event.audio_data.dtype == np.int16
assert event.metadata["sample_rate"] == 16000

# 2. Pass to Whisper
# The audio_data is ready for whisper.cpp or any STT engine
# You may need to save to WAV file or convert format

# Example: Save to temporary WAV for whisper.cpp
import wave
import tempfile

def audio_event_to_wav(event: AudioEvent) -> str:
    """Convert AudioEvent to WAV file for whisper.cpp"""
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        with wave.open(f.name, 'wb') as wav:
            wav.setnchannels(event.metadata["channels"])
            wav.setsampwidth(2)  # 16-bit = 2 bytes
            wav.setframerate(event.metadata["sample_rate"])
            wav.writeframes(event.audio_data.tobytes())
        return f.name

# 3. Return transcription result
@dataclass
class TranscriptionResult:
    text: str
    confidence: float
    duration_ms: int
```

### Integration Example

```python
from voice_assistant.audio import AudioPipeline, AudioEvent, AudioConfig
from your_stt_module import WhisperSTT

class VoiceAssistantOrchestrator:
    def __init__(self):
        self.audio_pipeline = AudioPipeline(AudioConfig(
            wake_word_access_key=os.getenv("PORCUPINE_ACCESS_KEY")
        ))
        self.stt = WhisperSTT()

    async def start(self):
        await self.audio_pipeline.start(
            on_audio_ready=self._handle_audio
        )

    async def _handle_audio(self, event: AudioEvent):
        # 1. Transcribe
        result = await self.stt.transcribe(event.audio_data)

        # 2. Pass to LLM (Agent 4)
        # ...
```

## For Agent 4 (LLM Client)

You don't directly interact with the audio module. You receive transcribed text from Agent 3.

However, you may want to access audio metadata for context:

```python
async def handle_transcription(
    text: str,
    audio_metadata: dict  # Pass through from AudioEvent.metadata
):
    # audio_metadata contains:
    # - sample_rate: int
    # - channels: int
    # - duration_seconds: float (from Agent 3)
```

## For Agent 5 (MCP Server / macOS Automation)

No direct audio interaction needed. The audio pipeline triggers the entire chain,
but you work with the LLM's tool calls.

## For Agent 6 (Orchestration)

You're the conductor! You tie everything together:

```python
from voice_assistant.audio import AudioPipeline, AudioEvent, AudioConfig
from voice_assistant.stt import WhisperSTT
from voice_assistant.llm import LLMProvider
from voice_assistant.mcp import MCPClient

class VoiceAssistant:
    def __init__(self, config):
        # Initialize all components
        self.audio = AudioPipeline(AudioConfig(**config.audio))
        self.stt = WhisperSTT(config.stt)
        self.llm = LLMProvider(config.llm)
        self.mcp = MCPClient(config.mcp)

    async def start(self):
        # Start audio pipeline
        await self.audio.start(
            on_wake_word=self._on_wake_word,
            on_audio_ready=self._on_audio_ready,
            on_error=self._on_error
        )

    async def _on_wake_word(self, event: AudioEvent):
        # Optional: Play a sound, show notification
        print("Wake word detected!")

    async def _on_audio_ready(self, event: AudioEvent):
        # The full pipeline:
        # Audio → STT → LLM → MCP Tools → TTS

        # 1. Transcribe
        transcription = await self.stt.transcribe(event.audio_data)

        # 2. Get LLM response
        response = await self.llm.complete(transcription.text)

        # 3. Execute tools if needed
        if response.tool_calls:
            for tool in response.tool_calls:
                result = await self.mcp.execute_tool(tool)
                # ... handle result

        # 4. Speak response (TTS)
        # await self.tts.speak(response.text)

    async def _on_error(self, error: Exception):
        # Handle errors gracefully
        print(f"Error: {error}")
```

## For Agent 1 (Swift App)

The Swift app communicates with the Python service via XPC. You'll need to:

### 1. Start/Stop Pipeline

```swift
// In your Swift app, call Python service:

func startListening() {
    pythonService.call("audio_pipeline.start") { result in
        // Pipeline started
    }
}

func stopListening() {
    pythonService.call("audio_pipeline.stop") { result in
        // Pipeline stopped
    }
}
```

### 2. Update Settings

```swift
func updateSensitivity(_ sensitivity: Double) {
    pythonService.call("audio_pipeline.update_sensitivity",
                       args: ["sensitivity": sensitivity])
}
```

### 3. Handle Status Updates

```swift
// Python service should send callbacks:
protocol VoiceAssistantDelegate {
    func didStartListening()
    func didDetectWakeWord()
    func didReceiveTranscription(_ text: String)
    func didReceiveResponse(_ text: String)
    func didEncounterError(_ error: Error)
}

// Update menu bar icon based on status
func didStartListening() {
    menuBarIcon.image = NSImage(named: "listening")
}
```

## Configuration Setup

Create `config.yaml` in your project root:

```yaml
audio:
  wake_word:
    enabled: true
    access_key_env: PORCUPINE_ACCESS_KEY
    sensitivity: 0.5
    model_path: null  # Optional: custom .ppn file

  device_name: default
  sample_rate: 16000
  channels: 1
  buffer_duration_seconds: 3.0

  vad:
    threshold: 0.5
    min_speech_duration_ms: 250
    min_silence_duration_ms: 500
    max_utterance_seconds: 30.0
```

Load it in your code:

```python
import yaml
from voice_assistant.audio import AudioConfig

with open("config.yaml") as f:
    config = yaml.safe_load(f)

audio_config = AudioConfig(**config["audio"]["wake_word"], **config["audio"])
```

## Testing Your Integration

### 1. Unit Test with Mock Audio

```python
import pytest
import numpy as np
from voice_assistant.audio import AudioEvent

@pytest.mark.asyncio
async def test_stt_integration():
    # Create fake audio event
    fake_audio = np.zeros(16000, dtype=np.int16)  # 1 second of silence
    event = AudioEvent(
        type="audio_ready",
        audio_data=fake_audio,
        timestamp=123.456,
        duration_seconds=1.0,
        metadata={"sample_rate": 16000, "channels": 1}
    )

    # Test your handler
    result = await your_audio_handler(event)
    assert result is not None
```

### 2. Integration Test with Real Pipeline

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_pipeline():
    config = AudioConfig(wake_word_enabled=False)  # Skip wake word for test
    pipeline = AudioPipeline(config)

    received = []

    async def on_audio(event):
        received.append(event)

    await pipeline.start(on_audio_ready=on_audio)

    # Trigger manually
    pipeline.trigger_hotkey()

    # Wait and verify
    await asyncio.sleep(2)
    assert len(received) > 0
```

## Common Issues

### "ModuleNotFoundError: No module named 'numpy'"
```bash
cd python-service
poetry install
```

### "No audio input detected"
- Check microphone permissions in System Settings
- List devices: `AudioDeviceManager().list_input_devices()`

### "Wake word not working"
```bash
export PORCUPINE_ACCESS_KEY="your-key-here"
```

### "VAD ending too quickly"
Increase silence duration in config:
```yaml
min_silence_duration_ms: 1000  # Was 500
```

## Next Steps

1. **Agent 3**: Implement `WhisperSTT.transcribe(audio_data)` method
2. **Agent 4**: Implement LLM client to receive transcribed text
3. **Agent 5**: Implement MCP tools for system automation
4. **Agent 6**: Tie everything together in orchestrator
5. **Agent 1**: Build Swift UI and XPC integration

## Questions?

- Check `audio/README.md` for detailed component docs
- Run `examples/audio_pipeline_demo.py` for a working example
- Review test files for usage patterns

---

**Happy Integrating!** 🎤→📝→🤖
