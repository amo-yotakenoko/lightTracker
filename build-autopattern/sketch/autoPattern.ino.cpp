#include <Arduino.h>
#line 1 "C:\\Users\\taken\\projects\\lightTracker\\autoPattern\\autoPattern.ino"
#include <Adafruit_NeoPixel.h>

#define LED_PIN 6
#define LED_COUNT 30
#define PATTERN_DELAY 500

Adafruit_NeoPixel strip(LED_COUNT, LED_PIN, NEO_GRB + NEO_KHZ800);
const uint32_t colors[] = {strip.Color(200, 0, 0), strip.Color(0, 200, 0), strip.Color(0, 0, 255)};
#line 9 "C:\\Users\\taken\\projects\\lightTracker\\autoPattern\\autoPattern.ino"
void setup();
#line 18 "C:\\Users\\taken\\projects\\lightTracker\\autoPattern\\autoPattern.ino"
void setPixelAll(uint32_t color);
#line 29 "C:\\Users\\taken\\projects\\lightTracker\\autoPattern\\autoPattern.ino"
void loop();
#line 9 "C:\\Users\\taken\\projects\\lightTracker\\autoPattern\\autoPattern.ino"
void setup()
{

    strip.begin();
    strip.show(); // 全LED消灯

    //   Serial.begin(115200);
}

void setPixelAll(uint32_t color)
{
    for (int i = 0; i < strip.numPixels(); i++)
    {
        strip.setPixelColor(i, color);
    }
    strip.show();
}

int count = 0;
int pattern_loop = 4;
void loop()
{
    // setPixelAll(strip.Color(255, 0, 0));
    setPixelAll(colors[2]);
    delay(PATTERN_DELAY * 2 * 3);
    count = 0;
    for (size_t j = 0; j < pattern_loop * 10; j++)
    {

        for (size_t i = 0; i < LED_COUNT; i++)
        {
            strip.setPixelColor(i, colors[(i / ((int)pow(3, (count % pattern_loop)))) % 3]);
            // strip.setPixelColor(i, colors[0]);
        }
        strip.show();
        count += 1;
        delay(PATTERN_DELAY);
    }
}

