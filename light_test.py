import time
import os
from dotenv import load_dotenv
import marker_update
import pyautogui

# .envファイルから環境変数を読み込む（PORTなどを設定）
load_dotenv()

# LEDの数
LED_COUNT = 30
# 点灯させる色（青っぽい白）
COLOR_ON = (15, 15, 55)
# アニメーションの速度（秒）
SPEED = 0.01

def main():
    """
    pyautoguiを使用してマウスの左右の位置に合わせてLEDを点灯させるテストプログラム。
    """
    try:
        # シリアルポートの初期化
        marker_update.marker_initialize()
        print(f"{LED_COUNT}個のLEDをマウスの位置に合わせて点灯させます。Ctrl+Cで終了します。")
        time.sleep(2)  # Arduinoの初期化待ち

        # 画面の幅を取得
        screen_width, _ = pyautogui.size()

        while True:
            # マウスのX座標を取得
            mouse_x, _ = pyautogui.position()

            # マウスのX座標をLEDの位置にマッピング
            led_index = int((mouse_x / screen_width) * LED_COUNT)

            # LEDが範囲内に収まるように調整
            if led_index < 0:
                led_index = 0
            if led_index >= LED_COUNT:
                led_index = LED_COUNT - 1

        
            # 対応するLEDを点灯
            marker_update.led_set(led_index, COLOR_ON)
            marker_update.led_show()  # LEDに反映

            time.sleep(SPEED)

    except KeyboardInterrupt:
        print("\nプログラムを終了します。")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        print("PORTが.envファイルで正しく設定されているか確認してください。")
    finally:
        # 終了時にすべてのLEDを消灯
        if marker_update.arduino and marker_update.arduino.is_open:
            print("全LEDを消灯します。")
            marker_update.led_clear()
            marker_update.led_show()

if __name__ == "__main__":
    main()