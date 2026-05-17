local languages = {
  "lua",
  "javascript",
  "typescript",
  "python",
  "json",
  "html",
  "css",
  "bash",
  "markdown",
  "yaml",
}

return {
  "nvim-treesitter/nvim-treesitter",
  build = ":TSUpdate",
  event = "BufReadPost",
  config = function()
    -- Install parsers for the languages we care about
    require("nvim-treesitter").install(languages)

    -- Enable treesitter highlight and indent on every buffer
    vim.api.nvim_create_autocmd("FileType", {
      callback = function()
        pcall(vim.treesitter.start)
      end,
    })
    vim.bo.indentexpr = "v:lua.require'nvim-treesitter'.indentexpr()"
  end,
}
