#!/usr/bin/env python3
"""
RAM Usage Visualization Tool

Generates a treemap visualization of system memory usage by process.
This script collects memory information for all running processes
and renders it as a treemap where rectangle size represents memory consumption.
"""

import os
import sys
import json
import logging
import argparse
from typing import Dict, List, Tuple, Optional, Any, Set, cast
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.figure import Figure
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
import psutil
import squarify
import numpy as np


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("memusg")


class ProcessMemoryInfo:
    """Represents memory information for a single process."""

    def __init__(self, pid: int, name: str, memory_mb: float, username: str = "", cmdline: Optional[List[str]] = None):
        """
        Initialize process memory information.

        Args:
            pid: Process ID
            name: Process name
            memory_mb: Memory usage in megabytes
            username: Username of the process owner
            cmdline: Command line arguments used to launch the process
        """
        self.pid = pid
        self.name = name
        self.memory_mb = memory_mb
        self.username = username
        self.cmdline = cmdline or []

        # Create a display name by combining process name and first argument if available
        self.display_name = self.name
        if len(self.cmdline) > 1 and not self.name.startswith('/'):
            arg = os.path.basename(self.cmdline[1]) if self.cmdline[1] else ""
            if arg and len(arg) < 20:
                self.display_name = f"{self.name} ({arg})"

    def __repr__(self) -> str:
        return f"ProcessMemoryInfo(pid={self.pid}, name='{self.name}', memory_mb={self.memory_mb:.1f}, user='{self.username}')"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "pid": self.pid,
            "name": self.name,
            "memory_mb": round(self.memory_mb, 2),
            "username": self.username,
            "cmdline": self.cmdline,
            "display_name": self.display_name
        }


def collect_process_memory_info(
    min_memory_mb: float = 1.0,
    exclude_pids: Optional[Set[int]] = None,
    exclude_users: Optional[Set[str]] = None
) -> List[ProcessMemoryInfo]:
    """
    Collect memory usage information for all running processes.

    Args:
        min_memory_mb: Minimum memory usage threshold in MB
        exclude_pids: Set of process IDs to exclude
        exclude_users: Set of usernames to exclude

    Returns:
        List of ProcessMemoryInfo objects sorted by memory usage (descending)
    """
    processes = []
    exclude_pids = exclude_pids or set()
    exclude_users = exclude_users or set()

    try:
        for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'username', 'cmdline']):  # pyright: ignore[reportPossiblyUnboundVariable]
            try:
                process_info = proc.info
                pid = process_info['pid']
                username = process_info.get('username', '')

                # Apply filters
                if pid in exclude_pids or (username and username in exclude_users):
                    continue

                mem_usage_mb = process_info['memory_info'].rss / (1024 * 1024)

                if mem_usage_mb >= min_memory_mb:
                    processes.append(ProcessMemoryInfo(
                        pid=pid,
                        name=process_info['name'],
                        memory_mb=mem_usage_mb,
                        username=username,
                        cmdline=process_info.get('cmdline', [])
                    ))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                logger.debug(f"Skipping process: {e}")
    except Exception as e:
        logger.error(f"Error collecting process information: {e}")
        raise

    # Sort by memory usage (descending)
    return sorted(processes, key=lambda p: p.memory_mb, reverse=True)


def get_system_memory_info() -> Dict[str, Any]:
    """
    Get system-wide memory information.

    Returns:
        Dictionary with system memory details
    """
    try:
        mem = psutil.virtual_memory()  # pyright: ignore[reportPossiblyUnboundVariable]
        swap = psutil.swap_memory()  # pyright: ignore[reportPossiblyUnboundVariable]
        return {
            'total_gb': mem.total / (1024**3),
            'used_gb': mem.used / (1024**3),
            'available_gb': mem.available / (1024**3),
            'percent': mem.percent,
            'swap_total_gb': swap.total / (1024**3),
            'swap_used_gb': swap.used / (1024**3),
            'swap_percent': swap.percent
        }
    except Exception as e:
        logger.error(f"Error getting system memory information: {e}")
        raise


def group_processes_by_attribute(processes: List[ProcessMemoryInfo],
                                attribute: Optional[str] = None) -> List[ProcessMemoryInfo]:
    """
    Group processes by a specified attribute.

    Args:
        processes: List of process memory information
        attribute: Attribute to group by ('username' or None)

    Returns:
        List of grouped ProcessMemoryInfo objects
    """
    if not attribute or attribute not in ('username',):
        return processes

    # Type alias for group keys
    grouped_data: Dict[str, Dict[str, Any]] = {}

    for proc in processes:
        key = cast(str, getattr(proc, attribute, "unknown"))

        if not key or key == "":
            key = "unknown"

        if key not in grouped_data:
            grouped_data[key] = {
                'name': f"{key} (group)",
                'memory_mb': 0.0,
                'username': key if attribute == 'username' else "",
                'processes': []
            }

        grouped_data[key]['memory_mb'] += proc.memory_mb
        grouped_data[key]['processes'].append(proc)

    # Convert grouped data back to ProcessMemoryInfo objects
    grouped_processes = []

    for key, data in grouped_data.items():
        process_list = cast(List[ProcessMemoryInfo], data['processes'])
        # Choose a representative PID from the group
        if process_list:
            # Use the PID with highest memory usage
            pid = max(process_list, key=lambda p: p.memory_mb).pid
        else:
            pid = 0

        grouped_processes.append(ProcessMemoryInfo(
            pid=pid,
            name=data['name'],
            memory_mb=data['memory_mb'],
            username=key if attribute == 'username' else ""
        ))

    # Sort by memory usage (descending)
    return sorted(grouped_processes, key=lambda p: p.memory_mb, reverse=True)


def get_truncated_text(text: str, max_length: int = 30) -> str:
    """
    Truncate text if it exceeds maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum allowed length

    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + '...'


def _create_empty_figure() -> Tuple["Figure", Any]:
    """Create an empty figure when no processes are available to visualize."""
    fig, ax = plt.subplots(figsize=(8, 6))  # pyright: ignore[reportPossiblyUnboundVariable]
    ax.text(0.5, 0.5, "No processes found meeting the minimum memory threshold",
            ha='center', va='center', fontsize=14)
    ax.axis('off')
    return fig, ax


def _get_colormap(cmap_name: str):
    """Get colormap using the appropriate matplotlib API."""
    try:
        # Use the newer recommended API (for Matplotlib 3.7+)
        if hasattr(plt, 'colormaps'):  # pyright: ignore[reportPossiblyUnboundVariable]
            cmap = plt.colormaps[cmap_name]  # pyright: ignore[reportPossiblyUnboundVariable]
        # Fallback for older Matplotlib versions
        else:
            cmap = plt.get_cmap(cmap_name)  # pyright: ignore[reportPossiblyUnboundVariable]
    except Exception as e:
        logger.warning(f"Error using preferred colormap API, falling back to older method: {e}")
        cmap = plt.cm.get_cmap(cmap_name)  # pyright: ignore[reportPossiblyUnboundVariable]
    return cmap


def _get_colors_by_username(processes: List[ProcessMemoryInfo], cmap):
    """Create colors based on unique usernames."""
    usernames: List[str] = list(set(p.username for p in processes))
    username_to_idx: Dict[str, int] = {name: i for i, name in enumerate(usernames)}
    norm = Normalize(0, max(len(usernames) - 1, 1))  # pyright: ignore[reportPossiblyUnboundVariable]
    colors = [cmap(norm(username_to_idx.get(p.username, 0))) for p in processes]
    return colors, usernames, username_to_idx, norm


def _get_colors_by_memory(processes: List[ProcessMemoryInfo], cmap):
    """Create colors based on memory usage."""
    sizes = [p.memory_mb for p in processes]
    norm = Normalize(min(sizes) if len(sizes) > 1 else 0, max(sizes))  # pyright: ignore[reportPossiblyUnboundVariable]
    colors = [cmap(norm(value)) for value in sizes]
    return colors, norm


def _add_details_to_rectangle(ax, rect, process: ProcessMemoryInfo, i: int, min_area_for_details: int):
    """Add detailed info to large enough rectangles."""
    width = getattr(rect, 'get_width', lambda: 0)()
    height = getattr(rect, 'get_height', lambda: 0)()
    area = width * height

    if area <= min_area_for_details:
        return

    rx, ry = getattr(rect, 'get_xy', lambda: (0, 0))()
    
    # Add details with better formatting
    details = [
        f"{process.memory_mb:.1f} MB",
        f"PID: {process.pid}"
    ]

    if process.username:
        details.append(f"User: {process.username}")

    # Calculate text position and add with shadow for better readability
    text_y_positions = [ry + height/2 + (j - len(details)/2) * 12 for j in range(len(details))]

    for j, (text, y_pos) in enumerate(zip(details, text_y_positions)):
        # Shadow text for better readability
        ax.text(
            rx + width/2 + 1,
            y_pos + 1,
            text,
            ha='center',
            va='center',
            fontsize=7,
            color='black',
            alpha=0.7
        )

        ax.text(
            rx + width/2,
            y_pos,
            text,
            ha='center',
            va='center',
            fontsize=7,
            color='white',
            fontweight='bold'
        )


def _create_title(ax, processes: List[ProcessMemoryInfo], system_memory: Dict[str, Any]):
    """Create the title for the treemap with system information."""
    ax.set_title(
        f"RAM Usage Treemap - {len(processes)} Processes\n"
        f"Total: {system_memory['total_gb']:.1f} GB | "
        f"Used: {system_memory['used_gb']:.1f} GB ({system_memory['percent']}%) | "
        f"Available: {system_memory['available_gb']:.1f} GB\n"
        f"Swap: {system_memory['swap_total_gb']:.1f} GB total, "
        f"{system_memory['swap_used_gb']:.1f} GB used ({system_memory['swap_percent']}%)",
        fontsize=18,
        fontweight='bold'
    )


def _add_user_legend(ax, username_to_idx: Dict[str, int], cmap, norm):
    """Add a legend for user-based colors."""
    handles = []
    for username, idx in sorted(username_to_idx.items()):
        color = cmap(norm(idx))
        handles.append(Rectangle((0, 0), 1, 1, color=color, label=username or "unknown"))

    ax.legend(
        handles=handles,
        title="Users",
        loc='lower right',
        fontsize=10,
        title_fontsize=12
    )


def _add_memory_colorbar(fig, ax, cmap, norm):
    """Add a colorbar for memory-based visualization."""
    sm = ScalarMappable(cmap=cmap, norm=norm)  # pyright: ignore[reportPossiblyUnboundVariable]
    sm.set_array(np.array([]))  # Explicit array for type checking
    cbar = fig.colorbar(sm, ax=ax, orientation='vertical', shrink=0.6, pad=0.02)
    cbar.set_label('Memory Usage (MB)', fontsize=14)
    cbar.ax.tick_params(labelsize=12)


def create_treemap(
    processes: List[ProcessMemoryInfo],
    system_memory: Dict[str, Any],
    figsize: Tuple[int, int] = (48, 30),
    min_area_for_details: int = 5000,
    cmap_name: str = 'viridis',
    dpi: int = 100,
    show_user_colors: bool = False,
    top_processes: Optional[int] = None
) -> "Figure":  # Use string literal for forward reference
    """
    Create a treemap visualization of process memory usage.

    Args:
        processes: List of process memory information
        system_memory: System-wide memory information
        figsize: Figure dimensions (width, height) in inches
        min_area_for_details: Minimum rectangle area to show details
        cmap_name: Matplotlib colormap name
        dpi: Dots per inch for rendering
        show_user_colors: Color rectangles by username
        top_processes: Only show top N processes by memory usage

    Returns:
        Matplotlib figure object
    """
    if not processes:
        logger.warning("No processes to visualize")
        fig, _ = _create_empty_figure()
        return fig

    # Limit to top N processes if specified
    if top_processes and len(processes) > top_processes:
        processes = processes[:top_processes]
        logger.info(f"Limited visualization to top {top_processes} processes")

    # Extract data for visualization
    sizes = [p.memory_mb for p in processes]
    labels = [get_truncated_text(p.display_name) for p in processes]

    # Create figure and axes with adjusted margins for better visibility
    fig, ax = plt.subplots(figsize=figsize)  # pyright: ignore[reportPossiblyUnboundVariable]
    plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)  # pyright: ignore[reportPossiblyUnboundVariable]

    # Get colormap
    cmap = _get_colormap(cmap_name)
    
    # Determine colors based on strategy
    username_to_idx = {}
    if show_user_colors:
        colors, usernames, username_to_idx, norm = _get_colors_by_username(processes, cmap)
    else:
        colors, norm = _get_colors_by_memory(processes, cmap)

    # Plot treemap
    try:
        squarify.plot(  # pyright: ignore[reportPossiblyUnboundVariable]
            sizes=sizes,
            label=labels,
            alpha=0.8,
            color=colors,
            ax=ax,
            text_kwargs={'fontsize': 8, 'wrap': True, 'color': 'white'}
        )
    except Exception as e:
        logger.error(f"Error creating treemap: {e}")
        raise

    # Add details to large enough rectangles
    rects = ax.patches
    for i, rect in enumerate(rects):
        if i < len(processes):
            _add_details_to_rectangle(ax, rect, processes[i], i, min_area_for_details)

    # Configure axes
    ax.axis('off')

    # Add title with more detailed information
    _create_title(ax, processes, system_memory)

    # Add legend or colorbar based on visualization strategy
    if show_user_colors and username_to_idx:
        _add_user_legend(ax, username_to_idx, cmap, norm)
    else:
        _add_memory_colorbar(fig, ax, cmap, norm)

    fig.tight_layout()
    return fig


def save_visualization(fig: Figure, output_path: str, dpi: int = 100) -> str:
    """
    Save the visualization to file.

    Args:
        fig: Matplotlib figure
        output_path: Path to save the image
        dpi: Dots per inch for the output image

    Returns:
        Path to the saved file
    """
    try:
        # Ensure the directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        plt.savefig(output_path, dpi=dpi)
        logger.info(f"Treemap saved to {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Error saving visualization: {e}")
        raise


def export_to_csv(processes: List[ProcessMemoryInfo], output_path: str) -> str:
    """
    Export process memory information to CSV file.

    Args:
        processes: List of process memory information
        output_path: Path to save the CSV file

    Returns:
        Path to the saved file
    """
    try:
        # Ensure the directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        with open(output_path, 'w') as f:
            f.write("Process,PID,Memory (MB),Username\n")
            for p in processes:
                f.write(f"{p.name},{p.pid},{p.memory_mb:.2f},{p.username}\n")

        logger.info(f"Process list exported to {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Error exporting to CSV: {e}")
        raise


def export_to_json(processes: List[ProcessMemoryInfo], system_memory: Dict[str, Any], output_path: str) -> str:
    """
    Export process memory and system information to JSON file.

    Args:
        processes: List of process memory information
        system_memory: System memory information
        output_path: Path to save the JSON file

    Returns:
        Path to the saved file
    """
    try:
        # Ensure the directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Prepare the data
        data = {
            "system": system_memory,
            "processes": [p.to_dict() for p in processes],
            "timestamp": import_time_module().strftime("%Y-%m-%d %H:%M:%S")
        }

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Data exported to JSON: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Error exporting to JSON: {e}")
        raise


def import_time_module():
    """Import time module dynamically to avoid issues in restricted environments."""
    import time
    return time


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Visualize system memory usage by process as a treemap."
    )

    parser.add_argument(
        "-o", "--output",
        default=os.path.expanduser("~/ram_usage_treemap.png"),
        help="Output path for the treemap image (default: ~/ram_usage_treemap.png)"
    )

    parser.add_argument(
        "--csv",
        default=os.path.expanduser("~/ram_usage_data.csv"),
        help="Output path for CSV data export (default: ~/ram_usage_data.csv)"
    )

    parser.add_argument(
        "--json",
        default=os.path.expanduser("~/ram_usage_data.json"),
        help="Output path for JSON data export (default: ~/ram_usage_data.json)"
    )

    parser.add_argument(
        "--width",
        type=int,
        default=48,
        help="Width of the output image in inches (default: 48)"
    )

    parser.add_argument(
        "--height",
        type=int,
        default=30,
        help="Height of the output image in inches (default: 30)"
    )

    parser.add_argument(
        "--dpi",
        type=int,
        default=100,
        help="DPI of the output image (default: 100)"
    )

    parser.add_argument(
        "--min-memory",
        type=float,
        default=1.0,
        help="Minimum memory threshold in MB (default: 1.0)"
    )

    parser.add_argument(
        "--colormap",
        default="viridis",
        choices=["viridis", "plasma", "inferno", "magma", "cividis", "cool", "hot", "tab10", "tab20", "Set1", "Set2"],
        help="Colormap for the visualization (default: viridis)"
    )

    parser.add_argument(
        "--no-display",
        action="store_true",
        help="Don't attempt to display the visualization (just save to file)"
    )

    parser.add_argument(
        "--no-csv",
        action="store_true",
        help="Don't export data to CSV"
    )

    parser.add_argument(
        "--no-json",
        action="store_true",
        help="Don't export data to JSON"
    )

    parser.add_argument(
        "--group-by",
        choices=["username", "none"],
        default="none",
        help="Group processes by attribute (default: none)"
    )

    parser.add_argument(
        "--color-by-user",
        action="store_true",
        help="Color rectangles by username instead of memory usage"
    )

    parser.add_argument(
        "--exclude-pids",
        type=str,
        default="",
        help="Comma-separated list of PIDs to exclude"
    )

    parser.add_argument(
        "--exclude-users",
        type=str,
        default="",
        help="Comma-separated list of usernames to exclude"
    )

    parser.add_argument(
        "--top",
        type=int,
        default=None,
        help="Show only top N processes by memory usage"
    )

    parser.add_argument(
        "--headless",
        action="store_true",
        help="Force headless mode (use Agg backend, no GUI dependencies)"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version information and exit"
    )

    return parser.parse_args()


def handle_cli_args() -> Tuple[argparse.Namespace, Set[int], Set[str]]:
    """
    Process command line arguments and prepare filters.

    Returns:
        Tuple of (parsed_args, excluded_pids, excluded_users)
    """
    # Handle version display before any other operations
    if "--version" in sys.argv:
        print("memusg v1.1.0")
        sys.exit(0)

    # Check for headless mode before importing matplotlib
    if "--headless" in sys.argv or os.environ.get("DISPLAY") is None:
        logger.debug("Using Agg backend (headless mode)")
        matplotlib.use("Agg")  # pyright: ignore[reportPossiblyUnboundVariable]

    # Parse command-line arguments
    args = parse_args()

    # Configure logging verbosity
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Parse excluded PIDs
    exclude_pids: Set[int] = set()
    if args.exclude_pids:
        for pid_str in args.exclude_pids.split(","):
            try:
                exclude_pids.add(int(pid_str.strip()))
            except ValueError:
                logger.warning(f"Invalid PID value: {pid_str}")

    # Parse excluded users
    exclude_users: Set[str] = set()
    if args.exclude_users:
        for user in args.exclude_users.split(","):
            user = user.strip()
            if user:
                exclude_users.add(user)

    return args, exclude_pids, exclude_users


def process_data(args: argparse.Namespace,
                exclude_pids: Set[int],
                exclude_users: Set[str]) -> Tuple[List[ProcessMemoryInfo], Dict[str, Any]]:
    """
    Collect and process system data.

    Args:
        args: Parsed command line arguments
        exclude_pids: Set of PIDs to exclude
        exclude_users: Set of usernames to exclude

    Returns:
        Tuple of (process_list, system_memory_info)
    """
    # Collect process information
    logger.info(f"Collecting process memory information (min threshold: {args.min_memory} MB)")
    processes = collect_process_memory_info(
        min_memory_mb=args.min_memory,
        exclude_pids=exclude_pids,
        exclude_users=exclude_users
    )
    logger.info(f"Found {len(processes)} processes using at least {args.min_memory} MB of memory")

    # Group processes if requested
    if args.group_by != "none":
        processes = group_processes_by_attribute(processes, args.group_by)
        logger.info(f"Grouped processes by {args.group_by}, resulting in {len(processes)} groups")

    # Get system memory information
    logger.info("Collecting system memory information")
    system_memory = get_system_memory_info()

    return processes, system_memory


def generate_outputs(args: argparse.Namespace,
                    processes: List[ProcessMemoryInfo],
                    system_memory: Dict[str, Any]) -> int:
    """
    Generate and save visualization and data outputs.

    Args:
        args: Parsed command line arguments
        processes: List of process information
        system_memory: System memory information

    Returns:
        Exit code (0 for success)
    """
    # Create visualization
    logger.info("Creating treemap visualization")
    fig = create_treemap(
        processes=processes,
        system_memory=system_memory,
        figsize=(args.width, args.height),
        cmap_name=args.colormap,
        dpi=args.dpi,
        show_user_colors=args.color_by_user,
        top_processes=args.top
    )

    # Save visualization
    output_path = os.path.expanduser(args.output)
    save_visualization(fig, output_path, dpi=args.dpi)

    # Export to CSV if requested
    if not args.no_csv:
        csv_path = os.path.expanduser(args.csv)
        export_to_csv(processes, csv_path)

    # Export to JSON if requested
    if not args.no_json:
        json_path = os.path.expanduser(args.json)
        export_to_json(processes, system_memory, json_path)

    # Display visualization if requested
    if not args.no_display:
        logger.info("Attempting to display visualization")
        try:
            plt.show()  # pyright: ignore[reportPossiblyUnboundVariable]
        except Exception as e:
            logger.warning(f"Could not display visualization: {e}")

    logger.info("RAM usage visualization completed successfully")
    return 0


def main() -> int:
    """
    Main program entry point.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        # Process command line arguments
        args, exclude_pids, exclude_users = handle_cli_args()

        logger.debug("Starting RAM usage visualization")

        # Collect and process data
        processes, system_memory = process_data(args, exclude_pids, exclude_users)

        # Generate and save outputs
        return generate_outputs(args, processes, system_memory)

    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        return 130
    except NameError as e:
        logger.error(f"Module import error: {e}")
        print("This likely means a required module wasn't properly initialized.")
        return 1
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
