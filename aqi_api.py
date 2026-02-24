#!/usr/bin/env python3
"""aqi_api.py

環境部空氣品質（AQI）資料擷取與視覺化程式。

本程式主要做的事情：
1. 從環境部開放資料 API（資料集代碼：aqx_p_432）取得「全台即時 AQI」資料。
2. 將 API 回傳的 JSON 轉成 pandas DataFrame 方便後續處理。
3. 進行空間計算：每個測站到「台北車站」的距離（公里）。
4. 使用 folium 產生互動式地圖（輸出 HTML），並把資料輸出為 CSV/JSON。

輸入：
- `.env` 內的 API Key（優先讀取 `MOENV_API_KEY`，備援 `API_KEY`）

輸出（存放於 `./outputs/`）：
- aqi_data_YYYYMMDD_HHMMSS.csv
- aqi_data_YYYYMMDD_HHMMSS.json
- aqi_map_YYYYMMDD_HHMMSS.html
"""

import os
import requests
import json
import pandas as pd
import folium
import urllib3
import math
from datetime import datetime
from dotenv import load_dotenv

# 禁用 SSL 警告：
# 有些環境（例如校園網路/特定憑證鏈）可能會遇到 SSL 憑證驗證問題。
# 這裡搭配 requests.get(..., verify=False) 使用，因此需要關閉 InsecureRequestWarning。
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 載入環境變數：
# 會讀取同目錄下的 .env，將其中的 KEY=VALUE 載入到環境變數。
load_dotenv()

# 台北車站座標（WGS84）：作為距離計算的目標點
TAIPEI_MAIN_STATION_LAT = 25.0478
TAIPEI_MAIN_STATION_LON = 121.5170


def haversine_km(lat1, lon1, lat2, lon2):
    """使用 Haversine 公式計算兩個經緯度點之間的球面距離（公里）。

    為什麼不用平面距離？
    - 經緯度在地球表面是球面座標；Haversine 是常用的近似計算方式。
    - 對台灣尺度的距離估算已足夠。
    """
    r = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c

class AQIAPI:
    def __init__(self):
        # 讀取 API Key：
        # - MOENV_API_KEY：你在作業中使用的環境部 API key 變數名稱
        # - API_KEY：保留相容舊寫法
        self.api_key = os.getenv('MOENV_API_KEY') or os.getenv('API_KEY')

        # 可能的 API 端點（做容錯）：
        # - 優先使用 data.moenv.gov.tw
        # - 若 DNS/網路環境無法解析，再嘗試舊的 data.epa.gov.tw
        self.base_urls = [
            "https://data.moenv.gov.tw/api/v2",
            "https://data.epa.gov.tw/api/v2",
        ]
        
        if not self.api_key:
            # 沒有 API key 就不往下跑，避免發送匿名/錯誤請求
            print("請在 .env 檔案中設定 MOENV_API_KEY (或 API_KEY)")
            print("範例: MOENV_API_KEY=your_api_key_here")
            return
        
        print(f"API金鑰已載入: {self.api_key[:8]}...")
    
    def fetch_aqi_data(self):
        """
        獲取全台AQI資料
        
        Returns:
            dict: API回應資料
        """
        # API 查詢參數：
        # - api_key：授權金鑰
        # - format：回傳格式（JSON）
        params = {
            "api_key": self.api_key,
            "format": "JSON"
        }

        # last_error 用於記錄最後一次錯誤，若全部端點都失敗可提供診斷訊息
        last_error = None
        for base_url in self.base_urls:
            url = f"{base_url}/aqx_p_432"
            try:
                print(f"正在獲取空氣品質資料... ({base_url})")

                # verify=False：避免 SSL 憑證問題阻擋資料抓取（課堂環境常見）
                response = requests.get(url, params=params, timeout=30, verify=False)

                # HTTP 狀態碼非 2xx 會在這裡丟出例外
                response.raise_for_status()

                # 解析 JSON
                data = response.json()

                # 部分端點可能直接回傳 list[dict]，這裡統一成 dict 格式
                if isinstance(data, list):
                    data = {
                        "success": True,
                        "records": data,
                    }

                if data.get("success"):
                    records = data.get("records", [])
                    print(f"成功獲取 {len(records)} 個測站資料")
                    return data
                else:
                    # API 回應 success=False 時，直接回傳 None
                    print(f"API回應失敗: {data.get('message', '未知錯誤')}")
                    return None

            except requests.exceptions.RequestException as e:
                # 任何 requests 層級錯誤（DNS、Timeout、HTTPError...）都會到這裡
                last_error = e
                print(f"API請求錯誤: {e}")
                continue
            except json.JSONDecodeError as e:
                # 回傳內容不是合法 JSON 時會到這裡
                last_error = e
                print(f"JSON解析錯誤: {e}")
                continue

        if last_error is not None:
            # 所有端點都失敗時，提供常見排除方向
            print("所有 API 端點都連線失敗，因此不會產生 outputs 的地圖/資料檔案。")
            print("請檢查：")
            print("1. 網路連線是否正常")
            print("2. DNS 是否可解析 data.moenv.gov.tw")
            print("3. 是否有代理/防火牆阻擋")
        return None
    
    def process_aqi_data(self, data):
        """
        處理AQI資料
        
        Args:
            data (dict): API回應的AQI資料
        
        Returns:
            pd.DataFrame: 處理後的AQI資料
        """
        if not data or not data.get("records"):
            return None
        
        # records 是一個 list，每個元素是一個測站的資料（dict）
        records = data["records"]
        processed_data = []
        
        for record in records:
            try:
                # 同時支援 EPA 舊格式(大寫)與 MOENV 新格式(小寫)
                # 例如：
                # - 新格式：latitude / longitude / aqi / sitename / county
                # - 舊格式：Latitude / Longitude / AQI / SiteName / County
                latitude_raw = record.get("Latitude") if record.get("Latitude") is not None else record.get("latitude")
                longitude_raw = record.get("Longitude") if record.get("Longitude") is not None else record.get("longitude")
                
                # 處理座標資料：轉成 float
                lat = float(latitude_raw) if latitude_raw not in (None, "") else None
                lon = float(longitude_raw) if longitude_raw not in (None, "") else None
                
                # 處理 AQI 數值：
                # API 有時會用字串回傳（例如 "86"），因此先轉 float 再轉 int
                aqi_raw = record.get("AQI") if record.get("AQI") is not None else record.get("aqi")
                aqi = None
                if aqi_raw not in (None, ""):
                    try:
                        aqi = int(float(aqi_raw))
                    except (ValueError, TypeError):
                        aqi = None
                
                # 處理 PM2.5：同樣可能是字串或空值
                pm25_raw = (
                    record.get("PM2.5")
                    if record.get("PM2.5") is not None
                    else (record.get("pm2.5") if record.get("pm2.5") is not None else record.get("pm25"))
                )
                pm25 = None
                if pm25_raw not in (None, ""):
                    try:
                        pm25 = float(pm25_raw)
                    except (ValueError, TypeError):
                        pm25 = None
                
                # 轉成「我們專案內一致的欄位名稱」方便後續 map / export
                station_data = {
                    'site_id': record.get("SiteId") if record.get("SiteId") is not None else record.get("siteid", ""),
                    'site_name': record.get("SiteName") if record.get("SiteName") is not None else record.get("sitename", ""),
                    'county': record.get("County") if record.get("County") is not None else record.get("county", ""),
                    'latitude': lat,
                    'longitude': lon,
                    'aqi': aqi,
                    'pm25': pm25,
                    'status': record.get("Status") if record.get("Status") is not None else record.get("status", ""),
                    'pollutant': record.get("Pollutant") if record.get("Pollutant") is not None else record.get("pollutant", ""),
                    'publish_time': record.get("PublishTime") if record.get("PublishTime") is not None else record.get("publishtime", ""),
                    'wind_speed': record.get("WindSpeed") if record.get("WindSpeed") is not None else record.get("wind_speed", ""),
                    'wind_direction': record.get("WindDirec") if record.get("WindDirec") is not None else record.get("wind_direc", "")
                }
                
                processed_data.append(station_data)
                
            except (ValueError, TypeError) as e:
                print(f"處理測站 {record.get('SiteName', 'unknown')} 資料時發生錯誤: {e}")
                continue
        
        # 將 list[dict] 轉成 DataFrame
        df = pd.DataFrame(processed_data)

        # 過濾掉無效座標的資料
        df = df[df['latitude'].notna() & df['longitude'].notna()]
        df = df[(df['latitude'] != 0) & (df['longitude'] != 0)]
        
        return df

    def add_distance_to_taipei_main_station(self, df):
        """新增距離欄位：每個測站到台北車站的距離（公里）。

        產生的欄位名稱：distance_to_taipei_main_km
        """
        if df is None or df.empty:
            return df

        # copy() 避免修改到原始 df（保留函式式風格，較安全）
        df = df.copy()

        # 使用 DataFrame.apply 逐列計算距離
        df['distance_to_taipei_main_km'] = df.apply(
            lambda r: haversine_km(
                float(r['latitude']),
                float(r['longitude']),
                TAIPEI_MAIN_STATION_LAT,
                TAIPEI_MAIN_STATION_LON,
            ),
            axis=1,
        )
        return df
    
    def get_aqi_color(self, aqi):
        """
        根據AQI數值回傳對應顏色
        
        Args:
            aqi (int): AQI數值
        
        Returns:
            str: 顏色代碼
        """
        # 若該測站沒有 AQI（空值），使用灰色
        if aqi is None:
            return 'gray'
        
        # 作業需求的三段分色：
        # 0-50 綠色、51-100 黃色、101+ 紅色
        if aqi <= 50:
            return 'green'
        elif aqi <= 100:
            return 'yellow'
        else:
            return 'red'
    
    def get_aqi_level(self, aqi):
        """
        根據AQI數值回傳等級描述
        
        Args:
            aqi (int): AQI數值
        
        Returns:
            str: AQI等級描述
        """
        # 這個等級描述目前主要用在程式內部（若你未來想在地圖 popup 顯示）
        if aqi is None:
            return '資料不足'
        
        if aqi <= 50:
            return '良好'
        elif aqi <= 100:
            return '中等'
        else:
            return '不健康'
    
    def create_aqi_map(self, df):
        """
        建立AQI地圖
        
        Args:
            df (pd.DataFrame): AQI資料
        
        Returns:
            folium.Map: AQI地圖
        """
        # 防呆：沒有資料就不產地圖
        if df is None or df.empty:
            print("沒有資料可以製作地圖")
            return None
        
        # 計算「地圖中心點」：用所有測站的平均座標當作地圖中心
        center_lat = df['latitude'].mean()
        center_lon = df['longitude'].mean()
        
        # 建立底圖：
        # zoom_start=8 適合台灣全圖視角
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=8,
            tiles='OpenStreetMap'
        )
        
        # 將每個測站畫成 CircleMarker
        for idx, row in df.iterrows():
            try:
                aqi = row['aqi']
                color = self.get_aqi_color(aqi)
                
                # 點擊後顯示的 popup（作業需求：站名、縣市、AQI）
                popup_content = f"""
                <div style="width: 220px;">
                    <b>測站:</b> {row['site_name']}<br>
                    <b>縣市:</b> {row['county']}<br>
                    <b>AQI:</b> {aqi if aqi is not None else 'N/A'}
                </div>
                """
                
                # tooltip：滑鼠移到點上會顯示的簡短文字
                folium.CircleMarker(
                    location=[row['latitude'], row['longitude']],
                    radius=10,
                    popup=folium.Popup(popup_content, max_width=300),
                    tooltip=f"{row['site_name']}: AQI {aqi if aqi else 'N/A'}",
                    color=color,
                    fill=True,
                    fillColor=color,
                    fillOpacity=0.7,
                    weight=2
                ).add_to(m)
                
            except Exception as e:
                # 單一測站資料異常時略過，避免整張地圖生成失敗
                print(f"處理測站 {row.get('site_name', 'unknown')} 時發生錯誤: {e}")
                continue
        
        # 加上左下角圖例（使用 HTML 元素固定在畫面上）
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 180px; height: 120px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <h4>AQI 圖例</h4>
        <p><i class="fa fa-circle" style="color:green"></i> 0-50</p>
        <p><i class="fa fa-circle" style="color:yellow"></i> 51-100</p>
        <p><i class="fa fa-circle" style="color:red"></i> 101+</p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # 加上右下角統計資訊（同樣用固定 HTML）
        total_stations = len(df)
        valid_aqi = len(df[df['aqi'].notna()])
        avg_aqi = df['aqi'].mean() if valid_aqi > 0 else 0
        max_aqi = df['aqi'].max() if valid_aqi > 0 else 0
        
        stats_html = f"""
        <div style="position: fixed; 
                    bottom: 50px; right: 50px; width: 200px; height: 120px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <h4>空氣品質統計</h4>
        <p><b>總測站數:</b> {total_stations}</p>
        <p><b>有效AQI:</b> {valid_aqi}</p>
        <p><b>平均AQI:</b> {avg_aqi:.1f}</p>
        <p><b>最高AQI:</b> {max_aqi}</p>
        </div>
        """
        m.get_root().html.add_child(folium.Element(stats_html))
        
        return m
    
    def save_data(self, df, filename=None):
        """
        儲存AQI資料到檔案
        
        Args:
            df (pd.DataFrame): AQI資料
            filename (str, optional): 檔案名稱
        """
        # 沒資料就不輸出
        if df is None or df.empty:
            print("沒有資料可儲存")
            return
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"aqi_data_{timestamp}"
        
        # 確保 outputs 目錄存在
        output_dir = os.path.join(".", "outputs")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 儲存 CSV：使用 utf-8-sig，讓 Excel 開啟中文欄位不容易亂碼
        csv_path = os.path.join(output_dir, f"{filename}.csv")
        try:
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            print(f"CSV資料已儲存至: {csv_path}")
        except Exception as e:
            print(f"儲存CSV資料時發生錯誤: {e}")
        
        # 儲存 JSON：force_ascii=False 保留中文
        json_path = os.path.join(output_dir, f"{filename}.json")
        try:
            df.to_json(json_path, orient='records', force_ascii=False, indent=2)
            print(f"JSON資料已儲存至: {json_path}")
        except Exception as e:
            print(f"儲存JSON資料時發生錯誤: {e}")
    
    def save_map(self, map_obj, filename=None):
        """
        儲存地圖
        
        Args:
            map_obj (folium.Map): 地圖物件
            filename (str, optional): 檔案名稱
        """
        # 沒有地圖物件就不輸出
        if map_obj is None:
            print("沒有地圖可以儲存")
            return
        
        output_dir = os.path.join(".", "outputs")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"aqi_map_{timestamp}"
        
        map_file = os.path.join(output_dir, f"{filename}.html")
        
        # map_obj.save() 會輸出成一個可在瀏覽器開啟的 HTML
        try:
            map_obj.save(map_file)
            print(f"地圖已儲存至: {map_file}")
            return map_file
        except Exception as e:
            print(f"儲存地圖時發生錯誤: {e}")
            return None

def main():
    """主程式

    這裡是整個流程的控制中心：
    1. 讀取 API key、連線抓資料
    2. 清理/轉換資料
    3. 計算距離
    4. 產生地圖
    5. 輸出 CSV/JSON/HTML
    """
    print("=== 環境部空氣品質API串接程式 ===")
    
    try:
        # 初始化 API 客戶端（讀取 .env / 準備 base_url）
        api = AQIAPI()
        
        if not api.api_key:
            print("無法繼續執行，請先設定API金鑰")
            return
        
        # 1) 呼叫 API 取得原始資料
        aqi_data = api.fetch_aqi_data()
        
        if aqi_data:
            # 2) 將原始 JSON records 轉成 DataFrame
            df = api.process_aqi_data(aqi_data)
            
            if df is not None and not df.empty:
                print(f"\n成功處理 {len(df)} 個有效測站資料")
                
                # 顯示基本統計（方便確認資料合理性）
                print(f"\n=== AQI統計資訊 ===")
                valid_aqi = df[df['aqi'].notna()]
                if not valid_aqi.empty:
                    print(f"有效AQI資料: {len(valid_aqi)} 站")
                    print(f"AQI範圍: {valid_aqi['aqi'].min()} ~ {valid_aqi['aqi'].max()}")
                    print(f"平均AQI: {valid_aqi['aqi'].mean():.1f}")
                
                # 顯示前5筆資料
                print(f"\n前5筆測站資料:")
                for i, (_, row) in enumerate(df.head().iterrows()):
                    aqi_str = f"{row['aqi']}" if pd.notna(row['aqi']) else "N/A"
                    print(f"{i+1}. {row['site_name']} ({row['county']}) - AQI: {aqi_str}")
                
                # 3) 空間計算：新增到台北車站距離
                # 4) 產生 folium 地圖
                print(f"\n正在建立AQI地圖...")
                df = api.add_distance_to_taipei_main_station(df)
                aqi_map = api.create_aqi_map(df)
                
                # 5) 輸出資料與地圖到 outputs/
                api.save_data(df)
                if aqi_map:
                    api.save_map(aqi_map)
                
                print(f"\n=== 程式執行完成 ===")
                print("請在瀏覽器中開啟 outputs/ 資料夾中的HTML檔案查看AQI地圖")
                
            else:
                print("沒有提取到有效的AQI資料")
        
    except Exception as e:
        print(f"程式執行錯誤: {e}")

if __name__ == "__main__":
    main()
