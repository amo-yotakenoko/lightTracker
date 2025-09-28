import serial
import time

# Arduino の COM ポートを指定
arduino = serial.Serial('COM4', 115200, timeout=1)
time.sleep(2)  # Arduino リセット待ち

def set_led(index):
    """1 LEDの色を送信"""
    arduino.write(bytes([index]))





while True:
		for i in range(30):
			print(i)
			set_led(i)  # 緑色で点灯
