# 環境部AQI API 設定指南

## 🔧 API金鑰設定

### 步驟1：取得環境部API金鑰

1. 訪問 [環境部開放資料平台](https://data.epa.gov.tw/)
2. 註冊帳號並申請API金鑰
3. 取得您的API金鑰

### 步驟2：設定.env檔案

在專案根目錄的 `.env` 檔案中加入：

```env
API_KEY=您的實際API金鑰
```

**範例**：
```env
API_KEY=EPA-12345678-ABCD-EFGH-IJKL-MNOPQRSTUVWXYZ
```

## 🚀 執行程式

### 自動安裝環境（已完成）
```bash
python install.py
```

### 執行AQI資料獲取
```bash
python aqi_api.py
```

## 📊 輸出檔案

程式會在 `outputs/` 資料夾中產生：

1. **`aqi_data_YYYYMMDD_HHMMSS.csv`** - AQI資料CSV格式
2. **`aqi_data_YYYYMMDD_HHMMSS.json`** - AQI資料JSON格式  
3. **`aqi_map_YYYYMMDD_HHMMSS.html`** - 互動式AQI地圖

## 🗺️ AQI地圖功能

- **顏色分級**：
  - 🟢 綠色：良好 (0-50)
  - 🟡 黃色：中等 (51-100)
  - 🟠 橘色：對敏感族群不健康 (101-150)
  - 🔴 紅色：對所有族群不健康 (151-200)
  - 🟣 紫色：非常不健康 (201-300)
  - 🟤 褐色：危害 (300+)

- **互動功能**：
  - 點擊測站顯示詳細資訊
  - AQI數值、狀態、主要污染物
  - PM2.5、風速、風向等資訊
  - 更新時間顯示

## 📈 資料欄位說明

| 欄位 | 說明 |
|------|------|
| site_id | 測站代碼 |
| site_name | 測站名稱 |
| county | 所在縣市 |
| latitude | 緯度 |
| longitude | 經度 |
| aqi | AQI數值 |
| pm25 | PM2.5濃度 (μg/m³) |
| status | 空氣品質狀態 |
| pollutant | 主要污染物 |
| publish_time | 資料發布時間 |
| wind_speed | 風速 (m/s) |
| wind_direction | 風向 |

## 🔍 故障排除

### 常見問題

1. **API金鑰錯誤**
   - 檢查 `.env` 檔案中的API金鑰是否正確
   - 確認API金鑰是否有效且未過期

2. **網路連線問題**
   - 檢查網路連線是否正常
   - 確認防火牆設定

3. **套件安裝失敗**
   - 重新執行 `python install.py`
   - 或手動安裝：`pip install -r requirements.txt`

### 測試API連線

如果API連線有問題，可以檢查：
- API金鑰權限是否足夠
- API端點是否正確
- 網路連線是否穩定

## 📞 技術支援

如需協助，請檢查：
1. `.env` 檔案設定
2. 網路連線狀態
3. API金鑰有效性

程式會顯示詳細的錯誤訊息協助除錯。
