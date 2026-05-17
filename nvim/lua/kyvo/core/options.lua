local opt = vim.opt

-- Line numbers
opt.number = true
opt.relativenumber = true

-- Tabs & indentation
opt.tabstop = 2
opt.shiftwidth = 2
opt.expandtab = true
opt.smartindent = true

-- Search
opt.ignorecase = true
opt.smartcase = true

-- Appearance
opt.termguicolors = true
opt.signcolumn = "yes"
opt.cursorline = true
opt.scrolloff = 8

-- Splits
opt.splitright = true
opt.splitbelow = true

-- System clipboard
opt.clipboard = "unnamedplus"

-- Misc
opt.swapfile = false
opt.undofile = true
opt.updatetime = 250
