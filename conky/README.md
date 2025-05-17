# Conky Configuration

A customized system monitoring setup for Linux desktops using Conky. This module provides a sleek, information-rich dashboard displaying system metrics, hardware temperatures, disk usage, and network statistics.

## Features

- **Hardware Monitoring**: Real-time display of CPU, GPU, NVMe, and ACPI temperatures
- **System Resource Tracking**: Monitor CPU usage, memory consumption, and top processes
- **Disk Information**: View disk usage statistics and I/O activity
- **Network Visualization**: Display detailed network traffic statistics with graphs
- **Clean Dark Theme**: Modern aesthetic with custom color scheme
- **Modular Design**: Separate utility scripts for gathering system information

## Installation

The module is installed automatically when running the main dotfiles install script:

```bash
./install.sh
```

You can also install it standalone:

```bash
cd ~/dotfiles/conky
./install.sh
```

### Dependencies

The configuration requires:

- Conky (system monitoring software)
- `sensors` command (from lm-sensors package)
- vnStat and vnStati (for network statistics)
- ImageMagick (for image processing)
- JetBrainsMono Nerd Font or Maple Mono NF (for best display)

## Usage

Once installed, Conky will start automatically with your desktop environment. If not, you can start it manually:

```bash
conky -c ~/.conkyrc
```

To restart after making changes:

```bash
pkill conky && conky -c ~/.conkyrc
```

## Configuration

The main configuration file is `.conkyrc`. It defines:

- **Layout and appearance**: Window position, size, colors, and fonts
- **Update intervals**: How frequently information is refreshed
- **Display elements**: Which system metrics are shown and their formats

### Utility Scripts

The configuration uses several helper scripts:

- `sensors.sh`: Collects and formats hardware temperature data
- `vnstati.sh`: Generates network traffic visualizations
- `vimtips.sh`: Displays Vim tips (if configured)

## Example Display

![Conky Dashboard](dotfiles/conky/conky.gif)

## Customization

You can customize the configuration by editing the `.conkyrc` file:

```bash
vim ~/.conkyrc
```

### Main Display Sections

- **Sensory Information**: Hardware temperatures and power usage
- **Process Monitor**: Shows top processes by CPU and memory usage
- **Disk Usage**: Visual display of disk space and I/O activity
- **Network Statistics**: Detailed network traffic graphs for hourly, daily, and monthly usage

## Troubleshooting

If the display appears incorrect:

- Ensure all dependencies are installed
- Check that the font specified in the configuration is available
- Verify that sensor commands return valid data for your hardware
- Check permissions on the utility scripts (they should be executable)

For font-related issues, modify the font specification in `.conkyrc`:

```
font = 'Maple Mono NF:size=10',
```

Replace with any system font you have installed.
