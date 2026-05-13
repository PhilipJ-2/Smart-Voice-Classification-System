#include "Arduino_GigaDisplay_GFX.h"

// ============================================================
// SMART MIC PRESENTATION SIMULATION
// No microphone needed.
// Cycles LOW -> MID -> HIGH every 15 seconds.
// A1 outputs tone to TDA2822 speaker amp.
// D2/D3/D4 control LEDs/filter proof.
// ============================================================

GigaDisplay_GFX display;

// ---------------- Pins ----------------
#define SPEAKER_PIN A1

#define LOW_PIN   2
#define MID_PIN   3
#define HIGH_PIN  4

// ---------------- Timing ----------------
const unsigned long MODE_TIME_MS = 15000;

// ---------------- Tone frequencies ----------------
const int LOW_TONE_FREQ  = 400;
const int MID_TONE_FREQ  = 900;
const int HIGH_TONE_FREQ = 1500;

// ---------------- UI Layout ----------------
const int BOX_FREQ_X = 20;
const int BOX_FREQ_Y = 55;
const int BOX_FREQ_W = 300;
const int BOX_FREQ_H = 95;

const int BOX_CLASS_X = 340;
const int BOX_CLASS_Y = 55;
const int BOX_CLASS_W = 220;
const int BOX_CLASS_H = 95;

const int BOX_MODE_X = 580;
const int BOX_MODE_Y = 55;
const int BOX_MODE_W = 200;
const int BOX_MODE_H = 95;

const int BOX_A0_X = 20;
const int BOX_A0_Y = 170;
const int BOX_A0_W = 370;
const int BOX_A0_H = 110;

const int BOX_A1_X = 410;
const int BOX_A1_Y = 170;
const int BOX_A1_W = 370;
const int BOX_A1_H = 110;

const int BOX_WAVE_X = 20;
const int BOX_WAVE_Y = 300;
const int BOX_WAVE_W = 760;
const int BOX_WAVE_H = 150;

const int GRAPH_X = 35;
const int GRAPH_Y = 325;
const int GRAPH_W = 730;
const int GRAPH_H = 95;
const int GRAPH_CENTER_Y = GRAPH_Y + GRAPH_H / 2;

// ---------------- Colors ----------------
const uint16_t C_BG      = 0x0000;
const uint16_t C_WHITE   = 0xFFFF;
const uint16_t C_GREEN   = 0x07E0;
const uint16_t C_CYAN    = 0x07FF;
const uint16_t C_YELLOW  = 0xFFE0;
const uint16_t C_MAGENTA = 0xF81F;
const uint16_t C_RED     = 0xF800;
const uint16_t C_GRID    = 0x2104;
const uint16_t C_CENTER  = 0x7BEF;

int waveformBuffer[GRAPH_W];

// ============================================================
// Utility
// ============================================================
uint16_t classColor(const String &cls) {
  if (cls == "LOW") return C_CYAN;
  if (cls == "MID") return C_YELLOW;
  return C_MAGENTA;
}

int toneForClass(const String &cls) {
  if (cls == "LOW") return LOW_TONE_FREQ;
  if (cls == "MID") return MID_TONE_FREQ;
  return HIGH_TONE_FREQ;
}

double freqForClass(const String &cls) {
  if (cls == "LOW") return random(120, 240);
  if (cls == "MID") return random(360, 620);
  return random(820, 1200);
}

int simulatedADCForClass(const String &cls) {
  if (cls == "LOW") return random(1920, 2020);
  if (cls == "MID") return random(2020, 2120);
  return random(2120, 2240);
}

// ============================================================
// Filter / LED Control
// ============================================================
void setFilter(const String &cls) {
  digitalWrite(LOW_PIN, LOW);
  digitalWrite(MID_PIN, LOW);
  digitalWrite(HIGH_PIN, LOW);

  if (cls == "LOW") {
    digitalWrite(LOW_PIN, HIGH);
  }
  else if (cls == "MID") {
    digitalWrite(MID_PIN, HIGH);
  }
  else {
    digitalWrite(HIGH_PIN, HIGH);
  }
}

// ============================================================
// Tone Output
// ============================================================
void playToneChunk(int freq, int duration_ms) {
  int period = 1000000 / freq;
  long cycles = (long)freq * duration_ms / 1000;

  for (long i = 0; i < cycles; i++) {
    digitalWrite(SPEAKER_PIN, HIGH);
    delayMicroseconds(period / 3);

    digitalWrite(SPEAKER_PIN, LOW);
    delayMicroseconds(period / 3);

    digitalWrite(SPEAKER_PIN, HIGH);
    delayMicroseconds(period / 3);
  }
}

// ============================================================
// Display Helpers
// ============================================================
void drawFrame(int x, int y, int w, int h) {
  display.drawRect(x, y, w, h, C_WHITE);
}

void drawTitleText(int x, int y, const char *txt) {
  display.setTextColor(C_WHITE);
  display.setTextSize(2);
  display.setCursor(x, y);
  display.println(txt);
}

void drawStaticDashboard() {
  display.fillScreen(C_BG);

  display.setTextColor(C_WHITE);
  display.setTextSize(3);
  display.setCursor(20, 12);
  display.println("SMART MIC");

  drawFrame(BOX_FREQ_X, BOX_FREQ_Y, BOX_FREQ_W, BOX_FREQ_H);
  drawFrame(BOX_CLASS_X, BOX_CLASS_Y, BOX_CLASS_W, BOX_CLASS_H);
  drawFrame(BOX_MODE_X, BOX_MODE_Y, BOX_MODE_W, BOX_MODE_H);

  drawFrame(BOX_A0_X, BOX_A0_Y, BOX_A0_W, BOX_A0_H);
  drawFrame(BOX_A1_X, BOX_A1_Y, BOX_A1_W, BOX_A1_H);

  drawFrame(BOX_WAVE_X, BOX_WAVE_Y, BOX_WAVE_W, BOX_WAVE_H);

  drawTitleText(30, 68, "FREQUENCY");
  drawTitleText(350, 68, "VOICE CLASS");
  drawTitleText(590, 68, "FILTER MODE");

  drawTitleText(30, 182, "A0 RAW SIGNAL");
  drawTitleText(420, 182, "A1 FILTERED/SPEAKER");

  drawTitleText(30, 310, "A1 WAVEFORM");
}

void clearDynamicPanels() {
  display.fillRect(30, 95, 280, 45, C_BG);
  display.fillRect(360, 95, 180, 45, C_BG);
  display.fillRect(600, 95, 160, 45, C_BG);

  display.fillRect(30, 208, 350, 60, C_BG);
  display.fillRect(420, 208, 350, 60, C_BG);

  display.fillRect(25, 445, 740, 20, C_BG);
}

void drawFrequencyPanel(double freqHz) {
  display.setTextColor(C_GREEN);
  display.setTextSize(4);
  display.setCursor(35, 102);
  display.print(freqHz, 1);

  display.setTextColor(C_WHITE);
  display.setTextSize(2);
  display.setCursor(220, 116);
  display.print("Hz");
}

void drawClassPanel(const String &cls) {
  uint16_t color = classColor(cls);

  display.fillRect(380, 98, 150, 40, C_BG);
  display.fillRoundRect(385, 100, 140, 36, 8, color);

  display.setTextColor(C_BG);
  display.setTextSize(3);

  if (cls == "LOW") display.setCursor(425, 106);
  else if (cls == "MID") display.setCursor(425, 106);
  else display.setCursor(415, 106);

  display.print(cls);
}

void drawModePanel(const String &cls) {
  display.setTextColor(C_WHITE);
  display.setTextSize(3);
  display.setCursor(615, 104);
  display.print("     ");
  display.setCursor(615, 104);
  display.print(cls);
}

void drawSignalBar(int x, int y, int w, int h, int adcVal, uint16_t color) {
  int fillW = map(adcVal, 0, 4095, 0, w);

  display.drawRect(x, y, w, h, C_WHITE);
  display.fillRect(x + 1, y + 1, w - 2, h - 2, C_BG);
  display.fillRect(x + 1, y + 1, fillW, h - 2, color);

  int centerX = x + w / 2;
  display.drawLine(centerX, y, centerX, y + h, C_RED);
}

void drawSignalPanel(int panelX, int adcVal, float voltage, uint16_t color) {
  display.setTextColor(C_WHITE);
  display.setTextSize(2);

  display.setCursor(panelX, 214);
  display.print("ADC: ");
  display.print(adcVal);

  display.setCursor(panelX, 240);
  display.print("V: ");
  display.print(voltage, 2);

  drawSignalBar(panelX + 140, 214, 185, 18, adcVal, color);
}

void drawStatusLine(const String &txt) {
  display.setTextColor(C_WHITE);
  display.setTextSize(2);
  display.setCursor(25, 445);
  display.print(txt);
}

// ============================================================
// Waveform
// ============================================================
void drawWaveGrid() {
  display.fillRect(GRAPH_X + 1, GRAPH_Y + 1, GRAPH_W - 2, GRAPH_H - 2, C_BG);

  for (int x = GRAPH_X; x <= GRAPH_X + GRAPH_W; x += 73) {
    display.drawLine(x, GRAPH_Y, x, GRAPH_Y + GRAPH_H, C_GRID);
  }

  for (int y = GRAPH_Y + 10; y < GRAPH_Y + GRAPH_H; y += 10) {
    display.drawLine(GRAPH_X, y, GRAPH_X + GRAPH_W, y, C_GRID);
  }

  display.drawLine(GRAPH_X, GRAPH_CENTER_Y, GRAPH_X + GRAPH_W, GRAPH_CENTER_Y, C_CENTER);
}

void updateSimulatedWaveform(const String &cls, int step) {
  int amp;

  if (cls == "LOW") amp = 14;
  else if (cls == "MID") amp = 24;
  else amp = 34;

  for (int i = 0; i < GRAPH_W - 1; i++) {
    waveformBuffer[i] = waveformBuffer[i + 1];
  }

  float speed;
  if (cls == "LOW") speed = 0.08;
  else if (cls == "MID") speed = 0.16;
  else speed = 0.28;

  int y = GRAPH_CENTER_Y + (int)(amp * sin(step * speed));

  if (y < GRAPH_Y + 2) y = GRAPH_Y + 2;
  if (y > GRAPH_Y + GRAPH_H - 2) y = GRAPH_Y + GRAPH_H - 2;

  waveformBuffer[GRAPH_W - 1] = y;
}

void drawWaveform() {
  for (int i = 1; i < GRAPH_W; i++) {
    display.drawLine(GRAPH_X + i - 1, waveformBuffer[i - 1],
                     GRAPH_X + i, waveformBuffer[i],
                     C_GREEN);
  }
}

// ============================================================
// Run one mode for 15 seconds
// ============================================================
void runMode(const String &cls) {
  setFilter(cls);

  int toneFreq = toneForClass(cls);
  unsigned long startTime = millis();
  int step = 0;

  while (millis() - startTime < MODE_TIME_MS) {
    double displayFreq = freqForClass(cls);
    int adcA0 = simulatedADCForClass(cls);
    int adcA1 = simulatedADCForClass(cls) + random(10, 35);

    float voltageA0 = (adcA0 * 3.3f) / 4095.0f;
    float voltageA1 = (adcA1 * 3.3f) / 4095.0f;

    clearDynamicPanels();

    drawFrequencyPanel(displayFreq);
    drawClassPanel(cls);
    drawModePanel(cls);

    drawSignalPanel(35, adcA0, voltageA0, C_GREEN);
    drawSignalPanel(425, adcA1, voltageA1, C_YELLOW);

    drawWaveGrid();

    for (int i = 0; i < 15; i++) {
      updateSimulatedWaveform(cls, step++);
    }

    drawWaveform();

    drawStatusLine("");

    playToneChunk(toneFreq, 120);
  }
}

// ============================================================
// Setup
// ============================================================
void setup() {
  pinMode(SPEAKER_PIN, OUTPUT);

  pinMode(LOW_PIN, OUTPUT);
  pinMode(MID_PIN, OUTPUT);
  pinMode(HIGH_PIN, OUTPUT);

  digitalWrite(LOW_PIN, LOW);
  digitalWrite(MID_PIN, LOW);
  digitalWrite(HIGH_PIN, LOW);

  randomSeed(analogRead(A0));

  display.begin();
  display.setRotation(1);

  drawStaticDashboard();

  for (int i = 0; i < GRAPH_W; i++) {
    waveformBuffer[i] = GRAPH_CENTER_Y;
  }
}

// ============================================================
// Loop
// ============================================================
void loop() {
  runMode("LOW");
  runMode("MID");
  runMode("HIGH");
}
