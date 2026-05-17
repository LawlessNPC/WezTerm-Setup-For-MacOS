local wezterm = require('wezterm')
local act = wezterm.action
local config = wezterm.config_builder()

local home = wezterm.home_dir

-- Resolve the tmux binary across Homebrew (Apple Silicon / Intel) and the
-- system path, so this config works on any Mac without editing.
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
--   Dark UI, neon cyan / magenta / yellow accents, tuned to read over
--   the heavily darkened red background image.
--------------------------------------------------------------------------
config.colors = {
  foreground    = '#e8f6ff',
  background    = '#0a0a12',
  cursor_bg     = '#fcee0a', -- iconic cyberpunk yellow (reads over red)
  cursor_border = '#fcee0a',
  cursor_fg     = '#0a0a12',
  selection_bg  = '#3a1158',
  selection_fg  = '#f5e6ff',
  split         = '#d62cff', -- neon-magenta pane splits
  scrollbar_thumb = '#d62cff',

  ansi = {
    '#15151f', -- black
    '#ff2e6a', -- red     -> neon pink-red
    '#00ff9c', -- green   -> neon green
    '#fcee0a', -- yellow  -> cyberpunk yellow
    '#00b4ff', -- blue    -> neon blue
    '#d62cff', -- magenta -> neon purple
    '#02d7f2', -- cyan    -> neon cyan
    '#c0c4dd', -- white
  },
  brights = {
    '#3a3a52', -- bright black
    '#ff5c8a', -- bright red
    '#5cffbf', -- bright green
    '#fff45c', -- bright yellow
    '#5cc8ff', -- bright blue
    '#e36cff', -- bright magenta
    '#6ce8ff', -- bright cyan
    '#ffffff', -- bright white
  },

  tab_bar = {
    background = '#07070d',
    active_tab        = { bg_color = '#d62cff', fg_color = '#0a0a12', intensity = 'Bold' },
    inactive_tab      = { bg_color = '#15151f', fg_color = '#6ce8ff' },
    inactive_tab_hover = { bg_color = '#1f1f30', fg_color = '#fcee0a' },
    new_tab           = { bg_color = '#07070d', fg_color = '#02d7f2' },
    new_tab_hover     = { bg_color = '#15151f', fg_color = '#fcee0a' },
    inactive_tab_edge = '#07070d',
  },
}

--------------------------------------------------------------------------
-- Background image  (vday-screenshot treatment: image + dark wash)
--   Layer 1: the red cyberpunk art, darkened + desaturated so it reads
--            as a moody backdrop rather than an eye-searing red wall.
--   Layer 2: a near-black wash on top to keep terminal text legible.
--   Tune `brightness` / `saturation` / wash `opacity` to taste.
--------------------------------------------------------------------------
config.background = {
  {
    source = {
      File = home .. '/.config/wezterm/assets/cyberpunk-red.jpg',
    },
    width  = 'Cover',
    height = 'Cover',
    horizontal_align = 'Right', -- keep the figure visible on wide windows
    hsb = {
      brightness = 0.16,
      saturation = 0.65,
      hue        = 1.0,
    },
  },
  {
    source  = { Color = '#0a0a12' },
    width   = '100%',
    height  = '100%',
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

-- Tab bar -- always shown, styled like the vday screenshot's title strip.
config.use_fancy_tab_bar = true
config.hide_tab_bar_if_only_one_tab = false
config.tab_bar_at_bottom = false
config.show_new_tab_button_in_tab_bar = true
config.window_frame = {
  font = wezterm.font({ family = 'VictorMono Nerd Font', weight = 'Bold' }),
  font_size = 13,
  active_titlebar_bg   = '#07070d',
  inactive_titlebar_bg = '#07070d',
}

-- Dim inactive panes so the focused pane pops (vday look).
config.inactive_pane_hsb = {
  saturation = 0.8,
  brightness = 0.65,
}

config.default_cursor_style = 'BlinkingBar'

config.initial_cols = 120
config.initial_rows = 20

-- Launch every new tab/window straight into its own tmux session, so the
-- tmux status line is always present. Plain `new-session` gives each tab an
-- independent session; swap to { ..., 'new-session', '-A', '-s', 'main' }
-- if you'd rather every tab attach to one shared session instead.
config.default_prog = { tmux, 'new-session' }

config.set_environment_variables = {
  EDITOR = 'micro',
  VISUAL = 'micro',
}

wezterm.on('new-tab-button-click', function(window, pane, button, default_action)
  if button == 'Right' then
    window:perform_action(
      act.PromptInputLine {
        description = 'Enter new name for active tab. Leave blank to reset.',
        action = wezterm.action_callback(function(prompt_window, _, line)
          if line then
            prompt_window:active_tab():set_title(line)
          end
        end),
      },
      pane
    )
    return false
  end

  if default_action then
    window:perform_action(default_action, pane)
    return false
  end
end)

return config
