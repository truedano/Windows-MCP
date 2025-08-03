# Windows Scheduler GUI - 主視窗實作

## 概述

已完成任務 6.1：實作主視窗結構，符合 design.md 中的規範。

## 實作內容

### 1. 主視窗結構 (MainWindow)

- **檔案位置**: `src/gui/main_window.py`
- **功能特點**:
  - 完整的選單列（檔案、編輯、檢視、工具、說明）
  - 統一導航結構（Overview、Schedules、Logs、Settings、Help）
  - 狀態列顯示系統狀態和連接狀態
  - 響應式佈局，支援視窗大小調整
  - 鍵盤快捷鍵支援

### 2. 應用程式入口 (SchedulerApp)

- **檔案位置**: `src/gui/scheduler_app.py`
- **功能特點**:
  - 配置管理（自動載入/儲存）
  - 錯誤處理和異常管理
  - 應用程式生命週期管理

### 3. 統一導航系統

按照 design.md 規範實作的五個主要頁面：

1. **Overview (系統概覽)**
   - 系統統計資訊（活躍任務、總執行次數、成功率）
   - 最近活動記錄
   - 系統狀態監控

2. **Schedules (排程管理)**
   - 排程清單和管理（待後續實作）

3. **Logs (執行記錄)**
   - 任務執行歷史和日誌（待後續實作）

4. **Settings (系統設定)**
   - 系統配置選項（待後續實作）

5. **Help (說明文件)**
   - 使用指南和支援資訊（待後續實作）

## 設計特點

### 符合 design.md 規範

1. **主視窗佈局**:
   ```
   ┌─────────────────────────────────────────────────────────────┐
   │ ◆ Windows-MCP     Overview  Schedules  Logs  Settings  Help │
   ├─────────────────────────────────────────────────────────────┤
   │                                                             │
   │    [主要內容區域 - 根據選中的導航項目顯示對應頁面]           │
   │                                                             │
   └─────────────────────────────────────────────────────────────┘
   ```

2. **統一導航結構**: 採用現代化 Web 風格界面設計
3. **響應式設計**: 支援視窗大小調整和全螢幕模式
4. **本地化支援**: 繁體中文界面

### 技術實作

- **GUI 框架**: Python Tkinter
- **配置管理**: JSON 格式配置文件
- **模組化設計**: 清晰的類別結構和職責分離
- **錯誤處理**: 完整的異常處理機制

## 使用方式

### 1. 直接啟動 GUI

```bash
python src/gui/scheduler_app.py
```

### 2. 從主程式啟動

```bash
python main.py --gui
```

### 3. 測試主視窗

```bash
python tmp_rovodev_test_gui.py
```

## 配置文件

應用程式會自動在 `.config/config.json` 中儲存配置：

```json
{
  "schedule_check_frequency": 1,
  "notifications_enabled": true,
  "log_recording_enabled": true,
  "log_retention_days": 30,
  "max_retry_attempts": 3,
  "ui_theme": "default",
  "language": "zh-TW",
  "window_width": 1024,
  "window_height": 768,
  "auto_start_scheduler": true,
  "minimize_to_tray": true,
  "show_splash_screen": true,
  "debug_mode": false
}
```

## 功能特點

### 已實作功能

- ✅ 主視窗結構和佈局
- ✅ 選單列和工具列
- ✅ 統一導航系統
- ✅ 狀態列
- ✅ 系統概覽頁面
- ✅ 配置管理
- ✅ 視窗事件處理
- ✅ 鍵盤快捷鍵
- ✅ 錯誤處理

### 待實作功能（後續任務）

- ⏳ 排程管理頁面詳細功能
- ⏳ 執行記錄頁面
- ⏳ 系統設定頁面
- ⏳ 說明文件頁面
- ⏳ 任務建立/編輯對話框
- ⏳ 系統匣功能
- ⏳ 通知系統

## 下一步

根據 tasks.md，下一個任務是：
- **6.2 建立統一導航系統** - 進一步完善導航功能和頁面切換機制

## 測試狀態

主視窗結構已通過基本測試，包括：
- 視窗初始化
- 配置載入
- 導航結構建立
- 頁面管理
- 事件處理

任務 6.1 已完成並在 tasks.md 中標記為完成 ✅