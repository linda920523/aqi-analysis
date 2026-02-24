#!/usr/bin/env python3
"""
檢查環境變數設定
"""

import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 檢查API Key
api_key = os.getenv('MOENV_API_KEY') or os.getenv('API_KEY')

print("=== 環境變數檢查 ===")
print(f"API_KEY: {api_key}")
print(f"API_KEY 類型: {type(api_key)}")
print(f"API_KEY 長度: {len(api_key) if api_key else 0}")

if api_key and api_key != 'your_api_key_here':
    print("[成功] API_KEY 已正確設定")
else:
    print("[錯誤] API_KEY 未正確設定")
    print("請在 .env 檔案中設定正確的API金鑰")

# 檢查.env檔案是否存在
env_file = '.env'
if os.path.exists(env_file):
    print(f"[成功] .env 檔案存在: {os.path.abspath(env_file)}")
    
    # 讀取檔案內容（不顯示完整金鑰）
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
        for line in lines:
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
