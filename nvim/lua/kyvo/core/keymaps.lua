local map = vim.keymap.set

-- Exit insert mode
map("i", "jk", "<Esc>", { desc = "Exit insert mode" })

-- Clear search highlights
map("n", "<leader>nh", "<cmd>nohlsearch<CR>", { desc = "Clear search highlights" })

-- Neo-tree toggle (right side)
map("n", "<leader>e", "<cmd>Neotree toggle<CR>", { desc = "Toggle file explorer" })

-- Split management
map("n", "<leader>sv", "<C-w>v", { desc = "Split vertically" })
map("n", "<leader>sh", "<C-w>s", { desc = "Split horizontally" })
map("n", "<leader>se", "<C-w>=", { desc = "Equal split sizes" })
map("n", "<leader>sx", "<cmd>close<CR>", { desc = "Close split" })

-- Buffer navigation
map("n", "<Tab>", "<cmd>bnext<CR>", { desc = "Next buffer" })
map("n", "<S-Tab>", "<cmd>bprevious<CR>", { desc = "Previous buffer" })
