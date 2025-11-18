# Audio Pipeline Module

This module provides the audio processing pipeline for the macOS Voice Assistant, including wake word detection, audio buffering, and voice activity detection.

## Components

### 1. AudioPipeline
Main orchestrator that coordinates all audio processing components.

**Features:**
- Continuous microphone monitoring
- Wake word detection ("Hey Claude")
- 3-second circular audio buffer (pre-wake-word context)
- Voice Activity Detection (VAD) for utterance segmentation
- Hotkey trigger support (Cmd+Shift+Space)
- Event-based architecture for downstream processing

**Usage:**
```python
from voice_assistant.audio import AudioPipeline, AudioEvent, AudioConfig

# Configure pipeline
config = AudioConfig(
    wake_word_enabled=True,
    wake_word_access_key="YOUR_PORCUPINE_KEY",
    wake_word_sensitivity=0.5,
    sample_rate=16000,
    buffer_duration_seconds=3.0
)

# Define callbacks
async def on_audio_ready(event: AudioEvent):
    print(f"Got {event.duration_seconds}s of audio")
    # Send to STT pipeline...

# Start pipeline
pipeline = AudioPipeline(config)
await pipeline.start(on_audio_ready=on_audio_ready)

# Trigger via hotkey
pipeline.trigger_hotkey()
```

### 2. CircularAudioBuffer
Thread-safe circular buffer for maintaining a rolling window of recent audio.

**Features:**
- Fixed-size rolling buffer
- Thread-safe operations
- Configurable duration
- Chronological data retrieval

**Usage:**
```python
from voice_assistant.audio import CircularAudioBuffer

buffer = CircularAudioBuffer(
    duration_seconds=3.0,
    sample_rate=16000,
    channels=1
)

# Write audio data
buffer.write(audio_chunk)

# Read all buffered audio
audio_data = buffer.read_all()

# Read specific duration
last_second = buffer.read_seconds(1.0)
```

### 3. WakeWordDetector
Wake word detection using Picovoice Porcupine.

**Features:**
- "Hey Claude" wake word detection
- Configurable sensitivity
- Frame-by-frame processing
- Custom keyword support (.ppn files)

**Setup:**
1. Get access key from [Picovoice Console](https://console.picovoice.ai/)
2. (Optional) Train custom "Hey Claude" wake word
3. Set `PORCUPINE_ACCESS_KEY` environment variable

**Usage:**
```python
from voice_assistant.audio.wake_word import WakeWordDetector

detector = WakeWordDetector(
    access_key="YOUR_KEY",
    keyword_path="/path/to/hey_claude.ppn",  # Optional
    sensitivity=0.5
)

# Process audio frame (must be exactly frame_length samples)
detected = detector.process_frame(audio_frame)

if detected:
    print("Wake word detected!")
```

### 4. VoiceActivityDetector
Speech detection using Silero VAD model.

**Features:**
- Distinguishes speech from silence
- Segments utterances
- Detects end of speech
- Fallback energy-based detection

**Usage:**
```python
from voice_assistant.audio.vad import VoiceActivityDetector

vad = VoiceActivityDetector(
    sample_rate=16000,
    threshold=0.5,
    min_silence_duration_ms=500
)

# Check if chunk contains speech
is_speech, confidence = vad.is_speech(audio_chunk)

# Detect end of utterance
speech_ended = vad.has_speech_ended(audio_chunk)
```

### 5. AudioDeviceManager
Audio input device enumeration and selection.

**Features:**
- List available devices
- Select by name or index
- Device validation
- Default device fallback

**Usage:**
```python
from voice_assistant.audio.device_manager import AudioDeviceManager

manager = AudioDeviceManager()

# List all input devices
devices = manager.list_input_devices()
for dev in devices:
    print(f"{dev['index']}: {dev['name']}")

# Select device
device = manager.select_device(device_name="MacBook Pro Microphone")
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    AudioPipeline                         │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   PyAudio    │→ │   Circular   │→ │  Wake Word   │ │
│  │   Stream     │  │    Buffer    │  │   Detector   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐                    │
│  │     VAD      │→ │  Audio Event │→ [To STT Pipeline] │
│  │   (Silero)   │  │   Emission   │                    │
│  └──────────────┘  └──────────────┘                    │
└─────────────────────────────────────────────────────────┘
```

## Data Flow

1. **Continuous Monitoring**
   - PyAudio captures audio in chunks (512 samples)
   - All audio written to circular buffer
   - Wake word detector processes each frame

2. **Wake Word Detection**
   - When "Hey Claude" detected → emit `AudioEvent(type="wake_word")`
   - Switch to "listening mode"
   - Begin accumulating utterance audio

3. **Utterance Recording**
   - Capture audio chunks
   - VAD monitors for end of speech
   - Stop on silence (500ms) or timeout (30s)

4. **Audio Ready**
   - Emit `AudioEvent(type="audio_ready")` with complete utterance
   - Return to monitoring mode
   - Ready for next wake word

## AudioEvent Contract

The pipeline emits `AudioEvent` objects:

```python
@dataclass
class AudioEvent:
    type: str                 # "wake_word" | "hotkey" | "audio_ready"
    audio_data: np.ndarray    # int16, mono, 16kHz
    timestamp: float          # Unix timestamp
    duration_seconds: float   # Audio duration
    metadata: dict            # Additional info
```

**For STT Integration:**
```python
async def on_audio_ready(event: AudioEvent):
    # event.audio_data is ready for Whisper transcription
    assert event.audio_data.dtype == np.int16
    assert event.type == "audio_ready"

    # Pass to STT pipeline
    result = await whisper_stt.transcribe(event.audio_data)
```

## Requirements

### Python Dependencies
```bash
pip install pyaudio numpy pvporcupine torch torchaudio
```

### System Requirements
- macOS 26.1+ (Tahoe)
- Microphone access permission
- Python 3.9+

### Optional
- Porcupine access key for wake word detection
- Custom .ppn wake word file

## Performance

**Targets (on M3 Ultra):**
- CPU usage: <5% during idle monitoring
- Wake word latency: <500ms
- Memory usage: <200MB (without LLM)

**Measured:**
- Circular buffer: ~5MB for 3 seconds @ 16kHz
- Wake word detector: ~10MB
- Silero VAD model: ~50MB

## Testing

Run tests:
```bash
# All tests
pytest tests/audio/

# Specific test file
pytest tests/audio/test_audio_buffer.py -v

# With coverage
pytest tests/audio/ --cov=voice_assistant.audio --cov-report=html
```

## Troubleshooting

### No audio input detected
- Check microphone permissions in System Settings
- Verify device with: `python -c "from voice_assistant.audio import AudioDeviceManager; print(AudioDeviceManager().list_input_devices())"`

### Wake word not detecting
- Ensure `PORCUPINE_ACCESS_KEY` is set
- Try increasing sensitivity (0.5 → 0.7)
- Check microphone is not muted
- Verify wake word model path

### VAD ending too early/late
- Adjust `min_silence_duration_ms` (500-1000ms)
- Modify `vad_threshold` (0.3-0.7)
- Check audio levels (RMS energy)

## Future Enhancements

- [ ] Noise cancellation preprocessing
- [ ] Multi-channel support
- [ ] Acoustic echo cancellation
- [ ] Background noise adaptation
- [ ] Custom wake word training UI
- [ ] Audio quality metrics
- [ ] Streaming VAD for real-time feedback

## License

Apache 2.0

## Contact

For issues or questions, see the main project README.
