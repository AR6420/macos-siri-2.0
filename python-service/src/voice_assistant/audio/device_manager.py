"""
Audio Device Manager

Handles audio input device selection, enumeration, and management.
"""

import pyaudio
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)


class AudioDeviceManager:
    """
    Manages audio input devices for the voice assistant.

    Provides device enumeration, selection, and validation.
    """

    def __init__(self):
        """Initialize audio device manager."""
        self.pyaudio = pyaudio.PyAudio()
        self._default_device_index: Optional[int] = None
        logger.info("Audio device manager initialized")

    def list_input_devices(self) -> List[Dict]:
        """
        List all available audio input devices.

        Returns:
            List of device info dictionaries containing:
                - index: Device index
                - name: Device name
                - channels: Max input channels
                - sample_rate: Default sample rate
                - is_default: Whether this is the system default
        """
        devices = []

        try:
            default_input = self.pyaudio.get_default_input_device_info()
            default_index = default_input['index']
        except Exception as e:
            logger.warning(f"Could not get default input device: {e}")
            default_index = None

        for i in range(self.pyaudio.get_device_count()):
            try:
                info = self.pyaudio.get_device_info_by_index(i)

                # Only include input devices
                if info['maxInputChannels'] > 0:
                    devices.append({
                        'index': i,
                        'name': info['name'],
                        'channels': info['maxInputChannels'],
                        'sample_rate': int(info['defaultSampleRate']),
                        'is_default': i == default_index
                    })
            except Exception as e:
                logger.warning(f"Error getting info for device {i}: {e}")
                continue

        logger.info(f"Found {len(devices)} input devices")
        return devices

    def get_device_by_name(self, name: str) -> Optional[Dict]:
        """
        Find audio device by name.

        Args:
            name: Device name (case-insensitive, partial match)

        Returns:
            Device info dict or None if not found
        """
        devices = self.list_input_devices()
        name_lower = name.lower()

        for device in devices:
            if name_lower in device['name'].lower():
                logger.info(f"Found device matching '{name}': {device['name']}")
                return device

        logger.warning(f"No device found matching '{name}'")
        return None

    def get_device_by_index(self, index: int) -> Optional[Dict]:
        """
        Get device info by index.

        Args:
            index: Device index

        Returns:
            Device info dict or None if invalid
        """
        try:
            info = self.pyaudio.get_device_info_by_index(index)

            if info['maxInputChannels'] > 0:
                return {
                    'index': index,
                    'name': info['name'],
                    'channels': info['maxInputChannels'],
                    'sample_rate': int(info['defaultSampleRate']),
                    'is_default': False  # Will be updated if needed
                }
        except Exception as e:
            logger.error(f"Error getting device {index}: {e}")

        return None

    def get_default_device(self) -> Dict:
        """
        Get the system default input device.

        Returns:
            Default device info dict

        Raises:
            RuntimeError: If no default device available
        """
        try:
            info = self.pyaudio.get_default_input_device_info()
            return {
                'index': info['index'],
                'name': info['name'],
                'channels': info['maxInputChannels'],
                'sample_rate': int(info['defaultSampleRate']),
                'is_default': True
            }
        except Exception as e:
            logger.error(f"Failed to get default input device: {e}")
            raise RuntimeError("No default audio input device available") from e

    def validate_device(
        self,
        device_index: int,
        sample_rate: int = 16000,
        channels: int = 1
    ) -> bool:
        """
        Validate that a device supports the required audio format.

        Args:
            device_index: Device index to validate
            sample_rate: Required sample rate
            channels: Required number of channels

        Returns:
            True if device supports the format, False otherwise
        """
        try:
            # Try to check if format is supported
            is_supported = self.pyaudio.is_format_supported(
                sample_rate,
                input_device=device_index,
                input_channels=channels,
                input_format=pyaudio.paInt16
            )

            if is_supported:
                logger.info(
                    f"Device {device_index} supports "
                    f"{sample_rate}Hz, {channels}ch, int16"
                )
            else:
                logger.warning(
                    f"Device {device_index} does not support "
                    f"{sample_rate}Hz, {channels}ch, int16"
                )

            return is_supported

        except Exception as e:
            logger.error(f"Error validating device {device_index}: {e}")
            return False

    def select_device(
        self,
        device_name: Optional[str] = None,
        device_index: Optional[int] = None
    ) -> Dict:
        """
        Select audio input device.

        Priority:
        1. device_index if provided and valid
        2. device_name if provided and found
        3. System default device

        Args:
            device_name: Device name to search for (partial match)
            device_index: Specific device index to use

        Returns:
            Selected device info dict

        Raises:
            RuntimeError: If no suitable device found
        """
        # Try device index first
        if device_index is not None:
            device = self.get_device_by_index(device_index)
            if device:
                logger.info(f"Selected device by index: {device['name']}")
                self._default_device_index = device['index']
                return device
            else:
                logger.warning(f"Invalid device index: {device_index}")

        # Try device name
        if device_name and device_name.lower() != "default":
            device = self.get_device_by_name(device_name)
            if device:
                logger.info(f"Selected device by name: {device['name']}")
                self._default_device_index = device['index']
                return device
            else:
                logger.warning(f"Device '{device_name}' not found")

        # Fall back to system default
        device = self.get_default_device()
        logger.info(f"Using default device: {device['name']}")
        self._default_device_index = device['index']
        return device

    def close(self) -> None:
        """Cleanup PyAudio resources."""
        if self.pyaudio:
            self.pyaudio.terminate()
            self.pyaudio = None
            logger.info("Audio device manager closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def __del__(self):
        """Cleanup on deletion."""
        self.close()

    def __repr__(self) -> str:
        num_devices = self.pyaudio.get_device_count() if self.pyaudio else 0
        return f"AudioDeviceManager(devices={num_devices})"
