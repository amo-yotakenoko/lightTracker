#include <Adafruit_NeoPixel.h>
#include "signPattern.h"

#define LED_PIN 6
#define LED_COUNT 6

#define use_color 2
#define pattern_loop 5
#define PATTERN_DELAY 50
Adafruit_NeoPixel strip(LED_COUNT, LED_PIN, NEO_GRB + NEO_KHZ800);
int lightPower = 255;
const uint32_t colors[] = {strip.Color(lightPower, 0, 0), strip.Color(0, lightPower, 0), strip.Color(0, 0, lightPower)};

const uint8_t lightPattern[LIGHT_PATTERN_LENGTH][LIGHT_PATTERN_TIME_LENGTH] = LIGHT_PATTERN;

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
    int t = 0;
    while (1)
    {

        for (size_t i = 0; i < LED_COUNT; i += 1)
        {
            strip.setPixelColor(i, colors[lightPattern[i][t % LIGHT_PATTERN_TIME_LENGTH]]);
            strip.show();
            delay(PATTERN_DELAY);
            // strip.setPixelColor(i, (count % 30) == i ? colors[1] : colors[0]);
        }

        t++;
    }
}
