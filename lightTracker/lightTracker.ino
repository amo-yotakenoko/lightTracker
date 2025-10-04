#include <Adafruit_NeoPixel.h>

#define LED_PIN 6
#define LED_COUNT 30

Adafruit_NeoPixel strip(LED_COUNT, LED_PIN, NEO_GRB + NEO_KHZ800);

void setup()
{

  strip.begin();
  strip.show(); // 全LED消灯

  lightTest();

  Serial.begin(115200);
}

void lightTest()
{
  for (int i = 0; i < LED_COUNT; i++)
  {
    strip.setPixelColor(i, strip.Color(255, 0, 0));
    strip.show();
    delay(10);

    strip.setPixelColor(i, strip.Color(0, 0, 0));
    strip.show();
  }

  for (int i = 0; i < LED_COUNT; i++)
  {
    strip.setPixelColor(i, strip.Color(0, 255, 0));
    strip.show();
    delay(10);

    strip.setPixelColor(i, strip.Color(0, 0, 0));
    strip.show();
  }

  for (int i = 0; i < LED_COUNT; i++)
  {
    strip.setPixelColor(i, strip.Color(0, 0, 255));
    strip.show();
    delay(10);

    strip.setPixelColor(i, strip.Color(0, 0, 0));
    strip.show();
  }
}

void clearStrip()
{
  for (int i = 0; i < LED_COUNT; i++)
  {
    strip.setPixelColor(i, strip.Color(0, 0, 0));
  }
}

void loop()
{
  // データを受信する
  if (Serial.available() >= 4)
  {
    int ledIndex = Serial.read(); // 1バイト目: LED番号

    int r = Serial.read(); // 1バイト目: LED番号
    int g = Serial.read(); // 1バイト目: LED番号
    int b = Serial.read(); // 1バイト目: LED番号

    if (ledIndex == 255) // led_clear
    {
      clearStrip();
      strip.show();
    }
    else if (ledIndex == 254) // led_show
    {
      strip.show();
      clearStrip();
    }
    else
    {
      strip.setPixelColor(ledIndex, strip.Color(r, g, b));
      // strip.show();
    }
  }
}
