Update the local Reddit Product Insights data used by Claude Desktop.

1. Run `powershell -ExecutionPolicy Bypass -File .\scripts\update_local_data.ps1` from the repository root.
2. Do not edit or delete existing dumps.
3. Confirm the latest available dump date, Nubra catalog version and local folder from the script output.
4. If GitHub authentication fails, explain the exact authentication step required. Do not ask the user to paste a token into chat.
5. Tell the user that Claude Desktop can now analyse the updated local files. Do not generate the full report unless requested.

