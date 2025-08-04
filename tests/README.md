# 測試說明

## 應用程式監控功能測試

### 自動化測試
運行單元測試：
```bash
uv run python -m pytest tests/test_app_monitoring.py -v
```

### 手動測試
運行手動測試來驗證 GUI 功能：
```bash
uv run python tests/test_app_monitoring_manual.py
```

手動測試提供兩個選項：
1. **App Monitor Panel** - 測試應用程式監控面板
2. **Apps Page** - 測試完整的應用程式頁面

### 測試功能

#### AppListWidget 測試
- 應用程式清單顯示
- 搜尋功能
- 篩選功能（全部、僅可見、有視窗）
- 自動重新整理
- 應用程式選擇

#### AppDetailWidget 測試
- 詳細資訊顯示
- 視窗資訊顯示
- 快速操作按鈕
- 操作結果回饋

#### AppMonitorPanel 測試
- 整合面板功能
- 左右面板互動
- 應用程式選擇同步

### 注意事項
- 手動測試需要在有 GUI 環境的系統上運行
- 某些功能需要管理員權限才能完全測試
- 測試時會顯示實際運行的應用程式