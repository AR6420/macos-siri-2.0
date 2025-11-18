"""
AppleScript Execution Tool

Executes AppleScript code on macOS with security validation and error handling.
Supports common automation tasks like opening applications, controlling Safari, etc.
"""

import asyncio
import subprocess
from typing import Optional

from loguru import logger

from ..validation import ToolValidator, ValidationError


class AppleScriptError(Exception):
    """Raised when AppleScript execution fails"""

    pass


class AppleScriptExecutor:
    """Execute AppleScript commands with validation and error handling"""

    def __init__(self, timeout: int = 30, sandbox: bool = True):
        """
        Initialize AppleScript executor

        Args:
            timeout: Maximum execution time in seconds
            sandbox: Enable security validation
        """
        self.timeout = timeout
        self.sandbox = sandbox

    async def execute(self, script: str) -> str:
        """
        Execute AppleScript code

        Args:
            script: AppleScript code to execute

        Returns:
            Script output as string

        Raises:
            ValidationError: If script fails validation
            AppleScriptError: If script execution fails
        """
        # Validate script if sandbox enabled
        if self.sandbox:
            is_valid, error_msg = ToolValidator.validate_applescript(script)
            if not is_valid:
                raise ValidationError(f"AppleScript validation failed: {error_msg}")

        try:
            logger.debug(f"Executing AppleScript: {script[:100]}...")

            # Execute via osascript
            process = await asyncio.create_subprocess_exec(
                "osascript",
                "-e",
                script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=self.timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise AppleScriptError(f"Script execution timed out after {self.timeout}s")

            # Check return code
            if process.returncode != 0:
                error_output = stderr.decode("utf-8", errors="replace").strip()
                raise AppleScriptError(f"Script failed with error: {error_output}")

            output = stdout.decode("utf-8", errors="replace").strip()
            logger.debug(f"AppleScript output: {output[:200]}...")

            return ToolValidator.sanitize_output(output)

        except ValidationError:
            raise
        except AppleScriptError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error executing AppleScript: {e}")
            raise AppleScriptError(f"Unexpected error: {str(e)}")


# Common AppleScript templates for typical tasks
class AppleScriptTemplates:
    """Common AppleScript templates for typical automation tasks"""

    @staticmethod
    def open_application(app_name: str) -> str:
        """Generate script to open an application"""
        return f'tell application "{app_name}" to activate'

    @staticmethod
    def quit_application(app_name: str) -> str:
        """Generate script to quit an application"""
        return f'tell application "{app_name}" to quit'

    @staticmethod
    def safari_open_url(url: str) -> str:
        """Generate script to open URL in Safari"""
        return f"""
        tell application "Safari"
            activate
            open location "{url}"
        end tell
        """

    @staticmethod
    def get_window_title(app_name: str) -> str:
        """Generate script to get window title"""
        return f"""
        tell application "{app_name}"
            if (count of windows) > 0 then
                return name of front window
            else
                return "No windows open"
            end if
        end tell
        """

    @staticmethod
    def set_volume(level: int) -> str:
        """
        Generate script to set system volume

        Args:
            level: Volume level 0-100
        """
        level = max(0, min(100, level))
        return f"set volume output volume {level}"

    @staticmethod
    def get_clipboard() -> str:
        """Generate script to get clipboard contents"""
        return "the clipboard as text"

    @staticmethod
    def set_clipboard(text: str) -> str:
        """Generate script to set clipboard contents"""
        # Escape quotes in text
        escaped_text = text.replace('"', '\\"')
        return f'set the clipboard to "{escaped_text}"'

    @staticmethod
    def notification(title: str, message: str) -> str:
        """
        Generate script to show system notification

        Args:
            title: Notification title
            message: Notification message
        """
        return f'display notification "{message}" with title "{title}"'

    @staticmethod
    def get_running_applications() -> str:
        """Generate script to list running applications"""
        return """
        tell application "System Events"
            set appList to name of every process whose background only is false
            return appList as text
        end tell
        """

    @staticmethod
    def finder_get_selection() -> str:
        """Generate script to get Finder selection"""
        return """
        tell application "Finder"
            set selectedItems to selection
            if (count of selectedItems) = 0 then
                return "No items selected"
            else
                set itemNames to {}
                repeat with anItem in selectedItems
                    set end of itemNames to name of anItem
                end repeat
                return itemNames as text
            end if
        end tell
        """

    @staticmethod
    def music_play_pause() -> str:
        """Generate script to play/pause Music"""
        return """
        tell application "Music"
            playpause
        end tell
        """

    @staticmethod
    def music_next_track() -> str:
        """Generate script to skip to next track"""
        return """
        tell application "Music"
            next track
        end tell
        """

    @staticmethod
    def music_get_current_track() -> str:
        """Generate script to get current track info"""
        return """
        tell application "Music"
            if player state is playing then
                set trackName to name of current track
                set trackArtist to artist of current track
                return trackName & " by " & trackArtist
            else
                return "Music is not playing"
            end if
        end tell
        """


# Example usage and testing
if __name__ == "__main__":
    import asyncio

    async def test_applescript():
        """Test AppleScript executor"""
        executor = AppleScriptExecutor(timeout=10, sandbox=True)

        # Test 1: Get date
        result = await executor.execute('return (current date) as text')
        print(f"Date: {result}")

        # Test 2: Open Safari (would actually open Safari on macOS)
        # result = await executor.execute(AppleScriptTemplates.open_application("Safari"))
        # print(f"Opened Safari: {result}")

        # Test 3: Get clipboard
        # result = await executor.execute(AppleScriptTemplates.get_clipboard())
        # print(f"Clipboard: {result}")

    # asyncio.run(test_applescript())
    print("AppleScript executor ready")
