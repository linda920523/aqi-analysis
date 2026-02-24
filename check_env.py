#!/usr/bin/env python3
"""
檢查環境變數設定
"""

import os
from dotenv import load_dotenv

# 載入環境變數：
# - 預設會讀取同目錄的 `.env` 檔案
# - 將 KEY=VALUE 形式寫入到目前 Python 程式的環境變數中
# - 這樣後續就能用 os.getenv("KEY") 取得設定值
load_dotenv()

# 檢查 API Key：
# - 本專案優先使用 `MOENV_API_KEY`
# - 若你習慣用 `API_KEY` 也能相容
api_key = os.getenv('MOENV_API_KEY') or os.getenv('API_KEY')

print("=== 環境變數檢查 ===")
# 注意：這裡會把整串 API key 印出來。
# 若你要錄影/截圖給老師，可自行把這行註解掉，避免 key 外洩。
print(f"API_KEY: {api_key}")
print(f"API_KEY 類型: {type(api_key)}")
print(f"API_KEY 長度: {len(api_key) if api_key else 0}")

if api_key and api_key != 'your_api_key_here':
    print("[成功] API_KEY 已正確設定")
else:
    print("[錯誤] API_KEY 未正確設定")
    print("請在 .env 檔案中設定正確的API金鑰")

# 進一步檢查 `.env` 檔案是否存在，並確認內容格式是否正確
env_file = '.env'
if os.path.exists(env_file):
    print(f"[成功] .env 檔案存在: {os.path.abspath(env_file)}")
    
    # 讀取檔案內容（不顯示完整金鑰）
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
        for line in lines:
            # 尋找 KEY=VALUE 形式的設定行
            if line.startswith('MOENV_API_KEY=') or line.startswith('API_KEY='):
                key_value = line.split('=', 1)
                if len(key_value) > 1:
                    key = key_value[1]
                    if key == 'your_api_key_here':
                        print("[錯誤] .env 檔案中的API_KEY仍是預設值")
                    else:
                        print(f"[成功] .env 檔案中的API_KEY已設定 (長度: {len(key)})")
                break
else:
    print("[錯誤] .env 檔案不存在")
