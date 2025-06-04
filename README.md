<div align="center">

  <h1>🪟 Windows-MCP</h1>

  <a href="https://github.com/Computer-Agent/Windows-MCP/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  </a>
  <img src="https://img.shields.io/badge/python-3.12%2B-blue" alt="Python">
  <img src="https://img.shields.io/badge/platform-Windows%2010%20%7C%2011-blue" alt="Platform">
  <img src="https://img.shields.io/github/last-commit/Computer-Agent/Windows-MCP" alt="Last Commit">
  <br>
  <a href="https://x.com/CursorTouch">
    <img src="https://img.shields.io/badge/follow-%40CursorTouch-1DA1F2?logo=twitter&style=flat" alt="Follow on Twitter">
  </a>
  <a href="https://discord.com/invite/Aue9Yj2VzS">
    <img src="https://img.shields.io/badge/Join%20on-Discord-5865F2?logo=discord&logoColor=white&style=flat" alt="Join us on Discord">
  </a>

</div>

<br>

**Windows MCP** is a lightweight, open-source project that enables seamless integration between AI agents and the Windows operating system. Acting as an MCP server bridges the gap between LLMs and the Windows operating system, allowing agents to perform tasks such as **file navigation, application control, UI interaction, QA testing,** and more.

<https://github.com/user-attachments/assets/d0e7ed1d-6189-4de6-838a-5ef8e1cad54e>

## ✨ Key Features

- **Seamless Windows Integration**  
  Interacts natively with Windows UI elements, opens apps, controls windows, simulates user input, and more.

- **Use Any LLM (Vision Optional)**
   Unlike many automation tools, Windows MCP doesn't rely on any traditional computer vision techniques or specific fine-tuned models; it works with any LLMs, reducing complexity and setup time.

- **Rich Toolset for UI Automation**  
  Includes tools for basic keyboard, mouse operation and capturing window/UI state.

- **Lightweight & Open-Source**  
  Minimal dependencies and easy setup with full source code available under MIT license.

- **Customizable & Extendable**  
  Easily adapt or extend tools to suit your unique automation or AI integration needs.

- **Real-Time Interaction**  
  Typical latency between actions (e.g., from one mouse click to the next) ranges from **4 to 8 secs**, and may slightly vary based on the number of active applications and system load.

### Supported Operating Systems

- Windows 10
- Windows 11  

## Installation

### Prerequisites

- Python 3.12+
- Anthropic Claude Desktop app or other MCP Clients
- UV (Python package manager), install with `pip install uv`

## 🏁 Getting Started

1. Clone the repository.

```shell
git clone https://github.com/CursorTouch/Windows-MCP.git
cd Windows-MCP
```

2. Install dependencies:

```shell
uv pip install -r pyproject.toml
```

3. Connect to the MCP server

Copy the below JSON with the appropriate {{PATH}} values:

```json
{
   "mcpServers": {
      "windows-mcp": {
         "command": "{{PATH_TO_UV}}",
         "args": [
            "--directory",
            "{{PATH_TO_SRC}}/Windows-MCP",
            "run",
            "server.py"
         ]
      }
   }
}
```

For Claude, save this as claude_desktop_config.json in your Claude Desktop configuration directory at:

```shell
%APPDATA%/Claude/claude_desktop_config.json
```

4. Restart Claude Desktop

Open Claude Desktop, and you should now see Windows-MCP as an available integration.

For additional Claude Desktop integration troubleshooting, see the [MCP documentation](https://modelcontextprotocol.io/quickstart/server#claude-for-desktop-integration-issues). The documentation includes helpful tips for checking logs and resolving common issues.

---

## 🛠️MCP Tools

Claude can access the following tools to interact with Windows:

- `Click-Tool`: Click on the screen at the given coordinates.
- `Type-Tool`: Type text on an element (optionally clears existing text).
- `Clipboard-Tool`: Copy or paste using the system clipboard.
- `Scroll-Tool`: Scroll up/down.
- `Drag-Tool`: Drag from one point to another.
- `Move-Tool`: Move mouse pointer.
- `Shortcut-Tool`: Press keyboard shortcuts (`Ctrl+c`, `Alt+Tab`, etc).
- `Key-Tool`: Press a single key.
- `Wait-Tool`: Pause for a defined duration.
- `State-Tool`: Combined snapshot of active apps and interactive UI elements.
- `Screenshot-Tool`: Capture a screenshot of the desktop.
- `Launch-Tool`: To launch an application from the start menu.
- `Shell-Tool`: To execute PowerShell commands.
- `Scrape-Tool`: To scrape the entire webpage for information.

## ⚠️Caution

This MCP interacts directly with your Windows operating system to perform actions. Use with caution and avoid deploying it in environments where such risks cannot be tolerated.

## 🪪License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝Contributing

Contributions are welcome! Please see [CONTRIBUTING](CONTRIBUTING) for setup instructions and development guidelines.

Made with ❤️ by [Jeomon George](https://github.com/Jeomon)

## Citation

```bibtex
@misc{
  author       = {George, Jeomon},
  title        = {Windows-MCP},
  year         = {2024},
  publisher    = {GitHub},
  howpublished = {\url{https://github.com/Jeomon/Windows-MCP}},
  note         = {Lightweight open-source project for integrating LLM agents with Windows}
}
```
