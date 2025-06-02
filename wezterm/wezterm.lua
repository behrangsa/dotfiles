local wezterm = require 'wezterm'
local config = wezterm.config_builder()

-- Font configuration
config.font = wezterm.font_with_fallback {
    'Maple Mono NF',
    'Noto Color Emoji',
    'Symbols Nerd Font Mono',
}

config.font_size = 14.0
config.line_height = 1.1

-- Appearance
-- Function to get system appearance
local function get_appearance()
    if wezterm.gui then
        return wezterm.gui.get_appearance()
    end
    return 'Dark' -- fallback
end

-- Function to choose color scheme based on appearance
local function scheme_for_appearance(appearance)
    if appearance:find 'Dark' then
        return 'Belafonte Night' -- Dark theme
    else
        return 'Belafonte Day'   -- Light theme
    end
end

-- Set color scheme based on system appearance
config.color_scheme = scheme_for_appearance(get_appearance())
config.window_background_opacity = 0.9

-- Set window decorations
config.window_decorations = 'RESIZE'

-- Window settings optimized for 34" ultrawide (3440x1440)
config.initial_cols = 200
config.initial_rows = 50
config.adjust_window_size_when_changing_font_size = false

-- Tab bar
config.enable_tab_bar = true
config.use_fancy_tab_bar = true
config.tab_bar_at_bottom = false
config.show_tab_index_in_tab_bar = true
config.hide_tab_bar_if_only_one_tab = false

-- Performance optimizations for Vega 6
config.webgpu_power_preference = 'LowPower'
config.front_end = 'WebGpu'
config.max_fps = 60

-- Wayland-specific settings
config.enable_wayland = true

-- Scrollback
config.scrollback_lines = 42069

-- Key bindings that match Kitty's behavior
config.keys = {
    -- Clipboard operations (what you requested)
    { key = 'c',          mods = 'CTRL|SHIFT',     action = wezterm.action.CopyTo 'Clipboard' },
    { key = 'v',          mods = 'CTRL|SHIFT',     action = wezterm.action.PasteFrom 'Clipboard' },

    -- Kitty-like window management
    -- Ctrl+Shift+Enter creates new window (matches Kitty exactly)
    { key = 'Enter',      mods = 'CTRL|SHIFT',     action = wezterm.action.SplitHorizontal { domain = 'CurrentPaneDomain' } },

    -- Ctrl+Shift+L switches layouts (matches Kitty exactly)
    { key = 'l',          mods = 'CTRL|SHIFT',     action = wezterm.action.RotatePanes 'Clockwise' },

    -- Window navigation (standard across terminals)
    { key = 'LeftArrow',  mods = 'CTRL|SHIFT',     action = wezterm.action.ActivatePaneDirection 'Left' },
    { key = 'RightArrow', mods = 'CTRL|SHIFT',     action = wezterm.action.ActivatePaneDirection 'Right' },
    { key = 'UpArrow',    mods = 'CTRL|SHIFT',     action = wezterm.action.ActivatePaneDirection 'Up' },
    { key = 'DownArrow',  mods = 'CTRL|SHIFT',     action = wezterm.action.ActivatePaneDirection 'Down' },

    -- Tab management (matches Kitty)
    { key = 't',          mods = 'CTRL|SHIFT',     action = wezterm.action.SpawnTab 'CurrentPaneDomain' },
    { key = 'w',          mods = 'CTRL|SHIFT',     action = wezterm.action.CloseCurrentTab { confirm = true } },

    -- Window resizing (like Kitty)
    { key = 'LeftArrow',  mods = 'CTRL|SHIFT|ALT', action = wezterm.action.AdjustPaneSize { 'Left', 5 } },
    { key = 'RightArrow', mods = 'CTRL|SHIFT|ALT', action = wezterm.action.AdjustPaneSize { 'Right', 5 } },
    { key = 'UpArrow',    mods = 'CTRL|SHIFT|ALT', action = wezterm.action.AdjustPaneSize { 'Up', 5 } },
    { key = 'DownArrow',  mods = 'CTRL|SHIFT|ALT', action = wezterm.action.AdjustPaneSize { 'Down', 5 } },

    -- Close current pane
    { key = 'w',          mods = 'CTRL|SHIFT|ALT', action = wezterm.action.CloseCurrentPane { confirm = true } },
}

-- Mouse bindings for convenience
config.mouse_bindings = {
    -- Right click to paste
    {
        event = { Up = { streak = 1, button = 'Right' } },
        mods = 'NONE',
        action = wezterm.action.PasteFrom 'Clipboard',
    },
    -- Middle click for primary selection (Linux)
    {
        event = { Up = { streak = 1, button = 'Middle' } },
        mods = 'NONE',
        action = wezterm.action.PasteFrom 'PrimarySelection',
    },
}


-- Environment variables
config.set_environment_variables = {
    TERM = 'wezterm',
    COLORTERM = 'truecolor',
}

return config
