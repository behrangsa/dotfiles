#!/bin/bash

# Get all sensor readings
CPU_TEMP=$(sensors k10temp-pci-00c3 2>/dev/null | grep Tctl | awk '{print $2}' || echo "N/A")
NVME_TEMP=$(sensors nvme-pci-0100 2>/dev/null | grep Composite | awk '{print $2}' || echo "N/A")
GPU_TEMP=$(sensors amdgpu-pci-0400 2>/dev/null | grep edge | awk '{print $2}' || echo "N/A")
ACPI_TEMP=$(sensors acpitz-acpi-0 2>/dev/null | grep temp1 | awk '{print $2}' || echo "N/A")
GPU_PWR=$(sensors amdgpu-pci-0400 2>/dev/null | grep PPT | awk '{print $2, $3}' || echo "N/A")
BAT=$(sensors BAT1-acpi-0 2>/dev/null | grep in0 | awk '{print $2, $3}' || echo "N/A")

# Define column width for consistent spacing
COL_WIDTH=250

# Check which set to display based on argument
case "$1" in
  1)
    echo "CPU: $CPU_TEMP / \${cpu}% / \${freq_g}GHz\${goto $COL_WIDTH}NVMe: $NVME_TEMP\${alignr}GPU: $GPU_TEMP"
    ;;
  2)
    echo "ACPI: $ACPI_TEMP\${goto $COL_WIDTH}GPU Pwr: $GPU_PWR\${alignr}BAT: $BAT"
    ;;
  *)
    echo "Usage: $0 [1-2]"
    ;;
esac
