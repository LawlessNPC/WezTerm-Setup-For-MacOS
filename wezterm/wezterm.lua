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
-- Theme
--   'glass'     -- Liquid Glass: translucent blurred window, Apple colors
--   'cyberpunk' -- neon palette over rotating wallpapers
--   Each theme sets fonts, colors, background, window chrome and tab style.
--   Also switch the matching source-file line in ~/.tmux.conf.
--------------------------------------------------------------------------
local THEME = 'glass'

config.font_dirs = {
  home .. '/Library/Fonts',
}

require('themes.' .. THEME).apply(config)

--------------------------------------------------------------------------
-- Appearance (shared)
--------------------------------------------------------------------------

-- Tab bar -- always shown; the theme decides how tabs look.
config.hide_tab_bar_if_only_one_tab = false
config.tab_bar_at_bottom = false
config.show_new_tab_button_in_tab_bar = true

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
