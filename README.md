# 0224homework Python 專案

## 專案結構

```
0224homework/
├── data/          # 存放原始資料
├── outputs/       # 存放分析結果
├── .env          # API設定檔
├── .gitignore    # Git忽略設定
└── README.md     # 專案說明
```

## 環境設定

1. 在 `.env` 檔案中加入您的API金鑰：
```
API_KEY=your_api_key_here
```

## 使用說明

- `data/` 資料夾用於存放原始資料檔案
- `outputs/` 資料夾用於存放分析結果和輸出檔案
- `.env` 檔案存放敏感資訊（API金鑰等）
- `.gitignore` 確保敏感檔案不被提交到Git

## 注意事項

- 請勿將 `.env` 檔案提交到版本控制系統
- 請確保在分享程式碼前移除或替換真實的API金鑰
