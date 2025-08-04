<div align="center">

  <h1>🪟 Windows-MCP</h1>

  <a href="https://github.com/CursorTouch/Windows-MCP/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  </a>
  <img src="https://img.shields.io/badge/python-3.13%2B-blue" alt="Python">
  <img src="https://img.shields.io/badge/platform-Windows%207–11-blue" alt="Platform: Windows 7 to 11">
  <img src="https://img.shields.io/github/last-commit/CursorTouch/Windows-MCP" alt="Last Commit">
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

## Windows Scheduler GUI

本專案還包含一個基於 Windows-MCP 的圖形化排程管理工具 - **Windows Scheduler GUI**，提供使用者友善的介面來管理和自動化 Windows 應用程式的操作。

### GUI 主要功能

- **直觀的圖形介面**：包含功能表列、工具列和主要工作區域
- **應用程式管理**：掃描並管理系統中的 Windows 應用程式
- **排程任務建立**：建立和編輯自動化任務，支援多種執行時間設定
- **任務監控**：監控任務執行狀態和查看執行歷史
- **安全性控制**：安全的操作確認和權限管理

### GUI 技術規格

- **Python版本**: 3.13+
- **GUI框架**: Tkinter
- **整合模組**: Windows-MCP
- **支援系統**: Windows 7-11

### 啟動 GUI

```bash
# 直接啟動 GUI
python src/gui/scheduler_app.py

# 或從主程式啟動
python main.py --gui
```

更多 GUI 開發資訊請參考 [開發文檔.md](開發文檔.md)。

## Updates

- Try out 🪟[Windows-Use](https://github.com/CursorTouch/Windows-Use)!!, an agent built using Windows-MCP.
- Windows-MCP is now featured as Desktop Extension in `Claude Desktop`.

### Supported Operating Systems

- Windows 7
- Windows 8, 8.1
- Windows 10
- Windows 11  

## 🎥 Demos

<https://github.com/user-attachments/assets/d0e7ed1d-6189-4de6-838a-5ef8e1cad54e>

<https://github.com/user-attachments/assets/d2b372dc-8d00-4d71-9677-4c64f5987485>

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
  Typical latency between actions (e.g., from one mouse click to the next) ranges from **1.5 to 2.3 secs**, and may slightly vary based on the number of active applications and system load, also the inferencing speed of the llm.

### Prerequisites

- Python 3.13+
- Anthropic Claude Desktop app or other MCP Clients
- UV (Package Manager) from Astra, install with `pip install uv`
- DXT (Desktop Extension) from Antropic, install with `npm install -g @anthropic-ai/dxt`
- Set `English` as the default language in Windows

## 🏁 Getting Started

### Gemini CLI

1. Navigate to `%USERPROFILE%/.gemini` in File Explorer and open `settings.json`.

2. Add the `windows-mcp` config in the `settings.json` and save it.

```json
{
  "theme": "Default",
  ...
//MCP Server Config
  "mcpServers": {
    "windows-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "<path to the windows-mcp directory>",
        "run",
        "main.py"
      ]
    }
  }
}
```

3. Rerun Gemini CLI in terminal. Enjoy 🥳

### Claude Desktop

1. Clone the repository.

```shell
git clone https://github.com/CursorTouch/Windows-MCP.git
cd Windows-MCP
```

2. Build Desktop Extension `DXT`:

```shell
npx @anthropic-ai/dxt pack
```

3. Open Claude Desktop:

Go to Claude Desktop: Settings->Extensions->Install Extension (locate the `.dxt` file)-> Install

Finally Enjoy 🥳.

For additional Claude Desktop integration troubleshooting, see the [MCP documentation](https://modelcontextprotocol.io/quickstart/server#claude-for-desktop-integration-issues). The documentation includes helpful tips for checking logs and resolving common issues.

---

## 🛠️MCP Tools

Claude can access the following tools to interact with Windows:

- `Click-Tool`: Click on the screen at the given coordinates.
- `Type-Tool`: Type text on an element (optionally clears existing text).
- `Clipboard-Tool`: Copy or paste using the system clipboard.
- `Scroll-Tool`: Scroll vertically or horizontally on the window or specific regions.
- `Drag-Tool`: Drag from one point to another.
- `Move-Tool`: Move mouse pointer.
- `Shortcut-Tool`: Press keyboard shortcuts (`Ctrl+c`, `Alt+Tab`, etc).
- `Key-Tool`: Press a single key.
- `Wait-Tool`: Pause for a defined duration.
- `State-Tool`: Combined snapshot of default language, browser, active apps and interactive, textual and scrollable elements along with screenshot of the desktop.
- `Resize-Tool`: Used to change the window size or location of an app.
- `Launch-Tool`: To launch an application from the start menu.
- `Shell-Tool`: To execute PowerShell commands.
- `Scrape-Tool`: To scrape the entire webpage for information.

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=CursorTouch/Windows-MCP&type=Date)](https://www.star-history.com/#CursorTouch/Windows-MCP&Date)

## ⚠️Caution

This MCP interacts directly with your Windows operating system to perform actions. Use with caution and avoid deploying it in environments where such risks cannot be tolerated.

## 📝 Limitations

- Selecting specific sections of the text in a paragraph, as the MCP is relying on a11y tree. (⌛ Working on it.)
- `Type-Tool` is meant for typing text, not programming in IDE because of it types program as a whole in a file. (⌛ Working on it.)

## 🪪License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝Contributing

Contributions are welcome! Please see [CONTRIBUTING](CONTRIBUTING) for setup instructions and development guidelines.

Made with ❤️ by [Jeomon George](https://github.com/Jeomon)

## Citation

```bibtex
@software{
  author       = {George, Jeomon},
  title        = {Windows-MCP: Lightweight open-source project for integrating LLM agents with Windows},
  year         = {2024},
  publisher    = {GitHub},
  url={https://github.com/CursorTouch/Windows-MCP}
}
```
