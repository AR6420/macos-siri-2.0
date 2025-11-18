# Agent 3: Speech-to-Text Integration Notes

## Overview

The Speech-to-Text (STT) module provides high-performance audio transcription using whisper.cpp with Core ML acceleration on Apple Silicon. This document provides integration guidance for Agent 6 (Orchestrator) and other dependent agents.

## Module Components

### 1. WhisperSTT Client (`whisper_client.py`)

**Primary interface for speech-to-text transcription.**

```python
from voice_assistant.stt import WhisperSTT, AudioInput, TranscriptionResult, WhisperModel

# Initialize
stt = WhisperSTT(
    model=WhisperModel.SMALL_EN,
    enable_cache=True,
    enable_vad=True,
)

# Transcribe audio
audio_input = AudioInput(
    samples=numpy_array,  # int16 or float32
    sample_rate=16000,
    language="en"
)

result = stt.transcribe(audio_input)
print(result.text)
```

### 2. AudioProcessor (`audio_processor.py`)

**Audio preprocessing utilities: VAD, normalization, resampling.**

```python
from voice_assistant.stt.audio_processor import AudioProcessor

processor = AudioProcessor()

# Extract speech segments (remove silence)
speech_only = processor.extract_speech(audio, sample_rate=16000)

# Normalize audio
normalized = processor.normalize_audio(audio)

# Resample audio
resampled = processor.resample(audio, orig_sr=48000, target_sr=16000)
```

### 3. ModelManager (`model_manager.py`)

**Model download and management.**

```python
from voice_assistant.stt import ModelManager, WhisperModel

manager = ModelManager()

# Download model
manager.download_model(WhisperModel.SMALL_EN)

# Verify installation
if manager.verify_whisper_cpp_installation():
    print("whisper.cpp is ready!")
```

## Interface Contract for Agent 6 (Orchestrator)

### Input: AudioEvent from Agent 2 (Audio Pipeline)

```python
from dataclasses import dataclass
import numpy as np

@dataclass
class AudioEvent:
    """From Agent 2"""
    type: str  # "wake_word" | "hotkey" | "audio_ready"
    audio_data: np.ndarray  # Audio samples (16kHz, mono, int16)
    timestamp: float
    duration_seconds: float
```

### Output: TranscriptionResult to Agent 6

```python
@dataclass
class TranscriptionResult:
    text: str                # Transcribed text
    language: str            # Detected language
    confidence: float        # 0.0-1.0
    duration_ms: int         # Processing time
    segments: List[Segment]  # Optional: word-level timing
    model_used: str         # Model name
    cache_hit: bool         # Whether result was cached
```

### Integration Example

```python
# In orchestrator.py (Agent 6)
from voice_assistant.stt import WhisperSTT, AudioInput, WhisperModel

class VoiceAssistant:
    def __init__(self, config):
        # Initialize STT client
        self.stt = WhisperSTT(
            model=WhisperModel.SMALL_EN,
            enable_cache=True,
            enable_vad=True,
        )

    async def _handle_audio(self, audio_event: AudioEvent):
        """Process audio from Agent 2"""

        # Convert AudioEvent to AudioInput
        audio_input = AudioInput(
            samples=audio_event.audio_data,
            sample_rate=16000,  # Agent 2 provides 16kHz
            language="en"
        )

        # Transcribe (use async wrapper)
        result = await self.stt.transcribe_async(audio_input)

        # Check if transcription succeeded
        if not result.text:
            logger.warning("No speech detected")
            return None

        if result.confidence < 0.5:
            logger.warning(f"Low confidence: {result.confidence}")
            # Maybe ask user to repeat

        logger.info(f"Transcription: \"{result.text}\" ({result.duration_ms}ms)")

        # Pass to LLM (Agent 4)
        return result.text
```

## Configuration

Add to `config.yaml`:

```yaml
stt:
  engine: whisper_cpp
  model: small.en  # tiny.en, base.en, small.en, medium.en
  whisper_cpp_path: ~/.voice-assistant/whisper.cpp/build/bin/main
  language: en
  enable_vad: true
  enable_cache: true
  cache_dir: ~/.voice-assistant/stt-cache
  num_threads: 4
```

## Performance Characteristics

### Latency (M3 Ultra, macOS)

| Model | 5s Audio | 10s Audio | Core ML |
|-------|----------|-----------|---------|
| tiny.en | ~200ms | ~350ms | ❌ |
| base.en | ~300ms | ~500ms | ✅ |
| small.en | ~400ms | ~700ms | ✅ |
| medium.en | ~800ms | ~1500ms | ✅ |

### Accuracy

- **small.en** (recommended): 95%+ on clean speech
- **base.en** (fast): 90%+ on clean speech
- **medium.en** (accurate): 97%+ on clean speech

### Resource Usage

- **CPU (idle)**: <1% (no active transcription)
- **Memory**: ~500MB (model loaded)
- **Core ML**: Offloads to Neural Engine (lower CPU usage)

## Error Handling

### Common Errors and Solutions

#### 1. Empty Transcription

```python
result = stt.transcribe(audio_input)
if not result.text:
    # Possible causes:
    # - Audio is silence
    # - VAD filtered out all audio
    # - Audio too short/corrupted

    # Solution: Disable VAD and retry
    stt_no_vad = WhisperSTT(enable_vad=False)
    result = stt_no_vad.transcribe(audio_input)
```

#### 2. Low Confidence

```python
if result.confidence < 0.5:
    # Possible causes:
    # - Background noise
    # - Poor audio quality
    # - Wrong language

    # Solution: Ask user to repeat
    await tts.speak("Sorry, I didn't catch that. Could you repeat?")
```

#### 3. Timeout

```python
try:
    result = stt.transcribe(audio_input)
except RuntimeError as e:
    if "timeout" in str(e):
        logger.error("Transcription timed out")
        # Fall back to shorter timeout or smaller model
```

#### 4. whisper.cpp Not Found

```python
from voice_assistant.stt import ModelManager

manager = ModelManager()
if not manager.verify_whisper_cpp_installation():
    raise RuntimeError(
        "whisper.cpp not installed. Run: scripts/setup_whisper.sh"
    )
```

## Audio Format Requirements

### Agent 2 Must Provide

- **Sample Rate**: 16000 Hz (16 kHz)
- **Channels**: Mono (1 channel)
- **Format**: int16 or float32
- **Duration**: 0.5s - 30s recommended

### Auto-Conversion

The STT module automatically handles:
- ✅ Stereo → Mono conversion
- ✅ Float32 ↔ Int16 conversion
- ✅ Resampling (any rate → 16 kHz)
- ✅ Normalization

### Not Supported

- ❌ Compressed formats (MP3, AAC) - must be decoded first
- ❌ Sample rates < 8 kHz or > 48 kHz
- ❌ More than 2 channels

## Optimization Tips

### 1. Enable Caching (Development)

```python
stt = WhisperSTT(
    enable_cache=True,
    cache_dir="/tmp/stt-cache"
)

# Repeated transcriptions of same audio are instant
# Cache key based on audio content hash
```

### 2. Disable VAD for Short Clips

```python
# For commands < 2 seconds, VAD may remove too much
stt = WhisperSTT(enable_vad=False)
```

### 3. Use Smaller Model for Fast Responses

```python
# For simple commands, base.en is sufficient
stt_fast = WhisperSTT(model=WhisperModel.BASE_EN)

# For dictation, use more accurate model
stt_accurate = WhisperSTT(model=WhisperModel.MEDIUM_EN)
```

### 4. Async Processing

```python
# Don't block the event loop
result = await stt.transcribe_async(audio_input)
```

## Testing

### Unit Tests

```bash
cd python-service
pytest tests/stt/ -v
```

### Integration Tests (Require whisper.cpp)

```bash
# Setup whisper.cpp first
./scripts/setup_whisper.sh

# Run integration tests
pytest tests/stt/ -v -m integration
```

### Manual Testing

```bash
# Test with example script
python examples/stt_example.py --wav test.wav

# Test all examples
python examples/stt_example.py
```

## Troubleshooting

### Issue: Core ML Not Working

**Symptoms**: Transcription works but doesn't use Neural Engine

**Check**:
```python
from voice_assistant.stt import ModelManager, WhisperModel

manager = ModelManager()
if manager.has_coreml_model(WhisperModel.SMALL_EN):
    print("Core ML model available")
else:
    print("Core ML model missing - run setup_whisper.sh")
```

**Fix**:
```bash
cd ~/.voice-assistant/whisper.cpp
bash models/generate-coreml-model.sh small.en
```

### Issue: Slow Transcription

**Check**:
1. Verify Core ML is enabled (see above)
2. Check CPU threads: `num_threads` in config
3. Monitor with Activity Monitor for Neural Engine usage

### Issue: Poor Accuracy

**Causes**:
- Background noise → Use noise reduction preprocessing
- Wrong language → Set correct language in AudioInput
- Model too small → Use medium.en instead of base.en

## Dependencies for Agent 6

### Required Imports

```python
from voice_assistant.stt import (
    WhisperSTT,
    AudioInput,
    TranscriptionResult,
    WhisperModel,
)
```

### Configuration Loading

```python
import yaml

with open("config.yaml") as f:
    config = yaml.safe_load(f)

stt = WhisperSTT(
    model=WhisperModel[config['stt']['model'].upper().replace('.', '_')],
    enable_vad=config['stt'].get('enable_vad', True),
    enable_cache=config['stt'].get('enable_cache', True),
)
```

## Future Enhancements

Planned features (not yet implemented):

1. **Streaming Transcription**: Real-time transcription as audio arrives
2. **Language Detection**: Auto-detect language from audio
3. **Custom Vocabulary**: Bias model toward specific words
4. **Diarization**: Speaker identification
5. **Punctuation Restoration**: Better sentence formatting
6. **Timestamp Alignment**: Word-level timestamps

## Contact & Support

For issues related to the STT module:
- Check logs in `/tmp/voice-assistant/logs/stt.log`
- Run diagnostics: `python -m voice_assistant.stt.diagnostics`
- Review test failures: `pytest tests/stt/ -v --tb=short`

## Summary for Agent 6

**Minimal Integration:**

```python
from voice_assistant.stt import WhisperSTT, AudioInput, WhisperModel

# Init (once)
stt = WhisperSTT(model=WhisperModel.SMALL_EN)

# Transcribe (per audio)
audio_input = AudioInput(samples=audio_array, sample_rate=16000)
result = await stt.transcribe_async(audio_input)

# Use result
if result.text:
    print(f"User said: {result.text}")
```

**That's it!** The STT module handles all the complexity internally.
