"""
Messages Automation Tool

Sends iMessages and SMS using the macOS Messages app via AppleScript.
Includes user confirmation for security.
"""

from typing import Optional

from loguru import logger

from ..validation import ToolValidator, ValidationError
from .applescript import AppleScriptError, AppleScriptExecutor


class MessagesError(Exception):
    """Raised when message operations fail"""

    pass


class MessagesAutomation:
    """Send messages via Messages app using AppleScript"""

    def __init__(
        self, require_confirmation: bool = True, config: Optional[dict] = None
    ):
        """
        Initialize Messages automation

        Args:
            require_confirmation: Require user confirmation before sending
            config: Optional configuration with allowed contacts
        """
        self.require_confirmation = require_confirmation
        self.config = config or {}
        self.applescript = AppleScriptExecutor(timeout=10, sandbox=True)

    async def send_message(
        self, recipient: str, message: str, platform: str = "imessage"
    ) -> str:
        """
        Send message via Messages app

        Args:
            recipient: Phone number or contact name
            message: Message text to send
            platform: "imessage" or "sms" (currently both use Messages app)

        Returns:
            Success message

        Raises:
            ValidationError: If recipient or message is invalid
            MessagesError: If sending fails
        """
        # Validate recipient
        is_valid_recipient, error_msg = ToolValidator.validate_contact(
            recipient, self.config
        )
        if not is_valid_recipient:
            raise ValidationError(f"Invalid recipient: {error_msg}")

        # Validate message
        is_valid_message, error_msg = ToolValidator.validate_message_content(message)
        if not is_valid_message:
            raise ValidationError(f"Invalid message: {error_msg}")

        # Confirmation check
        if self.require_confirmation:
            logger.warning(
                f"Message sending requires user confirmation: {recipient}: {message[:50]}..."
            )
            return (
                f"Message prepared for {recipient}. "
                f"User confirmation required before sending: '{message[:50]}...'"
            )

        try:
            # Generate AppleScript to send message
            script = self._generate_send_script(recipient, message)

            # Execute script
            result = await self.applescript.execute(script)

            logger.info(f"Sent message to {recipient}")
            return f"Successfully sent message to {recipient}"

        except AppleScriptError as e:
            logger.error(f"Error sending message: {e}")
            raise MessagesError(f"Failed to send message: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error sending message: {e}")
            raise MessagesError(f"Unexpected error: {str(e)}")

    async def get_recent_messages(
        self, contact: Optional[str] = None, count: int = 10
    ) -> str:
        """
        Get recent messages (read-only operation)

        Args:
            contact: Optional contact name to filter
            count: Number of recent messages to retrieve

        Returns:
            Recent messages as formatted string

        Note:
            This is a complex operation requiring database access.
            Implementation simplified for security.
        """
        logger.info(f"Retrieving recent messages (contact={contact}, count={count})")

        # Note: Actual implementation would require accessing Messages database
        # at ~/Library/Messages/chat.db which requires Full Disk Access permission
        # For now, return a note about this limitation

        return (
            "Reading messages requires Full Disk Access permission and "
            "direct database access. This feature is not yet fully implemented "
            "for security and privacy reasons."
        )

    def _generate_send_script(self, recipient: str, message: str) -> str:
        """
        Generate AppleScript to send message

        Args:
            recipient: Phone number or contact name
            message: Message text

        Returns:
            AppleScript code as string
        """
        # Escape quotes and special characters in message
        escaped_message = message.replace('"', '\\"').replace("\n", "\\n")
        escaped_recipient = recipient.replace('"', '\\"')

        script = f"""
        tell application "Messages"
            set targetService to 1st account whose service type = iMessage
            set targetBuddy to participant "{escaped_recipient}" of targetService
            send "{escaped_message}" to targetBuddy
        end tell
        """

        return script

    async def check_messages_running(self) -> bool:
        """
        Check if Messages app is running

        Returns:
            True if Messages is running, False otherwise
        """
        try:
            script = """
            tell application "System Events"
                return (name of processes) contains "Messages"
            end tell
            """
            result = await self.applescript.execute(script)
            return result.strip().lower() == "true"

        except Exception as e:
            logger.error(f"Error checking Messages status: {e}")
            return False

    async def open_messages(self) -> str:
        """
        Open Messages app

        Returns:
            Success message
        """
        try:
            script = 'tell application "Messages" to activate'
            await self.applescript.execute(script)
            logger.info("Opened Messages app")
            return "Successfully opened Messages app"

        except AppleScriptError as e:
            logger.error(f"Error opening Messages: {e}")
            raise MessagesError(f"Failed to open Messages: {str(e)}")

    async def get_contacts(self) -> str:
        """
        Get list of contacts from Messages

        Returns:
            List of contacts as formatted string
        """
        try:
            script = """
            tell application "Messages"
                set contactList to {}
                repeat with aPerson in participants
                    set end of contactList to name of aPerson
                end repeat
                return contactList as text
            end tell
            """

            result = await self.applescript.execute(script)
            return f"Contacts: {result}"

        except AppleScriptError as e:
            logger.warning(f"Could not retrieve contacts: {e}")
            return "Unable to retrieve contacts. Messages may not have any active conversations."


# Example usage
if __name__ == "__main__":
    import asyncio

    async def test_messages():
        """Test Messages automation"""
        messages = MessagesAutomation(require_confirmation=True)

        # Test checking if Messages is running
        is_running = await messages.check_messages_running()
        print(f"Messages running: {is_running}")

        # Test send message (will require confirmation)
        result = await messages.send_message(
            recipient="+1234567890",
            message="Hello from Voice Assistant!",
        )
        print(f"Send result: {result}")

    # asyncio.run(test_messages())
    print("Messages automation ready")
