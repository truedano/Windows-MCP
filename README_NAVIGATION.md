# Windows Scheduler GUI - 統一導航系統實作

## 概述

已完成任務 6.2：建立統一導航系統，符合 design.md 中的規範。

## 實作內容

### 1. NavigationFrame 類別 (`src/gui/navigation.py`)

**核心功能**:
- 統一導航結構管理
- 頁面切換和狀態管理
- 響應式佈局支援
- 鍵盤快捷鍵支援
- 導航歷史記錄

**主要特點**:
- ✅ 現代化 Web 風格界面設計
- ✅ 五個主要導航頁面（Overview、Schedules、Logs、Settings、Help）
- ✅ 動態按鈕樣式（Normal、Active、Disabled、Hover）
- ✅ 工具提示（Tooltip）支援
- ✅ 響應式佈局適應不同視窗大小
- ✅ 頁面啟用/停用控制
- ✅ 頁面顯示/隱藏控制

### 2. PageManager 類別 (`src/gui/page_manager.py`)

**核心功能**:
- 頁面生命週期管理
- 頁面註冊和移除
- 頁面切換協調
- 內容刷新管理

**主要特點**:
- ✅ BasePage 抽象基類定義頁面介面
- ✅ 頁面懶載入（Lazy Loading）
- ✅ 頁面狀態管理（初始化、啟用、停用）
- ✅ 自動內容刷新機制

### 3. 頁面實作 (`src/gui/pages/`)

#### 3.1 OverviewPage - 系統概覽頁面
- ✅ 統計卡片顯示（活躍任務、總執行次數、成功率）
- ✅ 最近活動列表
- ✅ 系統狀態監控
- ✅ 動態數據更新

#### 3.2 SchedulesPage - 排程管理頁面
- ✅ 基礎頁面結構
- ⏳ 詳細功能待後續實作

#### 3.3 LogsPage - 執行記錄頁面
- ✅ 基礎頁面結構
- ⏳ 詳細功能待後續實作

#### 3.4 SettingsPage - 系統設定頁面
- ✅ 基礎頁面結構
- ⏳ 詳細功能待後續實作

#### 3.5 HelpPage - 說明文件頁面
- ✅ 基礎頁面結構
- ⏳ 詳細功能待後續實作

## 設計規範符合性

### 符合 design.md 統一導航結構

```
┌─────────────────────────────────────────────────────────────┐
│ ◆ Windows-MCP     Overview  Schedules  Logs  Settings  Help │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│    [主要內容區域 - 根據選中的導航項目顯示對應頁面]           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 導航項目對應

| 導航項目 | 中文名稱 | 功能描述 | 快捷鍵 |
|---------|---------|---------|--------|
| Overview | 系統概覽 | 顯示任務統計、系統狀態和最近活動 | Ctrl+1 |
| Schedules | 排程管理 | 包含排程清單、詳細資訊和建立/編輯功能 | Ctrl+2 |
| Logs | 執行記錄 | 顯示任務執行歷史和日誌搜尋 | Ctrl+3 |
| Settings | 系統設定 | 提供系統配置選項 | Ctrl+4 |
| Help | 說明文件 | 包含使用指南、FAQ和聯絡資訊 | F1 |

## 技術特點

### 1. 響應式設計

```python
def configure_responsive_layout(self, window_width: int):
    """根據視窗寬度調整佈局"""
    if window_width < 800:
        # 緊湊佈局
    elif window_width < 1200:
        # 中等佈局
    else:
        # 完整佈局
```

### 2. 狀態管理

```python
class NavigationState(Enum):
    NORMAL = "normal"
    ACTIVE = "active"
    DISABLED = "disabled"
    HOVER = "hover"
```

### 3. 頁面介面

```python
class PageInterface(ABC):
    @abstractmethod
    def on_page_enter(self) -> None: pass
    
    @abstractmethod
    def on_page_leave(self) -> None: pass
    
    @abstractmethod
    def refresh_content(self) -> None: pass
```

## API 使用範例

### 1. 切換頁面

```python
# 透過主視窗
main_window.switch_to_page("Schedules")

# 透過導航框架
navigation_frame.switch_to_page("Settings")
```

### 2. 頁面控制

```python
# 啟用/停用頁面
navigation_frame.set_page_enabled("Logs", False)

# 顯示/隱藏頁面
navigation_frame.set_page_visible("Help", False)
```

### 3. 頁面管理

```python
# 註冊新頁面
page_manager.register_page(CustomPage, *args, **kwargs)

# 刷新當前頁面
page_manager.refresh_current_page()
```

## 整合更新

### MainWindow 類別更新

- ✅ 移除舊的導航實作
- ✅ 整合 NavigationFrame 和 PageManager
- ✅ 添加響應式佈局支援
- ✅ 更新事件處理機制

### 檔案結構

```
src/gui/
├── __init__.py
├── main_window.py          # 主視窗（已更新）
├── navigation.py           # 導航系統（新增）
├── page_manager.py         # 頁面管理（新增）
├── scheduler_app.py        # 應用程式入口
└── pages/                  # 頁面實作（新增）
    ├── __init__.py
    ├── overview_page.py
    ├── schedules_page.py
    ├── logs_page.py
    ├── settings_page.py
    └── help_page.py
```

## 測試方式

### 1. 啟動應用程式

```bash
# 方式一：透過主程式
python main.py --gui

# 方式二：直接啟動
python src/gui/scheduler_app.py
```

### 2. 測試功能

- ✅ 點擊導航按鈕切換頁面
- ✅ 使用鍵盤快捷鍵（Ctrl+1~4, F1）
- ✅ 調整視窗大小測試響應式佈局
- ✅ 查看系統概覽頁面的統計資訊

## 下一步

根據 tasks.md，下一個任務是：
- **7.1 建立任務清單顯示** - 實作 TaskListWidget，顯示任務清單和狀態

## 完成狀態

✅ **任務 6.2 已完成並在 tasks.md 中標記為完成**

### 實作清單

- ✅ 實作 NavigationFrame 類別，管理統一的導航結構
- ✅ 建立 Overview、Schedules、Logs、Settings、Help 頁面的導航
- ✅ 實作頁面切換和狀態管理機制
- ✅ 設定響應式佈局，支援視窗大小調整
- ✅ 符合需求 1.1, 1.3

統一導航系統已成功實作，提供了現代化、響應式的導航體驗，為後續功能開發奠定了堅實基礎。