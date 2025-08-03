# Windows Scheduler GUI

Windows應用程式排程控制GUI - 基於Windows-MCP的圖形化排程管理工具

## 專案概述

這是一個基於Python Tkinter開發的Windows應用程式排程控制系統，整合了Windows-MCP的功能，提供使用者友善的圖形介面來管理和自動化Windows應用程式的操作。

## 主要功能

- **GUI主介面設計**: 直觀的圖形介面，包含功能表列、工具列和主要工作區域
- **應用程式偵測與管理**: 掃描並管理系統中的Windows應用程式
- **排程任務建立與編輯**: 建立和編輯自動化任務，支援多種執行時間設定
- **排程執行引擎**: 自動執行排程任務，整合Windows-MCP功能
- **任務監控與日誌**: 監控任務執行狀態和查看執行歷史
- **系統設定與配置**: 自訂應用程式行為和系統設定
- **安全性與權限管理**: 安全的操作確認和權限控制
- **使用者體驗優化**: 簡單直觀的操作介面和引導教學
- **說明與支援系統**: 完整的使用說明和FAQ支援

## 技術規格

- **Python版本**: 3.13+
- **包管理器**: uv
- **GUI框架**: Tkinter
- **整合模組**: Windows-MCP
- **支援系統**: Windows 7-11

## 安裝與設定

### 1. 環境準備

確保已安裝Python 3.13+和uv包管理器。

### 2. 專案設定

```bash
# 建立虛擬環境
uv venv

# 激活虛擬環境 (Windows)
.venv\Scripts\activate

# 安裝依賴
uv sync

# 安裝開發依賴
uv add --dev pytest black flake8 mypy
```

### 3. 開發工具配置

```bash
# 代碼格式化
uv run black src/

# 代碼檢查
uv run flake8 src/

# 類型檢查
uv run mypy src/

# 運行測試
uv run pytest tests/
```

## 專案結構

```
windows-scheduler-gui/
├── pyproject.toml          # uv專案配置文件
├── .python-version         # Python版本指定
├── src/
│   ├── models/            # 資料模型
│   │   ├── enums.py       # 枚舉定義
│   │   ├── data_models.py # 核心資料模型
│   │   ├── help_models.py # 說明內容模型
│   │   └── statistics_models.py # 統計資料模型
│   ├── gui/               # GUI元件
│   ├── core/              # 核心業務邏輯
│   │   └── interfaces.py  # 核心介面定義
│   ├── storage/           # 資料存取層
│   └── utils/             # 工具函數
│       └── constants.py   # 常數定義
├── tests/                 # 測試文件
└── .venv/                 # uv虛擬環境
```

## 核心元件

### 資料模型
- **Task**: 排程任務定義
- **Schedule**: 排程配置
- **ExecutionResult**: 執行結果
- **AppConfig**: 應用程式配置
- **ExecutionLog**: 執行日誌

### 介面定義
- **ITaskManager**: 任務管理介面
- **ISchedulerEngine**: 排程引擎介面
- **IWindowsController**: Windows控制介面
- **IStorage**: 資料存儲介面

### 枚舉類型
- **ActionType**: 操作類型 (啟動、關閉、調整視窗等)
- **ScheduleType**: 排程類型 (一次性、每日、每週、自訂)
- **TaskStatus**: 任務狀態
- **ConditionType**: 條件觸發類型

## 使用方式

### 基本操作

1. **建立排程任務**: 選擇目標應用程式，設定操作類型和執行時間
2. **管理任務**: 編輯、刪除或暫停現有任務
3. **監控執行**: 查看任務執行狀態和歷史記錄
4. **系統設定**: 配置排程頻率、通知選項等

### 支援的操作類型

- `LAUNCH_APP`: 啟動應用程式
- `CLOSE_APP`: 關閉應用程式
- `RESIZE_WINDOW`: 調整視窗大小
- `MOVE_WINDOW`: 移動視窗位置
- `MINIMIZE_WINDOW`: 最小化視窗
- `MAXIMIZE_WINDOW`: 最大化視窗
- `CLICK_ELEMENT`: 點擊UI元素
- `TYPE_TEXT`: 輸入文字
- `SEND_KEYS`: 發送快捷鍵

## 開發指南

### 代碼風格

專案使用以下工具確保代碼品質：
- **Black**: 代碼格式化
- **Flake8**: 代碼檢查
- **MyPy**: 類型檢查
- **Pytest**: 單元測試

### 貢獻指南

1. Fork專案
2. 建立功能分支
3. 提交變更
4. 建立Pull Request

## 授權條款

本專案採用MIT授權條款 - 詳見[LICENSE](LICENSE)文件。

## 支援與聯絡

如有問題或建議，請透過以下方式聯絡：
- 建立Issue
- 發送Pull Request
- 查看專案Wiki