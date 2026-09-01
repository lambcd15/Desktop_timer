#include <FastLED.h>

#define DATA_PIN    11
#define NUM_LEDS    12
CRGB leds[NUM_LEDS];

// Original sensor mode variables
CRGB colourList[] = { CRGB::Red, CRGB::Green };
const int numberOfColours = sizeof(colourList) / sizeof(colourList[0]);
int colourIndex = 0;

// Control modes
enum Mode {
  SENSOR_MODE,
  STATIC_COLOR,
  EFFECT_MODE
};

Mode currentMode = SENSOR_MODE;
CRGB staticColor = CRGB::Black;

// Effect system
enum EffectType {
  EFFECT_NONE,
  EFFECT_BREATHING,
  EFFECT_SUNRISE,
  EFFECT_SUNSET,
  EFFECT_LAVA_NOISE,
  EFFECT_HEARTBEAT,
  EFFECT_ROTATING_GRADIENT,
  EFFECT_COMET,
  EFFECT_CANDLE,
  EFFECT_OCEAN,
  EFFECT_FOREST,
  EFFECT_FIRE,
  EFFECT_AURORA,
  EFFECT_PROGRESS_HALO,
  EFFECT_BEAT_PULSE
};

EffectType currentEffect = EFFECT_NONE;
unsigned long effectTimer = 0;
float effectPhase = 0.0;
uint8_t effectSpeed = 128;  // 0-255
uint8_t effectIntensity = 255;  // 0-255
CRGB effectColor = CRGB::White;
uint8_t progressValue = 0;  // 0-100 for progress halo

// Noise variables for lava effect
uint16_t noiseX = 0;
uint16_t noiseY = 0;
uint16_t noiseZ = 0;

// Comet variables
CRGB cometColor = CRGB(255, 0, 255); // 💡 Set any RGB color (e.g., Red, Green, Blue, Purple)
int cometPos = 0;         // Current position of the comet
int cometSize = 2;        // Length of the comet tail
int fadeAmount = 60;      // How fast the tail fades (higher = faster)
int cometSpeed = 100;                  // Delay in ms between frames (lower = faster)

// ---- Direction ----
// +1 = clockwise,  -1 = counter-clockwise
int8_t direction = 1;                 // 🔀 Change this to -1 to reverse direction

// Heartbeat variables
unsigned long lastHeartbeat = 0;
uint8_t heartbeatPhase = 0;

// Beat pulse variables
unsigned long lastBeatPulse = 0;
uint8_t beatIntensity = 0;

// Candle flicker
uint8_t candleFlicker[NUM_LEDS];

// Color palettes
DEFINE_GRADIENT_PALETTE( ocean_gp ) {
  0,   0,  50, 100,    // Deep blue
  64,   0, 100, 150,    // Medium blue
  128,  20, 150, 200,    // Light blue
  192,  50, 200, 255,    // Very light blue
  255, 100, 255, 255     // White-blue
};

DEFINE_GRADIENT_PALETTE( forest_gp ) {
  0,   0,  50,   0,     // Dark green
  64,  20, 100,  20,     // Medium green
  128,  50, 150,  30,     // Light green
  192, 100, 200,  50,     // Yellow-green
  255, 150, 255, 100     // Light yellow
};

DEFINE_GRADIENT_PALETTE( fire_gp ) {
  0,   50,   0,   0,    // Dark red
  64,  150,  20,   0,    // Red
  128,  255,  50,   0,    // Orange
  192,  255, 150,  20,    // Yellow-orange
  255,  255, 255, 100    // Warm white
};

DEFINE_GRADIENT_PALETTE( aurora_gp ) {
  0,   0, 255, 255,     // Cyan
  64,  50, 200, 255,     // Light cyan
  128, 255,  50, 255,     // Magenta
  192, 200,   0, 200,     // Purple
  255,   0, 100, 255     // Blue
};

CRGBPalette16 oceanPalette = ocean_gp;
CRGBPalette16 forestPalette = forest_gp;
CRGBPalette16 firePalette = fire_gp;
CRGBPalette16 auroraPalette = aurora_gp;

void setup() {
  Serial.begin(9600);
  FastLED.addLeds<WS2812B, DATA_PIN, GRB>(leds, NUM_LEDS);
  FastLED.setBrightness(125);
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);

  // Initialize candle flicker array
  for (int i = 0; i < NUM_LEDS; i++) {
    candleFlicker[i] = random8(200, 255);
  }

  // Start with lights off
  fill_solid(leds, NUM_LEDS, CRGB::Black);
  FastLED.show();
}

void setStaticColor(CRGB color) {
  currentMode = STATIC_COLOR;
  staticColor = color;
  currentEffect = EFFECT_NONE;
  fill_solid(leds, NUM_LEDS, color);
  blur1d(leds, NUM_LEDS, 80);  // Heavy blur for diffusion
  FastLED.show();
}

void startEffect(EffectType effect) {
  currentMode = EFFECT_MODE;
  currentEffect = effect;
  effectTimer = millis();
  effectPhase = 0.0;

  // Reset effect-specific variables
  cometPos = 0;
  heartbeatPhase = 0;
  lastHeartbeat = 0;
  lastBeatPulse = 0;
  beatIntensity = 0;
}

// Effect implementations
void updateBreathingEffect() {
  float breath = (sin(effectPhase) + 1.0) / 2.0;  // 0.0 to 1.0
  uint8_t brightness = (uint8_t)(breath * effectIntensity);

  CRGB color = effectColor;
  color.nscale8(brightness);
  fill_solid(leds, NUM_LEDS, color);
  blur1d(leds, NUM_LEDS, 80);
}

void updateSunriseEffect() {
  // Sunrise: Deep red → Orange → Warm white
  uint8_t phase8 = (uint8_t)(effectPhase * 127.5 + 127.5);  // 0-255

  CRGB color;
  if (phase8 < 85) {
    // Deep red to red-orange
    color = CRGB(255, phase8 * 3, 0);
  } else if (phase8 < 170) {
    // Red-orange to orange
    uint8_t progress = (phase8 - 85) * 3;
    color = CRGB(255, 255, progress);
  } else {
    // Orange to warm white
    uint8_t progress = (phase8 - 170) * 3;
    color = CRGB(255, 255, 128 + progress / 2);
  }

  color.nscale8(effectIntensity);
  fill_solid(leds, NUM_LEDS, color);
  blur1d(leds, NUM_LEDS, 80);
}

void updateSunsetEffect() {
  // Sunset: Warm white → Orange → Deep red
  uint8_t phase8 = 255 - (uint8_t)(effectPhase * 127.5 + 127.5);  // Reverse of sunrise

  CRGB color;
  if (phase8 < 85) {
    color = CRGB(255, phase8 * 3, 0);
  } else if (phase8 < 170) {
    uint8_t progress = (phase8 - 85) * 3;
    color = CRGB(255, 255, progress);
  } else {
    uint8_t progress = (phase8 - 170) * 3;
    color = CRGB(255, 255, 128 + progress / 2);
  }

  color.nscale8(effectIntensity);
  fill_solid(leds, NUM_LEDS, color);
  blur1d(leds, NUM_LEDS, 80);
}

void updateLavaNoiseEffect() {
  // Organic color wandering with Perlin noise
  for (int i = 0; i < NUM_LEDS; i++) {
    uint8_t noise = inoise8(noiseX + i * 300, noiseY, noiseZ);
    uint8_t hue = (noise + effectPhase * 10.0f);
    leds[i] = CHSV(hue, 200, effectIntensity);
  }

  // Heavy blur for organic feel
  blur1d(leds, NUM_LEDS, 120);

  // Advance noise coordinates slowly
  noiseX += effectSpeed / 8;
  noiseY += effectSpeed / 12;
  noiseZ += effectSpeed / 16;
}

void updateHeartbeatEffect() {
  unsigned long now = millis();

  // Double beat pattern: beat-beat-pause
  if (now - lastHeartbeat > 1000) {  // 60 BPM
    lastHeartbeat = now;
    heartbeatPhase = 0;
  }

  uint8_t brightness = 0;
  unsigned long elapsed = now - lastHeartbeat;

  if (elapsed < 100) {
    // First beat
    brightness = sin8(map(elapsed, 0, 100, 0, 255));
  } else if (elapsed > 200 && elapsed < 300) {
    // Second beat
    brightness = sin8(map(elapsed - 200, 0, 100, 0, 255));
  }

  brightness = map(brightness, 0, 255, 0, effectIntensity);

  // Warm red color for heartbeat
//  CRGB color = CRGB(255, 50, 20);
  CRGB color = effectColor;
  color.nscale8(brightness);
  fill_solid(leds, NUM_LEDS, color);
  blur1d(leds, NUM_LEDS, 80);
}


uint16_t phase16 = 0;
uint8_t rotationSpeed = 15;

void updateRotatingGradientEffect() {
  if (direction == 1)
  {
    phase16 -= rotationSpeed;
  }else if (direction == -1) {
    phase16 += rotationSpeed;
  }
  
  uint8_t baseHue = phase16 >> 8;

  for (int i = 0; i < NUM_LEDS; i++) {
    // Use 255 instead of 256 to keep within 8-bit range cleanly
    uint8_t hue = baseHue + (uint8_t)((i * 255u) / NUM_LEDS);
    leds[i] = CHSV(hue, 200, effectIntensity);
  }
  blur1d(leds, NUM_LEDS, 100);
}


//void updateRotatingGradientEffect() {
//  uint8_t step = (NUM_LEDS > 1) ? (255u / (NUM_LEDS - 1)) : 0;
//  for (int i = 0; i < NUM_LEDS; i++) {
//    uint8_t hue = (effectPhase * 10) + (uint8_t(i * 256) / NUM_LEDS);
//    leds[i] = CHSV(hue, 200, effectIntensity);
//  }
//  blur1d(leds, NUM_LEDS, 100);  // Heavy blur for smooth gradient
//}

void updateCometEffect() {
  // Fade all LEDs slightly to create the trailing effect
  for (int i = 0; i < NUM_LEDS; i++) {
    leds[i].fadeToBlackBy(fadeAmount);
  }

  // Draw the comet head
  leds[cometPos] = effectColor;

  // Draw the tail
  for (int i = 1; i < cometSize; i++) {
    int pos = (cometPos + NUM_LEDS - (i * direction + NUM_LEDS)) % NUM_LEDS;
    // Dim the tail by scaling brightness
     uint8_t scale = 255 - ((uint16_t)i * 255) / (cometSize + 1);
    CRGB tail( (uint16_t)cometColor.r * scale / 255,
               (uint16_t)cometColor.g * scale / 255,
               (uint16_t)cometColor.b * scale / 255 );
    leds[pos] += tail; // additive so it blends nicely
  }

  FastLED.show();
  delay(cometSpeed); // Adjust speed

  // Move the comet forward
  cometPos = (cometPos + direction + NUM_LEDS) % NUM_LEDS;
  if (cometPos >= NUM_LEDS) cometPos = 0;
}

void updateCandleEffect() {
//  CRGB baseColor = CRGB(255, 180, 100);  // Warm white/orange
  CRGB baseColor = effectColor;  // Warm white/orange

  for (int i = 0; i < NUM_LEDS; i++) {
    // Gentle random variations
    if (random8() < 30) {  // 30/255 chance per frame
      candleFlicker[i] = random8(180, 255);
    }

    CRGB color = baseColor;
    color.nscale8(candleFlicker[i]);
    color.nscale8(effectIntensity);
    leds[i] = color;
  }

  blur1d(leds, NUM_LEDS, 60);  // Light blur for organic feel
}

void updateMoodEffect(CRGBPalette16 palette) {
  for (int i = 0; i < NUM_LEDS; i++) {
    uint8_t colorIndex = uint8_t(effectPhase * 2.0f) + uint8_t(i * 8);
    leds[i] = ColorFromPalette(palette, colorIndex, effectIntensity, LINEARBLEND);
  }
  blur1d(leds, NUM_LEDS, 90);
}

void updateProgressHaloEffect() {
  // Clear all LEDs
  fill_solid(leds, NUM_LEDS, CRGB::Black);

  // Calculate how many LEDs to fill based on progress (0-100)
  int ledsToFill = map(progressValue, 0, 100, 0, NUM_LEDS);

  for (int i = 0; i < ledsToFill; i++) {
    leds[i] = effectColor;
    leds[i].nscale8(effectIntensity);
  }

  // Heavy blur for smooth wedge appearance
  blur1d(leds, NUM_LEDS, 100);
}

void updateBeatPulseEffect() {
  unsigned long now = millis();

  // Trigger beat pulse every 500ms (120 BPM)
  if (now - lastBeatPulse > 500) {
    lastBeatPulse = now;
    beatIntensity = effectIntensity;
  }

  // Fade out the beat
  if (beatIntensity > 0) {
    beatIntensity = max(0, beatIntensity - 5);
  }

  CRGB color = effectColor;
  color.nscale8(beatIntensity);
  fill_solid(leds, NUM_LEDS, color);
  blur1d(leds, NUM_LEDS, 80);
}

void updateEffects() {
  if (currentMode != EFFECT_MODE || currentEffect == EFFECT_NONE) {
    return;
  }

  // Update effect phase
  unsigned long now = millis();
  float deltaTime = (now - effectTimer) / 1000.0;
  effectPhase += deltaTime * (effectSpeed / 128.0);
  effectTimer = now;

  // Keep phase in reasonable range
  if (effectPhase > TWO_PI) effectPhase -= TWO_PI;

  // Update the current effect
  switch (currentEffect) {
    case EFFECT_BREATHING:
      updateBreathingEffect();
      break;
    case EFFECT_SUNRISE:
      updateSunriseEffect();
      break;
    case EFFECT_SUNSET:
      updateSunsetEffect();
      break;
    case EFFECT_LAVA_NOISE:
      updateLavaNoiseEffect();
      break;
    case EFFECT_HEARTBEAT:
      updateHeartbeatEffect();
      break;
    case EFFECT_ROTATING_GRADIENT:
      updateRotatingGradientEffect();
      break;
    case EFFECT_COMET:
      updateCometEffect();
      break;
    case EFFECT_CANDLE:
      updateCandleEffect();
      break;
    case EFFECT_OCEAN:
      updateMoodEffect(oceanPalette);
      break;
    case EFFECT_FOREST:
      updateMoodEffect(forestPalette);
      break;
    case EFFECT_FIRE:
      updateMoodEffect(firePalette);
      break;
    case EFFECT_AURORA:
      updateMoodEffect(auroraPalette);
      break;
    case EFFECT_PROGRESS_HALO:
      updateProgressHaloEffect();
      break;
    case EFFECT_BEAT_PULSE:
      updateBeatPulseEffect();
      break;
  }

  FastLED.show();
}

void handleSerialCommand() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    if (command == "RED") {
      setStaticColor(CRGB::Red);
      Serial.println("OK:RED");
    }
    else if (command == "GREEN") {
      setStaticColor(CRGB::Green);
      Serial.println("OK:GREEN");
    }
    else if (command == "OFF") {
      setStaticColor(CRGB::Black);
      Serial.println("OK:OFF");
    }
    else if (command.startsWith("RGB:")) {
      // Parse RGB command format: "RGB:255,128,64"
      String rgbValues = command.substring(4);
      int firstComma = rgbValues.indexOf(',');
      int secondComma = rgbValues.indexOf(',', firstComma + 1);

      if (firstComma > 0 && secondComma > firstComma) {
        int r = rgbValues.substring(0, firstComma).toInt();
        int g = rgbValues.substring(firstComma + 1, secondComma).toInt();
        int b = rgbValues.substring(secondComma + 1).toInt();

        r = constrain(r, 0, 255);
        g = constrain(g, 0, 255);
        b = constrain(b, 0, 255);

        cometColor = CRGB(r, g, b);

        setStaticColor(CRGB(r, g, b));
        Serial.print("OK:RGB:");
        Serial.print(r);
        Serial.print(",");
        Serial.print(g);
        Serial.print(",");
        Serial.println(b);
      } else {
        Serial.println("ERROR:INVALID_RGB_FORMAT");
      }
    }
    // Effect commands
    else if (command == "EFFECT:BREATHING") {
      startEffect(EFFECT_BREATHING);
      Serial.println("OK:EFFECT:BREATHING");
    }
//    else if (command == "EFFECT:SUNRISE") {
//      startEffect(EFFECT_SUNRISE);
//      Serial.println("OK:EFFECT:SUNRISE");
//    }
//    else if (command == "EFFECT:SUNSET") {
//      startEffect(EFFECT_SUNSET);
//      Serial.println("OK:EFFECT:SUNSET");
//    }
//    else if (command == "EFFECT:LAVA") {
//      startEffect(EFFECT_LAVA_NOISE);
//      Serial.println("OK:EFFECT:LAVA");
//    }
    else if (command == "EFFECT:HEARTBEAT") {
      startEffect(EFFECT_HEARTBEAT);
      Serial.println("OK:EFFECT:HEARTBEAT");
    }
    else if (command == "EFFECT:GRADIENT") {
      startEffect(EFFECT_ROTATING_GRADIENT);
      Serial.println("OK:EFFECT:GRADIENT");
    }
    else if (command == "EFFECT:COMET+") {
      direction = 1;
      startEffect(EFFECT_COMET);
      Serial.println("OK:EFFECT:COMET+");
    }
    else if (command == "EFFECT:COMET-") {
      direction = -1;
      startEffect(EFFECT_COMET);
      Serial.println("OK:EFFECT:COMET-");
    }
    else if (command == "EFFECT:CANDLE") {
      startEffect(EFFECT_CANDLE);
      Serial.println("OK:EFFECT:CANDLE");
    }
//    else if (command == "EFFECT:OCEAN") {
//      startEffect(EFFECT_OCEAN);
//      Serial.println("OK:EFFECT:OCEAN");
//    }
//    else if (command == "EFFECT:FOREST") {
//      startEffect(EFFECT_FOREST);
//      Serial.println("OK:EFFECT:FOREST");
//    }
//    else if (command == "EFFECT:FIRE") {
//      startEffect(EFFECT_FIRE);
//      Serial.println("OK:EFFECT:FIRE");
//    }
//    else if (command == "EFFECT:AURORA") {
//      startEffect(EFFECT_AURORA);
//      Serial.println("OK:EFFECT:AURORA");
//    }
//    else if (command == "EFFECT:PROGRESS") {
//      startEffect(EFFECT_PROGRESS_HALO);
//      Serial.println("OK:EFFECT:PROGRESS");
//    }
    else if (command == "EFFECT:BEAT") {
      startEffect(EFFECT_BEAT_PULSE);
      Serial.println("OK:EFFECT:BEAT");
    }
    // Effect parameters
    else if (command.startsWith("SPEED:")) {
      effectSpeed = constrain(command.substring(6).toInt(), 0, 255);
      Serial.print("OK:SPEED:");
      Serial.println(effectSpeed);
    }
    else if (command.startsWith("INTENSITY:")) {
      effectIntensity = constrain(command.substring(10).toInt(), 0, 255);
      FastLED.setBrightness(effectIntensity);
      Serial.print("OK:INTENSITY:");
      Serial.println(effectIntensity);
    }
    else if (command.startsWith("EFFECT_COLOR:")) {
      // Parse RGB for effect color: "EFFECT_COLOR:255,128,64"
      String rgbValues = command.substring(13);
      int firstComma = rgbValues.indexOf(',');
      int secondComma = rgbValues.indexOf(',', firstComma + 1);

      if (firstComma > 0 && secondComma > firstComma) {
        int r = rgbValues.substring(0, firstComma).toInt();
        int g = rgbValues.substring(firstComma + 1, secondComma).toInt();
        int b = rgbValues.substring(secondComma + 1).toInt();

        r = constrain(r, 0, 255);
        g = constrain(g, 0, 255);
        b = constrain(b, 0, 255);

        effectColor = CRGB(r, g, b);
        Serial.print("OK:EFFECT_COLOR:");
        Serial.print(r);
        Serial.print(",");
        Serial.print(g);
        Serial.print(",");
        Serial.println(b);
      } else {
        Serial.println("ERROR:INVALID_EFFECT_COLOR_FORMAT");
      }
    }
    else if (command.startsWith("PROGRESS:")) {
      progressValue = constrain(command.substring(9).toInt(), 0, 100);
      Serial.print("OK:PROGRESS:");
      Serial.println(progressValue);
    }
    else if (command == "SENSOR_MODE") {
      currentMode = SENSOR_MODE;
      currentEffect = EFFECT_NONE;
      Serial.println("OK:SENSOR_MODE");
    }
    else if (command == "EFFECT_NONE") {
//      currentMode = SENSOR_MODE;
      currentEffect = EFFECT_NONE;
      Serial.println("OK:EFFECT_NONE");
    }
    else if (command == "STATUS") {
      if (currentMode == SENSOR_MODE) {
        Serial.println("STATUS:SENSOR_MODE");
      } else if (currentMode == STATIC_COLOR) {
        if (staticColor == CRGB::Red) Serial.println("STATUS:RED");
        else if (staticColor == CRGB::Green) Serial.println("STATUS:GREEN");
        else if (staticColor == CRGB::Black) Serial.println("STATUS:OFF");
        else Serial.println("STATUS:CUSTOM_COLOR");
      } else if (currentEffect == EFFECT_NONE) {
        Serial.print("STATUS:EFFECT:");
        Serial.println(currentEffect);
      }
    }
    else {
      Serial.println("ERROR:UNKNOWN_COMMAND");
    }
  }
}

void loop() {
  // Always check for serial commands
  handleSerialCommand();

  // Handle different modes
  if (currentMode == SENSOR_MODE) {
    // Original sensor behavior
    int sensorValue = analogRead(A0);
    if (sensorValue > 350) {
      fill_solid(leds, NUM_LEDS, colourList[colourIndex]);
      FastLED.show();
      delay(150);
      colourIndex = (colourIndex + 1) % numberOfColours; // wrap
    }
  } else if (currentMode == EFFECT_MODE) {
    // Update and display effects
    updateEffects();
  }
  // STATIC_COLOR mode doesn't need updates - color is set once

  delay(1); // stability
}
