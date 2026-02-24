"""main.py

此檔案是整個專案的「入口檔」。

目的：
- 讓老師/助教只要執行 `python main.py` 就能跑完整流程。
- 將主要流程集中在 `aqi_api.py` 的 `main()`，這裡只負責呼叫。

這樣做的好處：
- 專案結構更清楚（main.py = 入口；aqi_api.py = 核心邏輯）。
- 後續若要擴充其他分析流程，也可在 main.py 統一管理。
"""

# 從 aqi_api.py 匯入主流程函式 main()
from aqi_api import main


if __name__ == "__main__":
    # 直接執行 aqi_api.py 中定義的主流程
    main()
