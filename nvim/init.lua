-- Set leader key before anything else
vim.g.mapleader = " "
vim.g.maplocalleader = " "

-- Core settings
require("kyvo.core.options")

-- Plugin manager + plugins
require("kyvo.lazy-bootstrap")

-- Keymaps (after plugins so mappings can reference them)
require("kyvo.core.keymaps")
