"""
macOS Accessibility API Tool

Controls macOS applications using the Accessibility API via PyObjC.
Supports clicking buttons, filling fields, reading text, and more.
"""

from typing import Any, Dict, List, Optional

from loguru import logger

from ..validation import ToolValidator, ValidationError

# PyObjC imports for Accessibility API
# Note: These imports will work on actual macOS systems with PyObjC installed
try:
    from ApplicationServices import (
        AXIsProcessTrusted,
        AXUIElementCopyAttributeValue,
        AXUIElementCreateApplication,
        AXUIElementPerformAction,
        kAXButtonRole,
        kAXChildrenAttribute,
        kAXPressAction,
        kAXRoleAttribute,
        kAXTextFieldRole,
        kAXTitleAttribute,
        kAXValueAttribute,
    )
    from AppKit import NSRunningApplication, NSWorkspace

    PYOBJC_AVAILABLE = True
except ImportError:
    logger.warning("PyObjC not available - Accessibility features will be mocked")
    PYOBJC_AVAILABLE = False


class AccessibilityError(Exception):
    """Raised when Accessibility API operations fail"""

    pass


class AccessibilityController:
    """Control macOS applications using Accessibility API"""

    def __init__(self):
        """Initialize Accessibility controller"""
        self.workspace = None
        if PYOBJC_AVAILABLE:
            self.workspace = NSWorkspace.sharedWorkspace()

    def check_accessibility_permission(self) -> bool:
        """
        Check if Accessibility permission is granted

        Returns:
            True if permission granted, False otherwise
        """
        if not PYOBJC_AVAILABLE:
            logger.warning("PyObjC not available - returning mock permission status")
            return False

        return AXIsProcessTrusted()

    async def click_button(
        self, app_name: str, button_title: str, window_index: int = 0
    ) -> str:
        """
        Click a button in an application

        Args:
            app_name: Application name
            button_title: Title/label of button to click
            window_index: Window index (0 = front window)

        Returns:
            Success message

        Raises:
            ValidationError: If app name is invalid
            AccessibilityError: If operation fails
        """
        # Validate app name
        is_valid, error_msg = ToolValidator.validate_app_name(app_name)
        if not is_valid:
            raise ValidationError(error_msg)

        if not PYOBJC_AVAILABLE:
            return f"[Mock] Would click button '{button_title}' in {app_name}"

        # Check permission
        if not self.check_accessibility_permission():
            raise AccessibilityError(
                "Accessibility permission not granted. "
                "Please enable in System Settings > Privacy & Security > Accessibility"
            )

        try:
            # Find running application
            app_element = self._find_application(app_name)
            if not app_element:
                raise AccessibilityError(f"Application '{app_name}' is not running")

            # Find button
            button = self._find_button_by_title(app_element, button_title, window_index)
            if not button:
                raise AccessibilityError(
                    f"Button '{button_title}' not found in {app_name}"
                )

            # Click button
            error = AXUIElementPerformAction(button, kAXPressAction)
            if error:
                raise AccessibilityError(f"Failed to click button (error code: {error})")

            logger.info(f"Clicked button '{button_title}' in {app_name}")
            return f"Successfully clicked '{button_title}' in {app_name}"

        except AccessibilityError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error clicking button: {e}")
            raise AccessibilityError(f"Unexpected error: {str(e)}")

    async def get_text(self, app_name: str, element_type: str = "text") -> str:
        """
        Get text from application element

        Args:
            app_name: Application name
            element_type: Type of element to read ("text", "title", "value")

        Returns:
            Text content

        Raises:
            ValidationError: If app name is invalid
            AccessibilityError: If operation fails
        """
        is_valid, error_msg = ToolValidator.validate_app_name(app_name)
        if not is_valid:
            raise ValidationError(error_msg)

        if not PYOBJC_AVAILABLE:
            return f"[Mock] Text content from {app_name}"

        if not self.check_accessibility_permission():
            raise AccessibilityError("Accessibility permission not granted")

        try:
            app_element = self._find_application(app_name)
            if not app_element:
                raise AccessibilityError(f"Application '{app_name}' is not running")

            # Get window title as a simple example
            value, error = AXUIElementCopyAttributeValue(
                app_element, kAXTitleAttribute, None
            )
            if error:
                raise AccessibilityError(f"Failed to get text (error code: {error})")

            return str(value) if value else ""

        except AccessibilityError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting text: {e}")
            raise AccessibilityError(f"Unexpected error: {str(e)}")

    async def fill_field(
        self, app_name: str, field_label: str, text: str, window_index: int = 0
    ) -> str:
        """
        Fill a text field in an application

        Args:
            app_name: Application name
            field_label: Label/title of field to fill
            text: Text to enter
            window_index: Window index (0 = front window)

        Returns:
            Success message

        Raises:
            ValidationError: If app name is invalid
            AccessibilityError: If operation fails
        """
        is_valid, error_msg = ToolValidator.validate_app_name(app_name)
        if not is_valid:
            raise ValidationError(error_msg)

        if not PYOBJC_AVAILABLE:
            return f"[Mock] Would fill field '{field_label}' with '{text}' in {app_name}"

        if not self.check_accessibility_permission():
            raise AccessibilityError("Accessibility permission not granted")

        try:
            app_element = self._find_application(app_name)
            if not app_element:
                raise AccessibilityError(f"Application '{app_name}' is not running")

            # Find text field
            field = self._find_text_field_by_label(app_element, field_label, window_index)
            if not field:
                raise AccessibilityError(
                    f"Text field '{field_label}' not found in {app_name}"
                )

            # Set value
            error = AXUIElementCopyAttributeValue(field, kAXValueAttribute, text)
            if error:
                raise AccessibilityError(f"Failed to fill field (error code: {error})")

            logger.info(f"Filled field '{field_label}' in {app_name}")
            return f"Successfully filled '{field_label}' in {app_name}"

        except AccessibilityError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error filling field: {e}")
            raise AccessibilityError(f"Unexpected error: {str(e)}")

    def _find_application(self, app_name: str) -> Optional[Any]:
        """
        Find running application by name

        Args:
            app_name: Application name

        Returns:
            AXUIElement for application or None
        """
        if not PYOBJC_AVAILABLE:
            return None

        for app in self.workspace.runningApplications():
            if app.localizedName() == app_name:
                return AXUIElementCreateApplication(app.processIdentifier())

        return None

    def _find_button_by_title(
        self, app_element: Any, title: str, window_index: int = 0
    ) -> Optional[Any]:
        """
        Find button element by title

        Args:
            app_element: Application AXUIElement
            title: Button title to search for
            window_index: Window index

        Returns:
            Button AXUIElement or None
        """
        if not PYOBJC_AVAILABLE:
            return None

        try:
            # Get windows
            windows, error = AXUIElementCopyAttributeValue(
                app_element, kAXChildrenAttribute, None
            )
            if error or not windows or window_index >= len(windows):
                return None

            window = windows[window_index]

            # Recursively search for button
            return self._find_element_recursive(
                window, kAXButtonRole, kAXTitleAttribute, title
            )

        except Exception as e:
            logger.error(f"Error finding button: {e}")
            return None

    def _find_text_field_by_label(
        self, app_element: Any, label: str, window_index: int = 0
    ) -> Optional[Any]:
        """
        Find text field element by label

        Args:
            app_element: Application AXUIElement
            label: Field label to search for
            window_index: Window index

        Returns:
            Text field AXUIElement or None
        """
        if not PYOBJC_AVAILABLE:
            return None

        try:
            windows, error = AXUIElementCopyAttributeValue(
                app_element, kAXChildrenAttribute, None
            )
            if error or not windows or window_index >= len(windows):
                return None

            window = windows[window_index]
            return self._find_element_recursive(
                window, kAXTextFieldRole, kAXTitleAttribute, label
            )

        except Exception as e:
            logger.error(f"Error finding text field: {e}")
            return None

    def _find_element_recursive(
        self,
        element: Any,
        role: str,
        attribute: str,
        value: str,
        max_depth: int = 10,
        current_depth: int = 0,
    ) -> Optional[Any]:
        """
        Recursively search for UI element

        Args:
            element: Current element to search
            role: Element role to match
            attribute: Attribute to check
            value: Value to match
            max_depth: Maximum recursion depth
            current_depth: Current recursion depth

        Returns:
            Matching element or None
        """
        if not PYOBJC_AVAILABLE or current_depth >= max_depth:
            return None

        try:
            # Check if current element matches
            element_role, error = AXUIElementCopyAttributeValue(
                element, kAXRoleAttribute, None
            )
            if not error and element_role == role:
                element_value, error = AXUIElementCopyAttributeValue(
                    element, attribute, None
                )
                if not error and element_value == value:
                    return element

            # Recurse into children
            children, error = AXUIElementCopyAttributeValue(
                element, kAXChildrenAttribute, None
            )
            if not error and children:
                for child in children:
                    result = self._find_element_recursive(
                        child, role, attribute, value, max_depth, current_depth + 1
                    )
                    if result:
                        return result

        except Exception as e:
            logger.debug(f"Error in recursive search: {e}")

        return None


# Example usage
if __name__ == "__main__":
    import asyncio

    async def test_accessibility():
        """Test Accessibility controller"""
        controller = AccessibilityController()

        # Check permission
        has_permission = controller.check_accessibility_permission()
        print(f"Accessibility permission: {has_permission}")

        # Test clicking button (mock on non-macOS)
        result = await controller.click_button("Safari", "Search")
        print(f"Click result: {result}")

    # asyncio.run(test_accessibility())
    print("Accessibility controller ready")
