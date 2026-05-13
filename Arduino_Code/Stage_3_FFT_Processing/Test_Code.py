#include "Arduino_GigaDisplay_GFX.h"
#include <arduinoFFT.h>

// ============================================================
// SMART MIC - TRANSISTOR SWITCH FILTER VERSION (FIXED)
// LOW is default, switches to MID/HIGH only when frequency rises
// ============================================================

GigaDisplay_GFX display;

// ---------------- Pins ----------------
#define PRE_FILTER_PIN   A0   // LM358 output before filter
#define POST_FILTER_PIN  A1   // Filter node after switched resistor network

#define LOW_PIN          2    // Q1 base via R10
#define MID_PIN          3    // Q2 base via R11
#define HIGH_PIN         4    // Q3 base via R12

// ---------------- FFT ----------------
#define FFT_SAMPLES 128
#define SAMPLING_FREQUENCY 8000

double vReal[FFT_SAMPLES];
double vImag[FFT_SAMPLES];
ArduinoFFT<double> FFT = ArduinoFFT<double>(vReal, vImag, FFT_SAMPLES, SAMPLING_FREQUENCY);

// ---------------- Thresholds ----------------
// LOW stays default unless frequency clearly rises
const double VALID_MIN_FREQ   = 80.0;
const double VALID_MAX_FREQ   = 1200.0;

const double LOW_TO_MID_FREQ  = 300.0;
const double MID_TO_HIGH_FREQ = 600.0;

const double MID_TO_LOW_FREQ  = 240.0;
const double HIGH_TO_MID_FREQ = 520.0;

// ---------------- Smoothing ----------------
const double FREQ_ALPHA = 0.12;
const double ADC_ALPHA  = 0.18;
const float  WAVE_SCALE = 0.045f;

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

const int BOX_PRE_X = 20;
const int BOX_PRE_Y = 170;
const int BOX_PRE_W = 370;
const int BOX_PRE_H = 110;

const int BOX_POST_X = 410;
const int BOX_POST_Y = 170;
const int BOX_POST_W = 370;
const int BOX_POST_H = 110;

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

// ---------------- State ----------------
String currentClass = "LOW";
double smoothedFrequency = 0.0;
bool freqInitialized = false;

double smoothedPreADC = 0.0;
double smoothedPostADC = 0.0;
bool preADCInitialized = false;
bool postADCInitialized = false;

int waveformBuffer[GRAPH_W];

// ============================================================
// Utility
// ============================================================
double smoothValue(double oldVal, double newVal, double alpha, bool &initialized) {
  if (!initialized) {
    initialized = true;
    return newVal;
  }
  return (1.0 - alpha) * oldVal + alpha * newVal;
}

uint16_t classColor(const String &cls) {
  if (cls == "LOW") return C_CYAN;
  if (cls == "MID") return C_YELLOW;
  return C_MAGENTA;
}

// ============================================================
// Classification
// ============================================================
String classifyVoiceStable(double freq) {
  // Ignore garbage readings completely
  if (freq < VALID_MIN_FREQ || freq > VALID_MAX_FREQ) {
    return currentClass;
  }

  // LOW is default until signal clearly rises
  if (currentClass == "LOW") {
    if (freq >= MID_TO_HIGH_FREQ) currentClass = "HIGH";
    else if (freq >= LOW_TO_MID_FREQ) currentClass = "MID";
    else currentClass = "LOW";
  }
  else if (currentClass == "MID") {
    if (freq >= MID_TO_HIGH_FREQ) currentClass = "HIGH";
    else if (freq < MID_TO_LOW_FREQ) currentClass = "LOW";
    else currentClass = "MID";
  }
  else { // HIGH
    if (freq < HIGH_TO_MID_FREQ && freq >= MID_TO_LOW_FREQ) currentClass = "MID";
    else if (freq < MID_TO_LOW_FREQ) currentClass = "LOW";
    else currentClass = "HIGH";
  }

  return currentClass;
}

// ============================================================
// Filter switching
// ============================================================
void setFilter(String cls) {
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
// Display helpers
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

  drawFrame(BOX_PRE_X, BOX_PRE_Y, BOX_PRE_W, BOX_PRE_H);
  drawFrame(BOX_POST_X, BOX_POST_Y, BOX_POST_W, BOX_POST_H);

  drawFrame(BOX_WAVE_X, BOX_WAVE_Y, BOX_WAVE_W, BOX_WAVE_H);

  drawTitleText(30, 68, "FREQUENCY");
  drawTitleText(350, 68, "VOICE CLASS");
  drawTitleText(590, 68, "FILTER MODE");

  drawTitleText(30, 182, "A0 PRE-FILTER");
  drawTitleText(420, 182, "A1 POST-FILTER");

  drawTitleText(30, 310, "POST-FILTER WAVEFORM");
}

void clearDynamicPanels() {
  display.fillRect(30, 95, 280, 45, C_BG);
  display.fillRect(360, 95, 180, 45, C_BG);
  display.fillRect(600, 95, 160, 45, C_BG);

  display.fillRect(30, 208, 350, 60, C_BG);
  display.fillRect(420, 208, 350, 60, C_BG);

  display.fillRect(25, 445, 730, 18, C_BG);
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

void drawSignalBar(int x, int y, int w, int h, double adcVal, uint16_t color) {
  int fillW = map((int)adcVal, 0, 4095, 0, w);

  display.drawRect(x, y, w, h, C_WHITE);
  display.fillRect(x + 1, y + 1, w - 2, h - 2, C_BG);
  display.fillRect(x + 1, y + 1, fillW, h - 2, color);

  int centerX = x + w / 2;
  display.drawLine(centerX, y, centerX, y + h, C_RED);
}

void drawSignalPanel(int panelX, double adcVal, float voltage, uint16_t color) {
  display.setTextColor(C_WHITE);
  display.setTextSize(2);

  display.setCursor(panelX, 214);
  display.print("ADC: ");
  display.print((int)adcVal);

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

void updateWaveformBuffer(int rawPost) {
  for (int i = 0; i < GRAPH_W - 1; i++) {
    waveformBuffer[i] = waveformBuffer[i + 1];
  }

  int centered = rawPost - 2048;
  int y = GRAPH_CENTER_Y - (int)(centered * WAVE_SCALE);

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
// Sampling + FFT
// ============================================================
void acquireSamples(long &sumA0, long &sumA1) {
  sumA0 = 0;
  sumA1 = 0;

  for (int i = 0; i < FFT_SAMPLES; i++) {
    int rawA0 = analogRead(PRE_FILTER_PIN);
    int rawA1 = analogRead(POST_FILTER_PIN);

    sumA0 += rawA0;
    sumA1 += rawA1;

    vReal[i] = rawA0;
    vImag[i] = 0.0;

    updateWaveformBuffer(rawA1);

    delayMicroseconds(125);
  }
}

double computeDominantFrequency() {
  double mean = 0.0;
  for (int i = 0; i < FFT_SAMPLES; i++) {
    mean += vReal[i];
  }
  mean /= FFT_SAMPLES;

  for (int i = 0; i < FFT_SAMPLES; i++) {
    vReal[i] -= mean;
  }

  FFT.windowing(FFTWindow::Hamming, FFTDirection::Forward);
  FFT.compute(FFTDirection::Forward);
  FFT.complexToMagnitude();

  return FFT.majorPeak();
}

// ============================================================
// Setup
// ============================================================
void setup() {
  Serial.begin(115200);
  analogReadResolution(12);

  pinMode(LOW_PIN, OUTPUT);
  pinMode(MID_PIN, OUTPUT);
  pinMode(HIGH_PIN, OUTPUT);

  digitalWrite(LOW_PIN, LOW);
  digitalWrite(MID_PIN, LOW);
  digitalWrite(HIGH_PIN, LOW);

  display.begin();
  display.setRotation(1);

  drawStaticDashboard();

  for (int i = 0; i < GRAPH_W; i++) {
    waveformBuffer[i] = GRAPH_CENTER_Y;
  }

  setFilter("LOW");
}

// ============================================================
// Loop
// ============================================================
void loop() {
  long sumA0 = 0;
  long sumA1 = 0;

  acquireSamples(sumA0, sumA1);

  int avgA0 = sumA0 / FFT_SAMPLES;
  int avgA1 = sumA1 / FFT_SAMPLES;

  smoothedPreADC = smoothValue(smoothedPreADC, avgA0, ADC_ALPHA, preADCInitialized);
  smoothedPostADC = smoothValue(smoothedPostADC, avgA1, ADC_ALPHA, postADCInitialized);

  float voltageA0 = ((float)smoothedPreADC * 3.3f) / 4095.0f;
  float voltageA1 = ((float)smoothedPostADC * 3.3f) / 4095.0f;

  double rawFreq = computeDominantFrequency();
  smoothedFrequency = smoothValue(smoothedFrequency, rawFreq, FREQ_ALPHA, freqInitialized);

  String newClass = classifyVoiceStable(smoothedFrequency);
  setFilter(newClass);

  clearDynamicPanels();
  drawFrequencyPanel(smoothedFrequency);
  drawClassPanel(newClass);
  drawModePanel(newClass);

  drawSignalPanel(35, smoothedPreADC, voltageA0, C_GREEN);
  drawSignalPanel(425, smoothedPostADC, voltageA1, C_YELLOW);

  drawWaveGrid();
  drawWaveform();

  drawStatusLine("LOW is default. Switches only when freq clearly rises.");

  Serial.print("RawFreq: ");
  Serial.print(rawFreq, 1);
  Serial.print(" | SmoothFreq: ");
  Serial.print(smoothedFrequency, 1);
  Serial.print(" | Class: ");
  Serial.print(newClass);
  Serial.print(" | A0: ");
  Serial.print((int)smoothedPreADC);
  Serial.print(" | A1: ");
  Serial.println((int)smoothedPostADC);

  delay(40);
}
