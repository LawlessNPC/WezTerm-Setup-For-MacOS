local wezterm = require('wezterm')
local config = wezterm.config_builder()

local home = wezterm.home_dir

local function first_existing(paths)
  for _, path in ipairs(paths) do
    if wezterm.glob(path)[1] then
      return path
    end
  end
  return nil
end

local tmux = first_existing({
  '/opt/homebrew/bin/tmux',
  '/usr/local/bin/tmux',
  '/usr/bin/tmux',
}) or 'tmux'

--------------------------------------------------------------------------
-- Fonts
--------------------------------------------------------------------------
config.font = wezterm.font_with_fallback({
  'VictorMono Nerd Font',
  'Symbols Nerd Font Mono',
})
config.font_size = 22
config.line_height = 1.2

--------------------------------------------------------------------------
-- Cyberpunk-neon palette
--------------------------------------------------------------------------
config.colors = {
  foreground    = '#e8f6ff',
  background    = '#0a0a12',
  cursor_bg     = '#fcee0a',
  cursor_border = '#fcee0a',
  cursor_fg     = '#0a0a12',
  selection_bg  = '#3a1158',
  selection_fg  = '#f5e6ff',
  split         = '#d62cff',
  scrollbar_thumb = '#d62cff',

  ansi = {
    '#15151f',
    '#ff2e6a',
    '#00ff9c',
    '#fcee0a',
    '#00b4ff',
    '#d62cff',
    '#02d7f2',
    '#c0c4dd',
  },
  brights = {
    '#3a3a52',
    '#ff5c8a',
    '#5cffbf',
    '#fff45c',
    '#5cc8ff',
    '#e36cff',
    '#6ce8ff',
    '#ffffff',
  },

  tab_bar = {
    background = '#07070d',
    active_tab         = { bg_color = '#d62cff', fg_color = '#0a0a12', intensity = 'Bold' },
    inactive_tab       = { bg_color = '#15151f', fg_color = '#6ce8ff' },
    inactive_tab_hover = { bg_color = '#1f1f30', fg_color = '#fcee0a' },
    new_tab            = { bg_color = '#07070d', fg_color = '#02d7f2' },
    new_tab_hover      = { bg_color = '#15151f', fg_color = '#fcee0a' },
    inactive_tab_edge  = '#07070d',
  },
}

--------------------------------------------------------------------------
-- Background image
--------------------------------------------------------------------------
config.background = {
  {
    source = {
      File = home .. '/.config/wezterm/assets/cyberpunk-red.jpg',
    },
    width = 'Cover',
    height = 'Cover',
    horizontal_align = 'Right',
    hsb = {
      brightness = 0.16,
      saturation = 0.65,
      hue = 1.0,
    },
  },
  {
    source = { Color = '#0a0a12' },
    width = '100%',
    height = '100%',
    opacity = 0.55,
  },
}

--------------------------------------------------------------------------
-- Appearance
--------------------------------------------------------------------------
config.window_decorations = 'RESIZE'
config.window_background_opacity = 0.95
config.macos_window_background_blur = 20
config.window_padding = { left = 14, right = 14, top = 6, bottom = 6 }

config.use_fancy_tab_bar = true
config.hide_tab_bar_if_only_one_tab = false
config.tab_bar_at_bottom = false
config.show_new_tab_button_in_tab_bar = false
config.window_frame = {
  font = wezterm.font({ family = 'VictorMono Nerd Font', weight = 'Bold' }),
  font_size = 13,
  active_titlebar_bg = '#07070d',
  inactive_titlebar_bg = '#07070d',
}

config.inactive_pane_hsb = {
  saturation = 0.8,
  brightness = 0.65,
}

config.default_cursor_style = 'BlinkingBar'

config.initial_cols = 120
config.initial_rows = 20

config.default_prog = { tmux, 'new-session' }

config.set_environment_variables = {
  EDITOR = 'micro',
  VISUAL = 'micro',
}

return config
