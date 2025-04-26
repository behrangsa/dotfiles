#!/usr/bin/env python
"""
RAM Usage Visualization Tool

Generates a treemap visualization of system memory usage by process.
This script collects memory information for all running processes
and renders it as a treemap where rectangle size represents memory consumption.
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

# Check for required dependencies
missing_deps = []
try:
    import psutil
except ImportError:
    missing_deps.append("psutil")

try:
    import matplotlib.pyplot as plt
except ImportError:
    missing_deps.append("matplotlib")

try:
    import squarify
except ImportError:
    missing_deps.append("squarify")

try:
    import numpy as np
except ImportError:
    missing_deps.append("numpy")

# Exit if any dependencies are missing
if missing_deps:
    print("Error: The following required packages are missing:")
    for dep in missing_deps:
        print(f"  - {dep}")
    print("\nPlease install them with:")
    print(f"pip install {' '.join(missing_deps)}")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ram_usage_treemap")


class ProcessMemoryInfo:
    """Represents memory information for a single process."""
    
    def __init__(self, pid: int, name: str, memory_mb: float):
        """
        Initialize process memory information.
        
        Args:
            pid: Process ID
            name: Process name
            memory_mb: Memory usage in megabytes
        """
        self.pid = pid
        self.name = name
        self.memory_mb = memory_mb
    
    def __repr__(self) -> str:
        return f"ProcessMemoryInfo(pid={self.pid}, name='{self.name}', memory_mb={self.memory_mb:.1f})"


def collect_process_memory_info(min_memory_mb: float = 1.0) -> List[ProcessMemoryInfo]:
    """
    Collect memory usage information for all running processes.
    
    Args:
        min_memory_mb: Minimum memory usage threshold in MB
        
    Returns:
        List of ProcessMemoryInfo objects sorted by memory usage (descending)
    """
    processes = []
    
    try:
        for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
            try:
                process_info = proc.info
                mem_usage_mb = process_info['memory_info'].rss / (1024 * 1024)
                
                if mem_usage_mb >= min_memory_mb:
                    processes.append(ProcessMemoryInfo(
                        pid=process_info['pid'],
                        name=process_info['name'],
                        memory_mb=mem_usage_mb
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
        mem = psutil.virtual_memory()
        return {
            'total_gb': mem.total / (1024**3),
            'used_gb': mem.used / (1024**3),
            'percent': mem.percent
        }
    except Exception as e:
        logger.error(f"Error getting system memory information: {e}")
        raise


def create_treemap(
    processes: List[ProcessMemoryInfo], 
    system_memory: Dict[str, Any],
    figsize: Tuple[int, int] = (48, 30),
    min_area_for_details: int = 5000,
    cmap_name: str = 'viridis',
    dpi: int = 100
) -> plt.Figure:
    """
    Create a treemap visualization of process memory usage.
    
    Args:
        processes: List of process memory information
        system_memory: System-wide memory information
        figsize: Figure dimensions (width, height) in inches
        min_area_for_details: Minimum rectangle area to show details
        cmap_name: Matplotlib colormap name
        dpi: Dots per inch for rendering
        
    Returns:
        Matplotlib figure object
    """
    if not processes:
        logger.warning("No processes to visualize")
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, "No processes found meeting the minimum memory threshold",
                ha='center', va='center', fontsize=14)
        ax.axis('off')
        return fig
    
    # Extract data for visualization
    sizes = [p.memory_mb for p in processes]
    labels = [p.name for p in processes]
    
    # Create figure and axes
    fig, ax = plt.subplots(figsize=figsize)
    
    # Create color mapping
    try:
        # Use the newer recommended API (for Matplotlib 3.7+)
        if hasattr(plt, 'colormaps'):
            cmap = plt.colormaps[cmap_name]
        # Fallback for older Matplotlib versions
        else:
            cmap = plt.get_cmap(cmap_name)
    except Exception as e:
        logger.warning(f"Error using preferred colormap API, falling back to older method: {e}")
        cmap = plt.cm.get_cmap(cmap_name)
    
    norm = plt.Normalize(min(sizes), max(sizes))
    colors = [cmap(norm(value)) for value in sizes]
    
    # Plot treemap
    try:
        squarify.plot(
            sizes=sizes,
            label=labels,
            alpha=0.8,
            color=colors,
            ax=ax,
            text_kwargs={'fontsize': 8, 'wrap': True}
        )
    except Exception as e:
        logger.error(f"Error creating treemap: {e}")
        raise
    
    # Add details to large enough rectangles
    rects = ax.patches
    for i, rect in enumerate(rects):
        width = rect.get_width()
        height = rect.get_height()
        area = width * height
        
        if area > min_area_for_details and i < len(processes):
            rx, ry = rect.get_xy()
            process = processes[i]
            ax.text(
                rx + width/2,
                ry + height/2 + 10,
                f"PID: {process.pid}\n{process.memory_mb:.1f} MB",
                ha='center',
                va='center',
                fontsize=7,
                color='white'
            )
    
    # Configure axes
    ax.axis('off')
    
    # Add title
    ax.set_title(
        f"RAM Usage Treemap - All Processes\n"
        f"Total: {system_memory['total_gb']:.1f} GB, "
        f"Used: {system_memory['used_gb']:.1f} GB ({system_memory['percent']}%)",
        fontsize=18,
        fontweight='bold'
    )
    
    # Add colorbar
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, orientation='vertical', shrink=0.6, pad=0.02)
    cbar.set_label('Memory Usage (MB)', fontsize=14)
    cbar.ax.tick_params(labelsize=12)
    
    fig.tight_layout()
    return fig


def save_visualization(fig: plt.Figure, output_path: str, dpi: int = 100) -> str:
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
            f.write("Process,PID,Memory (MB)\n")
            for p in processes:
                f.write(f"{p.name},{p.pid},{p.memory_mb:.2f}\n")
                
        logger.info(f"Process list exported to {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Error exporting to CSV: {e}")
        raise


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
        choices=["viridis", "plasma", "inferno", "magma", "cividis", "cool", "hot"],
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
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


def main() -> int:
    """
    Main program entry point.
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        # Parse command-line arguments
        args = parse_args()
        
        # Configure logging verbosity
        if args.verbose:
            logger.setLevel(logging.DEBUG)
        
        logger.debug("Starting RAM usage visualization")
        
        # Collect process information
        logger.info(f"Collecting process memory information (min threshold: {args.min_memory} MB)")
        processes = collect_process_memory_info(min_memory_mb=args.min_memory)
        logger.info(f"Found {len(processes)} processes using at least {args.min_memory} MB of memory")
        
        # Get system memory information
        logger.info("Collecting system memory information")
        system_memory = get_system_memory_info()
        
        # Create visualization
        logger.info("Creating treemap visualization")
        fig = create_treemap(
            processes=processes,
            system_memory=system_memory,
            figsize=(args.width, args.height),
            cmap_name=args.colormap,
            dpi=args.dpi
        )
        
        # Save visualization
        output_path = os.path.expanduser(args.output)
        save_visualization(fig, output_path, dpi=args.dpi)
        
        # Export to CSV if requested
        if not args.no_csv:
            csv_path = os.path.expanduser(args.csv)
            export_to_csv(processes, csv_path)
            
        # Display visualization if requested
        if not args.no_display:
            logger.info("Attempting to display visualization")
            try:
                plt.show()
            except Exception as e:
                logger.warning(f"Could not display visualization: {e}")
        
        logger.info("RAM usage visualization completed successfully")
        return 0
        
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

