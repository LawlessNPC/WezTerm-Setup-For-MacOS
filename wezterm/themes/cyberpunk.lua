-- Cyberpunk-neon theme: neon palette over a rotating pool of darkened
-- wallpapers. Pair with ~/.tmux/themes/cyberpunk.conf.
local wezterm = require('wezterm')

local M = {}

function M.apply(config)
  local home = wezterm.home_dir

  ------------------------------------------------------------------------
  -- Fonts
  ------------------------------------------------------------------------
  config.font = wezterm.font_with_fallback({
    'VictorMono Nerd Font',
    'Symbols Nerd Font Mono',
  })
  config.font_size = 22
  config.line_height = 1.2

  ------------------------------------------------------------------------
  -- Palette
  --   Dark UI, neon cyan / magenta / yellow accents, tuned to read over
  --   the heavily darkened background images.
  ------------------------------------------------------------------------
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

  ------------------------------------------------------------------------
  -- Background image rotation
  --   Pool of wallpapers in assets/. Each tab gets one random wallpaper from
  --   a Fisher-Yates-shuffled queue on first render, and keeps it for the
  --   tab's lifetime. Switching tabs swaps the window's background via
  --   set_config_overrides; old tabs restore their original image on return.
  --   Background tables are prebuilt at startup so switches only swap a
  --   table reference rather than reallocating per call.
  ------------------------------------------------------------------------
  local ASSETS = home .. '/.config/wezterm/assets'
  local wallpapers = {
    ASSETS .. '/spiderverse.jpg',
    ASSETS .. '/carnage.jpg',
    ASSETS .. '/highlander.jpg',
    ASSETS .. '/matrix.jpg',
    ASSETS .. '/mrrobot.png',
    ASSETS .. '/piedpiper.jpg',
    ASSETS .. '/cyberpunk-red.jpg',
    ASSETS .. '/umbrella.jpg',
  }

  math.randomseed(os.time())

  local function shuffled(list)
    local out = {}
    for i, v in ipairs(list) do out[i] = v end
    for i = #out, 2, -1 do
      local j = math.random(i)
      out[i], out[j] = out[j], out[i]
    end
    return out
  end

  local rotation = { queue = {}, last = nil }
  local function next_wallpaper()
    if #rotation.queue == 0 then
      rotation.queue = shuffled(wallpapers)
      if rotation.last and rotation.queue[1] == rotation.last and #rotation.queue > 1 then
        rotation.queue[1], rotation.queue[2] = rotation.queue[2], rotation.queue[1]
      end
    end
    local pick = table.remove(rotation.queue, 1)
    rotation.last = pick
    return pick
  end

  local function build_background(image_path)
    return {
      {
        source = { File = image_path },
        width  = 'Cover',
        height = 'Cover',
        horizontal_align = 'Center',
        hsb = { brightness = 0.3, saturation = 0.65, hue = 1.0 },
      },
      {
        source  = { Color = '#0a0a12' },
        width   = '100%',
        height  = '100%',
        opacity = 0.35,
      },
    }
  end

  local prebuilt = {}
  for _, path in ipairs(wallpapers) do
    prebuilt[path] = build_background(path)
  end

  config.background = prebuilt[next_wallpaper()]

  local tab_bg = {}      -- tab_id -> image path (sticky for tab's lifetime)
  local applied_bg = {}  -- window_id -> image path currently applied

  wezterm.on('update-status', function(window, _pane)
    local tab = window:active_tab()
    if not tab then return end
    local tid = tab:tab_id()
    if not tab_bg[tid] then
      tab_bg[tid] = next_wallpaper()
    end
    local wid = window:window_id()
    local desired = tab_bg[tid]
    if applied_bg[wid] ~= desired then
      applied_bg[wid] = desired
      local overrides = window:get_config_overrides() or {}
      overrides.background = prebuilt[desired]
      window:set_config_overrides(overrides)
    end
  end)

  ------------------------------------------------------------------------
  -- Window
  ------------------------------------------------------------------------
  config.window_decorations = 'RESIZE'
  config.window_background_opacity = 0.95
  config.macos_window_background_blur = 20
  config.window_padding = { left = 14, right = 14, top = 6, bottom = 6 }

  config.use_fancy_tab_bar = true
  config.window_frame = {
    font = wezterm.font({ family = 'VictorMono Nerd Font', weight = 'Bold' }),
    font_size = 13,
    active_titlebar_bg   = '#07070d',
    inactive_titlebar_bg = '#07070d',
  }

  -- Dim inactive panes so the focused pane pops.
  config.inactive_pane_hsb = {
    saturation = 0.8,
    brightness = 0.65,
  }

  config.default_cursor_style = 'BlinkingBar'
end

return M
