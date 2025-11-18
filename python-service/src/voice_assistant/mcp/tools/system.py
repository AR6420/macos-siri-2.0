"""
System Information & Web Search Tools

Provides system status queries and web search functionality.
"""

import asyncio
import platform
from datetime import datetime
from typing import Optional

import psutil
from duckduckgo_search import DDGS
from loguru import logger

from ..validation import ToolValidator, ValidationError


class SystemError(Exception):
    """Raised when system operations fail"""

    pass


class WebSearchError(Exception):
    """Raised when web search fails"""

    pass


class SystemInfo:
    """Retrieve macOS system information"""

    @staticmethod
    async def get_battery_status() -> str:
        """
        Get battery status

        Returns:
            Battery status as formatted string
        """
        try:
            battery = psutil.sensors_battery()

            if battery is None:
                return "No battery found (desktop system)"

            percent = battery.percent
            plugged = "Plugged in" if battery.power_plugged else "On battery"
            time_left = ""

            if not battery.power_plugged and battery.secsleft != psutil.POWER_TIME_UNLIMITED:
                hours = battery.secsleft // 3600
                minutes = (battery.secsleft % 3600) // 60
                time_left = f", {hours}h {minutes}m remaining"

            status = f"Battery: {percent}% ({plugged}{time_left})"
            logger.debug(f"Battery status: {status}")

            return status

        except Exception as e:
            logger.error(f"Error getting battery status: {e}")
            raise SystemError(f"Failed to get battery status: {str(e)}")

    @staticmethod
    async def get_disk_usage(path: str = "/") -> str:
        """
        Get disk usage for path

        Args:
            path: Path to check (default: root)

        Returns:
            Disk usage as formatted string
        """
        try:
            usage = psutil.disk_usage(path)

            total_gb = usage.total / (1024**3)
            used_gb = usage.used / (1024**3)
            free_gb = usage.free / (1024**3)
            percent = usage.percent

            status = (
                f"Disk Usage ({path}):\n"
                f"  Total: {total_gb:.1f} GB\n"
                f"  Used: {used_gb:.1f} GB ({percent}%)\n"
                f"  Free: {free_gb:.1f} GB"
            )

            logger.debug(f"Disk usage: {percent}%")
            return status

        except Exception as e:
            logger.error(f"Error getting disk usage: {e}")
            raise SystemError(f"Failed to get disk usage: {str(e)}")

    @staticmethod
    async def get_memory_usage() -> str:
        """
        Get memory usage

        Returns:
            Memory usage as formatted string
        """
        try:
            memory = psutil.virtual_memory()

            total_gb = memory.total / (1024**3)
            used_gb = memory.used / (1024**3)
            available_gb = memory.available / (1024**3)
            percent = memory.percent

            status = (
                f"Memory Usage:\n"
                f"  Total: {total_gb:.1f} GB\n"
                f"  Used: {used_gb:.1f} GB ({percent}%)\n"
                f"  Available: {available_gb:.1f} GB"
            )

            logger.debug(f"Memory usage: {percent}%")
            return status

        except Exception as e:
            logger.error(f"Error getting memory usage: {e}")
            raise SystemError(f"Failed to get memory usage: {str(e)}")

    @staticmethod
    async def get_cpu_usage() -> str:
        """
        Get CPU usage

        Returns:
            CPU usage as formatted string
        """
        try:
            # Get per-CPU percentages
            cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
            avg_percent = sum(cpu_percent) / len(cpu_percent)

            cpu_count = psutil.cpu_count(logical=True)
            cpu_count_physical = psutil.cpu_count(logical=False)

            status = (
                f"CPU Usage:\n"
                f"  Average: {avg_percent:.1f}%\n"
                f"  Cores: {cpu_count_physical} physical, {cpu_count} logical"
            )

            logger.debug(f"CPU usage: {avg_percent:.1f}%")
            return status

        except Exception as e:
            logger.error(f"Error getting CPU usage: {e}")
            raise SystemError(f"Failed to get CPU usage: {str(e)}")

    @staticmethod
    async def get_network_status() -> str:
        """
        Get network status

        Returns:
            Network status as formatted string
        """
        try:
            # Get network interfaces
            interfaces = psutil.net_if_addrs()
            active_interfaces = []

            for interface_name, addresses in interfaces.items():
                # Skip loopback
                if interface_name.startswith("lo"):
                    continue

                # Look for IPv4 address
                for addr in addresses:
                    if addr.family == 2:  # AF_INET (IPv4)
                        active_interfaces.append(f"{interface_name}: {addr.address}")

            if not active_interfaces:
                return "Network: No active interfaces found"

            status = "Network Interfaces:\n  " + "\n  ".join(active_interfaces)

            logger.debug(f"Network status: {len(active_interfaces)} active interfaces")
            return status

        except Exception as e:
            logger.error(f"Error getting network status: {e}")
            raise SystemError(f"Failed to get network status: {str(e)}")

    @staticmethod
    async def get_system_info() -> str:
        """
        Get comprehensive system information

        Returns:
            System info as formatted string
        """
        try:
            system = platform.system()
            release = platform.release()
            version = platform.version()
            machine = platform.machine()
            processor = platform.processor()

            status = (
                f"System Information:\n"
                f"  OS: {system} {release}\n"
                f"  Version: {version}\n"
                f"  Architecture: {machine}\n"
                f"  Processor: {processor}"
            )

            logger.debug("Retrieved system information")
            return status

        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            raise SystemError(f"Failed to get system info: {str(e)}")

    @staticmethod
    async def get_running_apps() -> str:
        """
        Get list of running applications

        Returns:
            List of running apps as formatted string
        """
        try:
            processes = []

            for proc in psutil.process_iter(["name", "cpu_percent", "memory_percent"]):
                try:
                    # Filter for apps (not system processes)
                    name = proc.info["name"]

                    # Skip system processes and daemons
                    if name.endswith("d") or name.startswith("com."):
                        continue

                    cpu = proc.info["cpu_percent"] or 0
                    mem = proc.info["memory_percent"] or 0

                    # Only include processes with significant resource usage or common apps
                    if cpu > 0.1 or mem > 0.1 or name in [
                        "Safari",
                        "Chrome",
                        "Firefox",
                        "Messages",
                        "Mail",
                        "Music",
                        "Finder",
                    ]:
                        processes.append(
                            {
                                "name": name,
                                "cpu": cpu,
                                "mem": mem,
                            }
                        )

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Sort by CPU usage
            processes.sort(key=lambda x: x["cpu"], reverse=True)

            # Take top 10
            processes = processes[:10]

            if not processes:
                return "No significant applications running"

            status_lines = ["Running Applications:"]
            for proc in processes:
                status_lines.append(
                    f"  {proc['name']:20} - CPU: {proc['cpu']:>5.1f}%, "
                    f"Memory: {proc['mem']:>5.1f}%"
                )

            status = "\n".join(status_lines)

            logger.debug(f"Retrieved {len(processes)} running apps")
            return status

        except Exception as e:
            logger.error(f"Error getting running apps: {e}")
            raise SystemError(f"Failed to get running apps: {str(e)}")

    @staticmethod
    async def get_datetime() -> str:
        """
        Get current date and time

        Returns:
            Current date/time as formatted string
        """
        now = datetime.now()
        return now.strftime("%A, %B %d, %Y at %I:%M %p")


class WebSearch:
    """Web search using DuckDuckGo"""

    def __init__(self, config: Optional[dict] = None):
        """
        Initialize web search

        Args:
            config: Optional configuration with engine, max_results, timeout
        """
        self.config = config or {
            "engine": "duckduckgo",
            "max_results": 5,
            "timeout": 10,
        }

    async def search(self, query: str, num_results: Optional[int] = None) -> str:
        """
        Search the web and return results

        Args:
            query: Search query
            num_results: Number of results to return (overrides config)

        Returns:
            Search results as formatted string

        Raises:
            ValidationError: If query is invalid
            WebSearchError: If search fails
        """
        # Validate query
        is_valid, error_msg = ToolValidator.validate_web_query(query)
        if not is_valid:
            raise ValidationError(f"Invalid query: {error_msg}")

        max_results = num_results or self.config.get("max_results", 5)

        try:
            logger.info(f"Searching web for: {query}")

            # Run blocking search in thread pool
            results = await asyncio.get_event_loop().run_in_executor(
                None, self._search_ddg, query, max_results
            )

            if not results:
                return f"No results found for: {query}"

            # Format results
            formatted_results = [f"Web search results for '{query}':\n"]

            for i, result in enumerate(results, 1):
                title = result.get("title", "No title")
                snippet = result.get("body", "No description")
                url = result.get("href", "")

                formatted_results.append(f"{i}. {title}")
                formatted_results.append(f"   {snippet}")
                formatted_results.append(f"   URL: {url}\n")

            output = "\n".join(formatted_results)

            logger.info(f"Found {len(results)} results for: {query}")
            return ToolValidator.sanitize_output(output)

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error searching web: {e}")
            raise WebSearchError(f"Failed to search web: {str(e)}")

    def _search_ddg(self, query: str, max_results: int) -> list:
        """
        Perform DuckDuckGo search (blocking)

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of search result dictionaries
        """
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                return results

        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            raise


# Example usage
if __name__ == "__main__":
    import asyncio

    async def test_system_info():
        """Test system info"""
        # Test battery status
        battery = await SystemInfo.get_battery_status()
        print(battery)

        # Test disk usage
        disk = await SystemInfo.get_disk_usage()
        print(disk)

        # Test memory usage
        memory = await SystemInfo.get_memory_usage()
        print(memory)

        # Test date/time
        dt = await SystemInfo.get_datetime()
        print(dt)

    async def test_web_search():
        """Test web search"""
        search = WebSearch()
        results = await search.search("macOS Tahoe features", num_results=3)
        print(results)

    # asyncio.run(test_system_info())
    # asyncio.run(test_web_search())
    print("System info and web search ready")
