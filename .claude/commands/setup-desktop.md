Set up Reddit Product Insights for Claude Desktop on this computer.

1. Detect the operating system.
2. On macOS or Linux, run `./install.sh` from the repository root. On Windows, run `powershell -ExecutionPolicy Bypass -File .\scripts\install_claude_desktop.ps1`.
3. Let the installer create its environment, perform the initial verified data sync, merge the Claude Desktop configuration and install the daily updater.
4. If the data repository cannot be read, check whether it is private. Public repositories need no GitHub account. For a private repository, use an approved GitHub account or a securely issued read-only credential. Never request that a token be pasted into Claude chat and never write credentials into this repository or Claude's configuration.
5. Report the Claude configuration path, local data path, latest dump date and scheduler status.
6. Tell the user to completely quit and reopen Claude Desktop. Do not generate product insights during setup.
