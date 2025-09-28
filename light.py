from rpi_ws281x import PixelStrip, Color
import time

LED_COUNT = 5
LED_PIN = 18

strip = PixelStrip(LED_COUNT, LED_PIN, freq_hz=800000, dma=10, invert=False, channel=0)
strip.begin()

# スタート前に全消灯
for i in range(LED_COUNT):
    strip.setPixelColor(i, Color(0, 0, 0))
strip.show()
time.sleep(0.1)

# 1個ずつ順番に光らせる
for i in range(LED_COUNT):
    strip.setPixelColor(i, Color(0, 255, 0))
    strip.show()
    time.sleep(0.5)
    strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()
    time.sleep(0.1)

