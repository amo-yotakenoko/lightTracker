#include <Adafruit_NeoPixel.h>

#define LED_PIN 6
#define LED_COUNT 30

#define use_color 2
#define pattern_loop 5
#define PATTERN_DELAY 500

Adafruit_NeoPixel strip(LED_COUNT, LED_PIN, NEO_GRB + NEO_KHZ800);
const uint32_t colors[] = {strip.Color(200, 0, 0), strip.Color(0, 200, 0), strip.Color(0, 0, 200)};

// 'coun
void setup()
{
    strip.begin();
    strip.show(); // 全LED消灯

    Serial.begin(115200);
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
void loop()
{
    // setPixelAll(strip.Color(255, 0, 0));
    while (1)
    {
        if ((count % 10) == 0)
        {
            setPixelAll(colors[2]);
            delay(PATTERN_DELAY * 5);
            count = 0;
        }

        for (size_t i = 0; i < LED_COUNT; i++)
        {
            strip.setPixelColor(i, colors[(i / ((int)pow(use_color, (count % pattern_loop)))) % use_color]);

            // strip.setPixelColor(i, (count % 30) == i ? colors[1] : colors[0]);
        }
        strip.show();
        delay(PATTERN_DELAY);

        count += 1;
    }
}
