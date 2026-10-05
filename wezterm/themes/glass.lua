-- Liquid Glass theme (dark): a translucent, heavily blurred window that lets
-- the desktop show through, Apple system colors, and floating pill tabs.
-- Pair with ~/.tmux/themes/glass.conf.
local wezterm = require('wezterm')

local M = {}

-- Apple dark-mode system colors. Shared with tmux/themes/glass.conf -- keep
-- the two files in sync when tuning.
local P = {
  label     = '#F5F5F7', -- primary text
  secondary = '#8E8E93', -- secondary text (systemGray)
  surface   = '#1C1C1E', -- glass base tint
  fill      = '#3A3A3C', -- active pill (systemGray4)
  fill_soft = '#2C2C2E', -- hovered pill (systemGray5)
  blue      = '#0A84FF',
}

-- Nerd Font half-circle caps that round off each pill.
local CAP_L = utf8.char(0xe0b6)
local CAP_R = utf8.char(0xe0b4)

function M.apply(config)
  ------------------------------------------------------------------------
  -- Fonts
  --   SF Mono ships inside Terminal.app on every Mac; loading it from there
  --   avoids the sudo-only font-sf-mono cask. Symbols Nerd Font supplies
  --   the pill caps and icons SF Mono lacks.
  ------------------------------------------------------------------------
  table.insert(config.font_dirs, '/System/Applications/Utilities/Terminal.app/Contents/Resources/Fonts')
  config.font = wezterm.font_with_fallback({
    'SF Mono',
    'Symbols Nerd Font Mono',
  })
  config.font_size = 21
  config.line_height = 1.15

  ------------------------------------------------------------------------
  -- Palette
  ------------------------------------------------------------------------
  config.colors = {
    foreground    = P.label,
    background    = P.surface,
    cursor_bg     = P.blue,
    cursor_border = P.blue,
    cursor_fg     = '#FFFFFF',
    selection_bg  = 'rgba(10, 132, 255, 0.35)',
    selection_fg  = 'none',
    split         = 'rgba(255, 255, 255, 0.12)',
    scrollbar_thumb = 'rgba(255, 255, 255, 0.25)',

    ansi = {
      '#2C2C2E', -- black
      '#FF453A', -- red
      '#30D158', -- green
      '#FFD60A', -- yellow
      '#0A84FF', -- blue
      '#BF5AF2', -- magenta (systemPurple)
      '#64D2FF', -- cyan    (systemTeal)
      '#D1D1D6', -- white
    },
    brights = {
      '#636366', -- bright black
      '#FF6961', -- bright red
      '#4AE06F', -- bright green
      '#FFE04A', -- bright yellow
      '#409CFF', -- bright blue
      '#DA8FFF', -- bright magenta
      '#8EE0FF', -- bright cyan
      '#FFFFFF', -- bright white
    },

    tab_bar = {
      background = 'rgba(0, 0, 0, 0)',
      -- format-tab-title paints the pills; these cover the new-tab button.
      new_tab       = { bg_color = 'rgba(0, 0, 0, 0)', fg_color = P.secondary },
      new_tab_hover = { bg_color = 'rgba(0, 0, 0, 0)', fg_color = P.label },
    },
  }

  ------------------------------------------------------------------------
  -- Glass surface
  --   Layer 1 tints the blurred desktop. Layer 2 is a faint vertical sheen:
  --   lighter along the top edge, slightly darker at the bottom, standing in
  --   for Liquid Glass's specular rim (WezTerm can't refract).
  ------------------------------------------------------------------------
  config.macos_window_background_blur = 50
  config.background = {
    {
      source  = { Color = P.surface },
      width   = '100%',
      height  = '100%',
      opacity = 0.62,
    },
    {
      source = {
        Gradient = {
          orientation = 'Vertical',
          colors = { '#FFFFFF', P.surface, P.surface, '#000000' },
        },
      },
      width   = '100%',
      height  = '100%',
      opacity = 0.08,
    },
  }

  -- Per-window overrides survive config reloads, so a window that was open
  -- under the cyberpunk theme keeps its wallpaper override. Drop it.
  wezterm.on('window-config-reloaded', function(window, _pane)
    local overrides = window:get_config_overrides()
    if overrides and overrides.background then
      overrides.background = nil
      window:set_config_overrides(overrides)
    end
  end)

  ------------------------------------------------------------------------
  -- Window
  ------------------------------------------------------------------------
  config.window_decorations = 'INTEGRATED_BUTTONS|RESIZE'
  config.window_padding = { left = 20, right = 20, top = 12, bottom = 10 }

  ------------------------------------------------------------------------
  -- Floating pill tabs
  --   The retro tab bar renders format-tab-title verbatim (the fancy one
  --   draws its own tab chrome), so pills are built here from cap glyphs.
  --   Only the active tab gets a fill; inactive tabs are plain grey text.
  ------------------------------------------------------------------------
  config.use_fancy_tab_bar = false
  config.tab_max_width = 32

  wezterm.on('format-tab-title', function(tab, _tabs, _panes, _cfg, hover, max_width)
    local title = tab.tab_title
    if not title or title == '' then
      title = tab.active_pane.title
    end
    title = wezterm.truncate_right(title, max_width - 4)

    local clear = { Background = { Color = 'rgba(0, 0, 0, 0)' } }
    if not tab.is_active and not hover then
      return {
        clear,
        { Foreground = { Color = P.secondary } },
        { Text = '  ' .. title .. '  ' },
      }
    end

    local pill = tab.is_active and P.fill or P.fill_soft
    return {
      clear,
      { Foreground = { Color = pill } },
      { Text = CAP_L },
      { Background = { Color = pill } },
      { Foreground = { Color = P.label } },
      { Attribute = { Intensity = tab.is_active and 'Bold' or 'Normal' } },
      { Text = ' ' .. title .. ' ' },
      clear,
      { Foreground = { Color = pill } },
      { Text = CAP_R },
    }
  end)

  -- Focused pane stays crisp; others recede rather than getting a border.
  config.inactive_pane_hsb = {
    saturation = 0.9,
    brightness = 0.75,
  }

  config.default_cursor_style = 'SteadyBar'
end

return M
