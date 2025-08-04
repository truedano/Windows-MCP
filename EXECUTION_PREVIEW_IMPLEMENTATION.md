# ExecutionPreviewWidget 實作文件

## 概述

ExecutionPreviewWidget 是一個完整實作的 Tkinter 小工具，用於顯示排程任務的執行預覽。該小工具提供了詳細的視覺化預覽，包括動作參數、條件觸發、執行時間軸和安全警告。

## 功能特性

### 1. 實作ExecutionPreviewWidget，顯示將要執行的具體操作 ✅

ExecutionPreviewWidget 已完全實作，提供以下功能：

- **基本資訊顯示**：排程名稱、目標應用程式
- **排程設定顯示**：支援一次性、每日、每週、自訂間隔等排程類型
- **動作資訊顯示**：詳細的動作類型和參數說明
- **執行選項顯示**：重複執行、失敗重試、通知、日誌記錄等選項

#### 支援的動作類型：
- `LAUNCH_APP` - 啟動應用程式
- `CLOSE_APP` - 關閉應用程式  
- `RESIZE_WINDOW` - 調整視窗大小
- `MOVE_WINDOW` - 移動視窗位置
- `MINIMIZE_WINDOW` - 最小化視窗
- `MAXIMIZE_WINDOW` - 最大化視窗
- `RESTORE_WINDOW` - 還原視窗
- `FOCUS_WINDOW` - 聚焦視窗
- `CLICK_ELEMENT` - 點擊元素
- `TYPE_TEXT` - 輸入文字
- `SEND_KEYS` - 發送按鍵
- `CUSTOM_COMMAND` - 執行自訂命令

### 2. 建立動作參數和條件觸發的可視化顯示 ✅

#### 動作參數可視化：
- **視窗大小參數**：顯示 `width x height` 格式
- **位置參數**：顯示 `(x, y)` 座標格式
- **文字輸入參數**：顯示輸入文字內容和操作位置
- **按鍵組合參數**：顯示 `key1 + key2` 格式
- **自訂命令參數**：顯示完整的 PowerShell 命令

#### 條件觸發可視化：
- **條件類型顯示**：
  - `WINDOW_TITLE_CONTAINS` - 視窗標題包含
  - `WINDOW_TITLE_EQUALS` - 視窗標題等於
  - `WINDOW_EXISTS` - 視窗存在
  - `PROCESS_RUNNING` - 程序運行中
  - `TIME_RANGE` - 時間範圍
  - `SYSTEM_IDLE` - 系統閒置
- **條件值顯示**：顯示具體的條件參數
- **條件說明**：提供條件觸發的使用說明

### 3. 實作即時預覽更新機制 ✅

ExecutionPreviewWidget 提供完整的即時更新功能：

- **配置變更檢測**：當排程配置發生變更時自動更新預覽
- **錯誤處理**：配置錯誤時顯示友善的錯誤訊息
- **效能優化**：使用高效的文字更新機制，避免不必要的重繪
- **狀態管理**：正確管理文字小工具的啟用/停用狀態

#### 更新觸發條件：
- 排程名稱變更
- 目標應用程式變更
- 排程時間設定變更
- 動作類型或參數變更
- 條件觸發設定變更
- 執行選項變更

### 4. 建立執行前確認機制 ✅

ExecutionPreviewWidget 包含完整的執行前確認機制：

#### 安全警告系統：
- **自訂命令警告**：檢測 `CUSTOM_COMMAND` 動作類型，顯示安全提醒
- **系統應用警告**：檢測系統關鍵應用程式（cmd、powershell、regedit），顯示安全警告
- **高頻執行警告**：檢測執行間隔過短（< 60秒），提醒可能的效能影響

#### 執行時間軸預覽：
- **下次執行時間**：計算並顯示下次執行的具體時間
- **執行倒數計時**：顯示距離執行的剩餘時間
- **多次執行預覽**：對於重複排程，顯示接下來的多次執行時間

#### 確認訊息：
- **預覽模式提醒**：明確標示這是預覽模式，實際執行前需要測試
- **條件觸發提醒**：當啟用條件觸發時，提醒實際執行時間可能不同

## 技術實作細節

### 類別結構

```python
class ExecutionPreviewWidget(ttk.Frame):
    def __init__(self, parent: tk.Widget)
    def _create_ui(self)
    def _show_empty_preview(self)
    def _update_text_content(self, content_lines: List[tuple])
    def update_preview(self, config: Dict[str, Any])
    def _add_schedule_info(self, content_lines: List[tuple], schedule_config: Dict[str, Any])
    def _add_conditional_trigger_info(self, content_lines: List[tuple], trigger_config)
    def _add_action_info(self, content_lines: List[tuple], action_type, action_params: Dict[str, Any])
    def _add_options_info(self, content_lines: List[tuple], options: Dict[str, Any])
    def _add_execution_timeline(self, content_lines: List[tuple], config: Dict[str, Any])
    def _add_warnings_and_notes(self, content_lines: List[tuple], config: Dict[str, Any])
    def _format_timedelta(self, td: timedelta) -> str
    def _calculate_next_executions(self, schedule_config: Dict[str, Any], from_time: datetime, count: int) -> List[datetime]
```

### 文字格式化標籤

- `header` - 主標題（藍色粗體）
- `subheader` - 子標題（深藍色粗體）
- `info` - 一般資訊（黑色）
- `warning` - 警告訊息（橙色）
- `error` - 錯誤訊息（紅色）
- `success` - 成功訊息（綠色）

### 與 ScheduleDialog 的整合

ExecutionPreviewWidget 已完全整合到 ScheduleDialog 中：

1. **標籤頁整合**：作為獨立的「執行預覽」標籤頁
2. **即時更新**：所有配置變更都會觸發預覽更新
3. **錯誤處理**：配置錯誤時顯示適當的錯誤訊息
4. **使用者體驗**：提供直觀的預覽介面，幫助使用者理解排程配置

## 測試驗證

### 功能測試

已通過以下測試驗證：

1. **基本功能測試** ✅
   - 小工具初始化
   - 空預覽顯示
   - 基本配置預覽

2. **排程類型測試** ✅
   - 一次性執行預覽
   - 每日重複預覽
   - 每週重複預覽
   - 自訂間隔預覽

3. **動作參數測試** ✅
   - 視窗操作參數顯示
   - 文字輸入參數顯示
   - 按鍵組合參數顯示
   - 自訂命令參數顯示

4. **條件觸發測試** ✅
   - 條件類型顯示
   - 條件值顯示
   - 條件說明顯示

5. **執行時間軸測試** ✅
   - 未來執行時間計算
   - 倒數計時顯示
   - 時間格式化

6. **警告系統測試** ✅
   - 自訂命令警告
   - 系統應用警告
   - 高頻執行警告

7. **即時更新測試** ✅
   - 配置變更檢測
   - 預覽內容更新
   - 錯誤處理

8. **整合測試** ✅
   - ScheduleDialog 整合
   - 事件綁定
   - 使用者互動

### 演示應用程式

提供了完整的演示應用程式 `demo_execution_preview.py`，包含：

- 8 種不同的演示場景
- 手動配置介面
- 即時預覽更新
- 完整的功能展示

## 使用方式

### 基本使用

```python
from gui.widgets.execution_preview_widget import ExecutionPreviewWidget

# 建立小工具
preview_widget = ExecutionPreviewWidget(parent_widget)

# 更新預覽
config = {
    'name': '測試排程',
    'target_app': 'notepad',
    'schedule': {...},
    'action_type': ActionType.LAUNCH_APP,
    'action_params': {...},
    'options': {...}
}
preview_widget.update_preview(config)
```

### 在 ScheduleDialog 中使用

ExecutionPreviewWidget 已整合到 ScheduleDialog 中，會自動：

1. 監聽配置變更
2. 即時更新預覽
3. 顯示錯誤訊息
4. 提供執行確認

## 結論

ExecutionPreviewWidget 的實作完全滿足任務 8.4 的所有要求：

✅ **實作ExecutionPreviewWidget，顯示將要執行的具體操作**
✅ **建立動作參數和條件觸發的可視化顯示**
✅ **實作即時預覽更新機制**
✅ **建立執行前確認機制**

該實作提供了完整的執行預覽功能，包括詳細的動作說明、參數顯示、時間軸預覽、安全警告和確認機制，大大提升了使用者體驗和系統安全性。