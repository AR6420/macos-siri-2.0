"""
File Operations Tool

Provides secure file system operations including read, write, list, delete, move, and copy.
All operations are sandboxed to home directory for security.
"""

import os
import shutil
from pathlib import Path
from typing import Optional

import aiofiles
from loguru import logger

from ..validation import ToolValidator, ValidationError


class FileOperationError(Exception):
    """Raised when file operations fail"""

    pass


class FileOperations:
    """Secure file operations with sandboxing"""

    def __init__(self, config: Optional[dict] = None):
        """
        Initialize file operations

        Args:
            config: Optional configuration with allowed/blocked paths
        """
        self.config = config or {
            "allowed_paths": [
                "~/Documents",
                "~/Downloads",
                "~/Desktop",
                "~/Pictures",
                "~/Music",
                "~/Videos",
            ],
            "blocked_paths": ["~/.ssh", "~/.gnupg"],
        }

    async def read(self, path: str, max_size_mb: int = 10) -> str:
        """
        Read file contents

        Args:
            path: File path to read
            max_size_mb: Maximum file size in MB

        Returns:
            File contents as string

        Raises:
            ValidationError: If path is invalid
            FileOperationError: If read fails
        """
        # Validate path
        is_valid, error_msg, resolved_path = ToolValidator.validate_file_path(
            path, operation="read", config=self.config
        )
        if not is_valid:
            raise ValidationError(f"Invalid path: {error_msg}")

        try:
            # Check if file exists
            if not resolved_path.exists():
                raise FileOperationError(f"File does not exist: {path}")

            if not resolved_path.is_file():
                raise FileOperationError(f"Path is not a file: {path}")

            # Check file size
            file_size_mb = resolved_path.stat().st_size / (1024 * 1024)
            if file_size_mb > max_size_mb:
                raise FileOperationError(
                    f"File too large ({file_size_mb:.1f}MB). Maximum: {max_size_mb}MB"
                )

            # Read file asynchronously
            async with aiofiles.open(resolved_path, mode="r", encoding="utf-8") as f:
                content = await f.read()

            logger.info(f"Read file: {resolved_path} ({len(content)} bytes)")
            return ToolValidator.sanitize_output(content)

        except FileOperationError:
            raise
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error reading file {path}: {e}")
            raise FileOperationError(f"Failed to read file: {str(e)}")

    async def write(self, path: str, content: str, overwrite: bool = False) -> str:
        """
        Write content to file

        Args:
            path: File path to write
            content: Content to write
            overwrite: Allow overwriting existing file

        Returns:
            Success message

        Raises:
            ValidationError: If path is invalid
            FileOperationError: If write fails
        """
        # Validate path
        is_valid, error_msg, resolved_path = ToolValidator.validate_file_path(
            path, operation="write", config=self.config
        )
        if not is_valid:
            raise ValidationError(f"Invalid path: {error_msg}")

        try:
            # Check if file exists
            if resolved_path.exists() and not overwrite:
                raise FileOperationError(
                    f"File already exists: {path}. Use overwrite=True to replace."
                )

            # Create parent directory if needed
            resolved_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file asynchronously
            async with aiofiles.open(resolved_path, mode="w", encoding="utf-8") as f:
                await f.write(content)

            logger.info(f"Wrote file: {resolved_path} ({len(content)} bytes)")
            return f"Successfully wrote {len(content)} bytes to {path}"

        except FileOperationError:
            raise
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error writing file {path}: {e}")
            raise FileOperationError(f"Failed to write file: {str(e)}")

    async def list_directory(self, path: str, include_hidden: bool = False) -> str:
        """
        List directory contents

        Args:
            path: Directory path to list
            include_hidden: Include hidden files (starting with .)

        Returns:
            Directory listing as formatted string

        Raises:
            ValidationError: If path is invalid
            FileOperationError: If listing fails
        """
        # Validate path
        is_valid, error_msg, resolved_path = ToolValidator.validate_file_path(
            path, operation="read", config=self.config
        )
        if not is_valid:
            raise ValidationError(f"Invalid path: {error_msg}")

        try:
            # Check if directory exists
            if not resolved_path.exists():
                raise FileOperationError(f"Directory does not exist: {path}")

            if not resolved_path.is_dir():
                raise FileOperationError(f"Path is not a directory: {path}")

            # List contents
            entries = []
            for item in sorted(resolved_path.iterdir()):
                # Skip hidden files if requested
                if not include_hidden and item.name.startswith("."):
                    continue

                item_type = "DIR" if item.is_dir() else "FILE"
                size = item.stat().st_size if item.is_file() else 0
                size_str = self._format_size(size)

                entries.append(f"{item_type:6} {size_str:>10}  {item.name}")

            if not entries:
                return f"Directory is empty: {path}"

            result = f"Contents of {path}:\n" + "\n".join(entries)
            logger.info(f"Listed directory: {resolved_path} ({len(entries)} items)")

            return ToolValidator.sanitize_output(result)

        except FileOperationError:
            raise
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error listing directory {path}: {e}")
            raise FileOperationError(f"Failed to list directory: {str(e)}")

    async def delete(self, path: str, recursive: bool = False) -> str:
        """
        Delete file or directory

        Args:
            path: Path to delete
            recursive: Allow deleting non-empty directories

        Returns:
            Success message

        Raises:
            ValidationError: If path is invalid
            FileOperationError: If deletion fails
        """
        # Validate path
        is_valid, error_msg, resolved_path = ToolValidator.validate_file_path(
            path, operation="delete", config=self.config
        )
        if not is_valid:
            raise ValidationError(f"Invalid path: {error_msg}")

        try:
            # Check if exists
            if not resolved_path.exists():
                raise FileOperationError(f"Path does not exist: {path}")

            # Delete
            if resolved_path.is_file():
                resolved_path.unlink()
                logger.info(f"Deleted file: {resolved_path}")
                return f"Successfully deleted file: {path}"
            elif resolved_path.is_dir():
                if recursive:
                    shutil.rmtree(resolved_path)
                    logger.info(f"Deleted directory recursively: {resolved_path}")
                    return f"Successfully deleted directory: {path}"
                else:
                    resolved_path.rmdir()  # Will fail if not empty
                    logger.info(f"Deleted empty directory: {resolved_path}")
                    return f"Successfully deleted empty directory: {path}"
            else:
                raise FileOperationError(f"Unknown file type: {path}")

        except FileOperationError:
            raise
        except ValidationError:
            raise
        except OSError as e:
            if "Directory not empty" in str(e):
                raise FileOperationError(
                    f"Directory not empty: {path}. Use recursive=True to delete."
                )
            logger.error(f"Error deleting {path}: {e}")
            raise FileOperationError(f"Failed to delete: {str(e)}")
        except Exception as e:
            logger.error(f"Error deleting {path}: {e}")
            raise FileOperationError(f"Failed to delete: {str(e)}")

    async def move(self, source: str, destination: str) -> str:
        """
        Move file or directory

        Args:
            source: Source path
            destination: Destination path

        Returns:
            Success message

        Raises:
            ValidationError: If paths are invalid
            FileOperationError: If move fails
        """
        # Validate paths
        is_valid_src, error_msg_src, resolved_src = ToolValidator.validate_file_path(
            source, operation="move", config=self.config
        )
        if not is_valid_src:
            raise ValidationError(f"Invalid source path: {error_msg_src}")

        is_valid_dst, error_msg_dst, resolved_dst = ToolValidator.validate_file_path(
            destination, operation="move", config=self.config
        )
        if not is_valid_dst:
            raise ValidationError(f"Invalid destination path: {error_msg_dst}")

        try:
            # Check if source exists
            if not resolved_src.exists():
                raise FileOperationError(f"Source does not exist: {source}")

            # Check if destination exists
            if resolved_dst.exists():
                raise FileOperationError(
                    f"Destination already exists: {destination}"
                )

            # Create destination parent directory
            resolved_dst.parent.mkdir(parents=True, exist_ok=True)

            # Move
            shutil.move(str(resolved_src), str(resolved_dst))

            logger.info(f"Moved {resolved_src} to {resolved_dst}")
            return f"Successfully moved {source} to {destination}"

        except FileOperationError:
            raise
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error moving {source} to {destination}: {e}")
            raise FileOperationError(f"Failed to move: {str(e)}")

    async def copy(self, source: str, destination: str) -> str:
        """
        Copy file or directory

        Args:
            source: Source path
            destination: Destination path

        Returns:
            Success message

        Raises:
            ValidationError: If paths are invalid
            FileOperationError: If copy fails
        """
        # Validate paths
        is_valid_src, error_msg_src, resolved_src = ToolValidator.validate_file_path(
            source, operation="read", config=self.config
        )
        if not is_valid_src:
            raise ValidationError(f"Invalid source path: {error_msg_src}")

        is_valid_dst, error_msg_dst, resolved_dst = ToolValidator.validate_file_path(
            destination, operation="write", config=self.config
        )
        if not is_valid_dst:
            raise ValidationError(f"Invalid destination path: {error_msg_dst}")

        try:
            # Check if source exists
            if not resolved_src.exists():
                raise FileOperationError(f"Source does not exist: {source}")

            # Check if destination exists
            if resolved_dst.exists():
                raise FileOperationError(
                    f"Destination already exists: {destination}"
                )

            # Create destination parent directory
            resolved_dst.parent.mkdir(parents=True, exist_ok=True)

            # Copy
            if resolved_src.is_file():
                shutil.copy2(str(resolved_src), str(resolved_dst))
            elif resolved_src.is_dir():
                shutil.copytree(str(resolved_src), str(resolved_dst))
            else:
                raise FileOperationError(f"Unknown file type: {source}")

            logger.info(f"Copied {resolved_src} to {resolved_dst}")
            return f"Successfully copied {source} to {destination}"

        except FileOperationError:
            raise
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error copying {source} to {destination}: {e}")
            raise FileOperationError(f"Failed to copy: {str(e)}")

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format file size in human-readable format"""
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f}TB"


# Example usage
if __name__ == "__main__":
    import asyncio

    async def test_file_operations():
        """Test file operations"""
        file_ops = FileOperations()

        # Test listing directory
        result = await file_ops.list_directory("~/Documents")
        print(f"Directory listing:\n{result}")

        # Test write
        # await file_ops.write("~/Documents/test.txt", "Hello, World!", overwrite=True)

        # Test read
        # content = await file_ops.read("~/Documents/test.txt")
        # print(f"File content: {content}")

    # asyncio.run(test_file_operations())
    print("File operations ready")
