#!/usr/bin/env python3
"""
自動安裝環境套件
"""

import subprocess
import sys
import os

def install_package(package):
    """安裝單一套件"""
    try:
        print(f"正在安裝 {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} 安裝成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {package} 安裝失敗: {e}")
        return False

def install_requirements():
    """從requirements.txt安裝套件"""
    requirements_file = "requirements.txt"
    
    if not os.path.exists(requirements_file):
        print("❌ 找不到 requirements.txt 檔案")
        return False
    
    try:
        print("正在從 requirements.txt 安裝套件...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_file])
        print("✅ 所有套件安裝成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 從 requirements.txt 安裝失敗: {e}")
        return False

def check_package(package_name):
    """檢查套件是否已安裝"""
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False

def main():
    """主程式"""
    print("=== 環境套件自動安裝程式 ===")
    
    # 檢查pip是否可用
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                      check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("❌ pip 不可用，請先安裝 pip")
        return
    
    # 檢查requirements.txt是否存在
    if os.path.exists("requirements.txt"):
        print("找到 requirements.txt，嘗試安裝所有套件...")
        if install_requirements():
            print("🎉 環境安裝完成！")
        else:
            print("❌ 自動安裝失敗，嘗試手動安裝...")
            manual_install()
    else:
        print("未找到 requirements.txt，嘗試手動安裝必要套件...")
        manual_install()

def manual_install():
    """手動安裝必要套件"""
    required_packages = [
        "requests",
        "python-dotenv", 
        "pandas",
        "folium",
        "matplotlib"
    ]
    
    print("\n正在手動安裝必要套件...")
    
    success_count = 0
    for package in required_packages:
        if check_package(package.replace("-", "_")):
            print(f"✅ {package} 已安裝")
            success_count += 1
        else:
            if install_package(package):
                success_count += 1
    
    print(f"\n安裝結果: {success_count}/{len(required_packages)} 個套件安裝成功")
    
    if success_count == len(required_packages):
        print("🎉 所有套件安裝完成！")
        print("\n現在可以執行以下指令:")
        print("python aqi_api.py")
    else:
        print("❌ 部分套件安裝失敗，請手動安裝:")
        for package in required_packages:
            print(f"pip install {package}")

if __name__ == "__main__":
    main()
