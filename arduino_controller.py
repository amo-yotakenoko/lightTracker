import serial
import os

arduino = None

def initialize():
    """Arduinoとのシリアル通信を初期化する"""
    global arduino
    port = os.getenv("PORT")
    if port is None:
        raise ValueError("環境変数 'PORT' が設定されていません。")
    try:
        arduino = serial.Serial(port, 115200, timeout=1)
    except Exception as e:
        print("接続失敗")

def led_set(index: int, color: tuple[int, int, int]):
    """指定したLEDの色を送信"""
    global arduino
    if arduino is None:
        return
    # print(f"led_set {index} {color}")
    r, g, b = color
    arduino.write(bytes([index, b, g, r]))

def led_show():
    """LEDの色の変更を確定させる"""
    global arduino
    if arduino is None:
        return
    arduino.write(bytes([254, 0, 0, 0]))

def led_clear():
    """すべてのLEDを消灯する"""
    global arduino
    if arduino is None:
        return
    arduino.write(bytes([255, 0, 0, 0]))
