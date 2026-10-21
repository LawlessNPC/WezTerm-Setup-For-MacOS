-- Liquid Glass theme (dark): a translucent, heavily blurred window that lets
-- the desktop show through, Apple system colors, and floating pill tabs, each
-- tab in its own color. Pair with ~/.tmux/themes/glass.conf.
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

-- Each tab keeps one of these for its lifetime (picked by tab id, so closing
-- or moving a tab never recolors the others): its title is drawn in it, and
-- its pill, while active or hovered, is a deep tint of it.
local TAB_COLORS = {
  '#0A84FF', -- blue
  '#FF9F0A', -- orange
  '#30D158', -- green
  '#FF375F', -- pink
  '#BF5AF2', -- purple
  '#FFD60A', -- yellow
  '#64D2FF', -- teal
  '#66D4CF', -- mint
}

-- macOS traffic-light colors, for the window buttons drawn in the tab bar.
local LIGHTS = { close = '#FF5F57', hide = '#FEBC2E', maximize = '#28C840' }

-- Nerd Font half-circle caps that round off each pill.
local CAP_L = utf8.char(0xe0b6)
local CAP_R = utf8.char(0xe0b4)

-- Font Awesome circles (Symbols Nerd Font): a plain dot for each window
-- button, and the dot with its symbol cut out while hovered.
local DOT       = utf8.char(0xf111)
local DOT_CLOSE = utf8.char(0xf057)
local DOT_HIDE  = utf8.char(0xf056)
local DOT_MAX   = utf8.char(0xf055)

local function tab_color(tab)
  return TAB_COLORS[tab.tab_id % #TAB_COLORS + 1]
end

-- hex mixed into the glass base: 0 gives the base, 1 the color itself.
local function tint(hex, amount)
  local out = '#'
  for i = 2, 6, 2 do
    local base = tonumber(P.surface:sub(i, i + 1), 16)
    local c = tonumber(hex:sub(i, i + 1), 16)
    out = out .. string.format('%02X', math.floor(base + (c - base) * amount + 0.5))
  end
  return out
end

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

    -- Claude Code's diff panel: claude/themes/glass.json paints it in palette
    -- color 235 (normally #262626, its Dark theme's own grey), so here that
    -- one grey turns glassy. Colored cells keep their palette alpha.
    indexed = {
      [235] = 'rgba(38, 38, 38, 0.7)',
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
  --   With the native macOS buttons, this tab bar always leaves 10 blank
  --   cells for them (fixed in WezTerm), a wide gap at this font size. Any
  --   non-native button style hides them and has WezTerm draw its own, here
  --   traffic-light dots right before the first tab that show their symbol
  --   on hover. They close, minimize and maximize the window.
  ------------------------------------------------------------------------
  config.window_decorations = 'INTEGRATED_BUTTONS|RESIZE'
  config.integrated_title_button_style = 'Windows'
  config.integrated_title_button_alignment = 'Left'
  config.integrated_title_buttons = { 'Close', 'Hide', 'Maximize' }
  -- A Nerd Font icon followed by a space in the same colors is drawn two
  -- cells wide, so the spaces after a dot are reset to plain attributes:
  -- every dot stays one cell, the same size.
  local function light(color, glyph, after)
    return wezterm.format({
      { Foreground = { Color = color } },
      { Text = ' ' .. glyph },
      'ResetAttributes',
      { Text = after or '' },
    })
  end
  config.tab_bar_style = {
    window_close          = light(LIGHTS.close, DOT),
    window_close_hover    = light(LIGHTS.close, DOT_CLOSE),
    window_hide           = light(LIGHTS.hide, DOT),
    window_hide_hover     = light(LIGHTS.hide, DOT_HIDE),
    -- two spaces after the last dot: the same gap the tabs leave between them
    window_maximize       = light(LIGHTS.maximize, DOT, '  '),
    window_maximize_hover = light(LIGHTS.maximize, DOT_MAX, '  '),
  }
  config.window_padding = { left = 20, right = 20, top = 12, bottom = 10 }
  -- The tab bar sits right under the window's top border, so a clear one
  -- keeps the tabs and dots off the top edge.
  config.window_frame = {
    border_top_height = '0.35cell',
    border_top_color  = 'rgba(0, 0, 0, 0)',
  }

  ------------------------------------------------------------------------
  -- Floating pill tabs
  --   The retro tab bar renders format-tab-title verbatim (the fancy one
  --   draws its own tab chrome), so pills are built here from cap glyphs.
  --   Every tab's title is in its own color; only the active (or hovered)
  --   tab gets a pill, tinted with that color.
  ------------------------------------------------------------------------
  config.use_fancy_tab_bar = false
  config.tab_max_width = 32

  wezterm.on('format-tab-title', function(tab, _tabs, _panes, _cfg, hover, max_width)
    local title = tab.tab_title
    if not title or title == '' then
      title = tab.active_pane.title
    end
    title = wezterm.truncate_right(title, max_width - 4)

    local color = tab_color(tab)
    local clear = { Background = { Color = 'rgba(0, 0, 0, 0)' } }
    if not tab.is_active and not hover then
      return {
        clear,
        { Foreground = { Color = color } },
        { Text = '  ' .. title .. '  ' },
      }
    end

    local pill = tint(color, tab.is_active and 0.55 or 0.3)
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
