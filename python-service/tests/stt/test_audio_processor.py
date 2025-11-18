"""
Tests for Audio Processor
"""

import numpy as np
import pytest

from voice_assistant.stt.audio_processor import AudioProcessor


@pytest.fixture
def processor():
    """Create AudioProcessor instance"""
    return AudioProcessor(
        vad_threshold=0.02,
        vad_min_speech_duration_ms=100,
        vad_padding_ms=200,
    )


@pytest.fixture
def sample_audio():
    """Generate sample audio with speech"""
    sample_rate = 16000
    duration = 2.0

    # Generate 2 seconds: 0.5s silence, 1s speech, 0.5s silence
    silence1 = np.zeros(int(sample_rate * 0.5))
    speech = np.sin(2 * np.pi * 440 * np.linspace(0, 1, sample_rate)) * 0.5
    silence2 = np.zeros(int(sample_rate * 0.5))

    audio = np.concatenate([silence1, speech, silence2])
    return audio.astype(np.float32)


class TestNormalization:
    """Test audio normalization"""

    def test_normalize_int16(self, processor):
        """Test normalization of int16 audio"""
        audio = np.array([0, 16384, -16384, 32767, -32768], dtype=np.int16)
        normalized = processor.normalize_audio(audio)

        assert normalized.dtype == np.float32
        assert np.all(normalized >= -1.0)
        assert np.all(normalized <= 1.0)
        assert normalized.max() == pytest.approx(1.0, abs=0.01)

    def test_normalize_float32(self, processor):
        """Test normalization of float32 audio"""
        audio = np.array([0.0, 0.5, -0.5, 0.8, -0.8], dtype=np.float32)
        normalized = processor.normalize_audio(audio)

        assert normalized.dtype == np.float32
        assert normalized.max() == pytest.approx(1.0, abs=0.01)

    def test_normalize_stereo_to_mono(self, processor):
        """Test stereo to mono conversion"""
        audio_stereo = np.array([[0.5, 0.3], [0.6, 0.4]], dtype=np.float32)
        normalized = processor.normalize_audio(audio_stereo)

        assert len(normalized.shape) == 1
        assert len(normalized) == 2

    def test_normalize_zero_audio(self, processor):
        """Test normalization of silent audio"""
        audio = np.zeros(1000, dtype=np.float32)
        normalized = processor.normalize_audio(audio)

        assert np.all(normalized == 0.0)


class TestEnergyCalculation:
    """Test energy calculation for VAD"""

    def test_calculate_energy(self, processor):
        """Test energy calculation"""
        # Create audio with varying energy
        silence = np.zeros(1000, dtype=np.float32)
        loud = np.ones(1000, dtype=np.float32) * 0.5

        silence_energy = processor.calculate_energy(silence)
        loud_energy = processor.calculate_energy(loud)

        assert silence_energy.mean() < loud_energy.mean()

    def test_energy_frame_length(self, processor):
        """Test energy calculation with custom frame length"""
        audio = np.random.randn(16000).astype(np.float32) * 0.1

        energy = processor.calculate_energy(audio, frame_length=512)
        expected_frames = len(audio) // 512

        assert len(energy) == expected_frames


class TestVAD:
    """Test Voice Activity Detection"""

    def test_detect_speech_segments(self, processor, sample_audio):
        """Test speech segment detection"""
        segments = processor.detect_speech_segments(sample_audio, sample_rate=16000)

        assert len(segments) > 0

        # Check segments have valid bounds
        for start, end in segments:
            assert 0 <= start < end <= len(sample_audio)

    def test_no_speech_detection(self, processor):
        """Test with silence only"""
        silence = np.zeros(16000, dtype=np.float32)
        segments = processor.detect_speech_segments(silence, sample_rate=16000)

        assert len(segments) == 0

    def test_extract_speech(self, processor, sample_audio):
        """Test speech extraction"""
        speech = processor.extract_speech(sample_audio, sample_rate=16000)

        # Should be shorter than original (removed silence)
        assert len(speech) < len(sample_audio)
        assert len(speech) > 0

    def test_extract_speech_from_silence(self, processor):
        """Test speech extraction from silence"""
        silence = np.zeros(16000, dtype=np.float32)
        speech = processor.extract_speech(silence, sample_rate=16000)

        assert len(speech) == 0

    def test_minimum_speech_duration(self):
        """Test minimum speech duration filter"""
        # Create very short speech segments
        processor = AudioProcessor(
            vad_threshold=0.02,
            vad_min_speech_duration_ms=500,  # 500ms minimum
        )

        sample_rate = 16000
        # Create 100ms speech segment
        short_speech = np.sin(2 * np.pi * 440 * np.linspace(0, 0.1, 1600)) * 0.5
        silence = np.zeros(8000)
        audio = np.concatenate([silence, short_speech, silence])

        segments = processor.detect_speech_segments(audio.astype(np.float32), sample_rate)

        # Should not detect segments shorter than 500ms
        assert len(segments) == 0


class TestResampling:
    """Test audio resampling"""

    def test_resample_downsample(self, processor):
        """Test downsampling"""
        audio = np.random.randn(48000).astype(np.float32)
        resampled = processor.resample(audio, orig_sr=48000, target_sr=16000)

        expected_length = int(len(audio) * 16000 / 48000)
        assert len(resampled) == expected_length

    def test_resample_upsample(self, processor):
        """Test upsampling"""
        audio = np.random.randn(8000).astype(np.float32)
        resampled = processor.resample(audio, orig_sr=8000, target_sr=16000)

        expected_length = int(len(audio) * 16000 / 8000)
        assert len(resampled) == expected_length

    def test_resample_same_rate(self, processor):
        """Test resampling with same sample rate"""
        audio = np.random.randn(16000).astype(np.float32)
        resampled = processor.resample(audio, orig_sr=16000, target_sr=16000)

        np.testing.assert_array_equal(audio, resampled)


class TestSilenceTrimming:
    """Test silence trimming"""

    def test_trim_silence(self, processor, sample_audio):
        """Test silence trimming"""
        trimmed = processor.trim_silence(sample_audio, sample_rate=16000)

        # Should be shorter than original
        assert len(trimmed) < len(sample_audio)
        assert len(trimmed) > 0

    def test_trim_only_silence(self, processor):
        """Test trimming audio with only silence"""
        silence = np.zeros(16000, dtype=np.float32)
        trimmed = processor.trim_silence(silence, sample_rate=16000)

        assert len(trimmed) == 0


class TestHighPassFilter:
    """Test high-pass filter"""

    def test_high_pass_filter(self, processor):
        """Test high-pass filter application"""
        sample_rate = 16000
        duration = 1.0

        # Create low frequency signal (50Hz)
        t = np.linspace(0, duration, int(sample_rate * duration))
        low_freq = np.sin(2 * np.pi * 50 * t)

        filtered = processor.apply_high_pass_filter(
            low_freq.astype(np.float32),
            sample_rate,
            cutoff_freq=80
        )

        # Low frequency should be attenuated
        assert np.abs(filtered).mean() < np.abs(low_freq).mean()

    def test_high_pass_preserves_high_freq(self, processor):
        """Test that high frequencies are preserved"""
        sample_rate = 16000
        duration = 1.0

        # Create high frequency signal (1000Hz)
        t = np.linspace(0, duration, int(sample_rate * duration))
        high_freq = np.sin(2 * np.pi * 1000 * t)

        filtered = processor.apply_high_pass_filter(
            high_freq.astype(np.float32),
            sample_rate,
            cutoff_freq=80
        )

        # High frequency should be mostly preserved
        assert np.abs(filtered).mean() > 0.5 * np.abs(high_freq).mean()


class TestPreprocessingPipeline:
    """Test complete preprocessing pipeline"""

    def test_full_preprocessing(self, processor, sample_audio):
        """Test full preprocessing pipeline"""
        processed = processor.preprocess_for_stt(
            sample_audio,
            sample_rate=16000,
            enable_vad=True,
            enable_filter=False,
            target_sr=16000,
        )

        assert len(processed) > 0
        assert processed.dtype == np.float32

    def test_preprocessing_with_resampling(self, processor):
        """Test preprocessing with resampling"""
        # Create 48kHz audio
        audio = np.random.randn(48000).astype(np.float32) * 0.1

        processed = processor.preprocess_for_stt(
            audio,
            sample_rate=48000,
            enable_vad=False,
            enable_filter=False,
            target_sr=16000,
        )

        # Should be resampled to 16kHz
        expected_length = int(len(audio) * 16000 / 48000)
        assert abs(len(processed) - expected_length) < 100

    def test_preprocessing_with_filter(self, processor, sample_audio):
        """Test preprocessing with high-pass filter"""
        processed = processor.preprocess_for_stt(
            sample_audio,
            sample_rate=16000,
            enable_vad=False,
            enable_filter=True,
            target_sr=16000,
        )

        assert len(processed) > 0
        assert processed.dtype == np.float32
