#include "Arduino_GigaDisplay_GFX.h"
#include <arduinoFFT.h>

// ============================================================
// SMART MIC FINAL BUILD - UPDATED
// Fix: Uses signal movement / peak-to-peak instead of average A0
// so it does NOT stay LOW the whole time.
// ============================================================

GigaDisplay_GFX display;

// ---------------- Options ----------------
#define STARTUP_SPEAKER_TEST 1
#define CLASS_TONE_ON_CHANGE 1

// ---------------- Pins ----------------
#define RAW_PIN      A0
#define FILTER_PIN   A1

#define LOW_PIN      2
#define MID_PIN      3
#define HIGH_PIN     4

// ---------------- FFT ----------------
#define FFT_SAMPLES 128
#define SAMPLING_FREQUENCY 8000

double vReal[FFT_SAMPLES];
double vImag[FFT_SAMPLES];

ArduinoFFT<double> FFT = ArduinoFFT<double>(vReal, vImag, FFT_SAMPLES, SAMPLING_FREQUENCY);

// ---------------- Thresholds ----------------
// These are easier to trigger than the old version
const double VALID_MIN_FREQ   = 70.0;
const double VALID_MAX_FREQ   = 1500.0;

const double LOW_TO_MID_FREQ  = 250.0;
const double MID_TO_HIGH_FREQ = 550.0;

const double MID_TO_LOW_FREQ  = 200.0;
const double HIGH_TO_MID_FREQ = 480.0;

// Signal activity threshold
// If it still stays LOW, lower this to 10.
// If it jumps too much, raise this to 30 or 40.
const int ACTIVE_P2P_THRESHOLD = 18;

// ---------------- Smoothing ----------------
const double FREQ_ALPHA = 0.18;
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

// ---------------- State ----------------
String currentClass = "LOW";
String lastClassForTone = "LOW";

double smoothedFrequency = 0.0;
bool freqInitialized = false;

double smoothedA0 = 0.0;
double smoothedA1 = 0.0;
bool a0Initialized = false;
bool a1Initialized = false;

int waveformBuffer[GRAPH_W];

unsigned long lastToneTime = 0;
const unsigned long TONE_COOLDOWN_MS = 700;

// ============================================================
// Tone functions
// ============================================================
void playToneOnce(int freq, int duration_ms) {
  pinMode(FILTER_PIN, OUTPUT);

  int period = 1000000 / freq;
  int cycles = (freq * duration_ms) / 1000;

  for (int i = 0; i < cycles; i++) {
    digitalWrite(FILTER_PIN, HIGH);
    delayMicroseconds(period / 2);
    digitalWrite(FILTER_PIN, LOW);
    delayMicroseconds(period / 2);
  }

  digitalWrite(FILTER_PIN, LOW);
  delay(20);
  pinMode(FILTER_PIN, INPUT);
}

void playClassTone(const String &cls) {
  if (cls == "LOW") {
    playToneOnce(400, 120);
  }
  else if (cls == "MID") {
    playToneOnce(900, 120);
  }
  else {
    playToneOnce(1500, 120);
  }
}

void playStartupTone() {
  playToneOnce(700, 150);
  delay(80);
  playToneOnce(1000, 150);
  delay(80);
  playToneOnce(1300, 200);
}

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
// Filter Control
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
// Classification
// ============================================================
String classifyVoiceStable(double freq) {
  if (freq < VALID_MIN_FREQ || freq > VALID_MAX_FREQ) {
    return currentClass;
  }

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
  else {
    if (freq < HIGH_TO_MID_FREQ && freq >= MID_TO_LOW_FREQ) currentClass = "MID";
    else if (freq < MID_TO_LOW_FREQ) currentClass = "LOW";
    else currentClass = "HIGH";
  }

  return currentClass;
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

void updateWaveformBuffer(int rawA1) {
  for (int i = 0; i < GRAPH_W - 1; i++) {
    waveformBuffer[i] = waveformBuffer[i + 1];
  }

  int centered = rawA1 - 2048;
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
void acquireSamples(long &sumA0, long &sumA1,
                    int &minA0, int &maxA0,
                    int &minA1, int &maxA1) {
  sumA0 = 0;
  sumA1 = 0;

  minA0 = 4095;
  maxA0 = 0;
  minA1 = 4095;
  maxA1 = 0;

  for (int i = 0; i < FFT_SAMPLES; i++) {
    int rawA0 = analogRead(RAW_PIN);
    int rawA1 = analogRead(FILTER_PIN);

    sumA0 += rawA0;
    sumA1 += rawA1;

    if (rawA0 < minA0) minA0 = rawA0;
    if (rawA0 > maxA0) maxA0 = rawA0;

    if (rawA1 < minA1) minA1 = rawA1;
    if (rawA1 > maxA1) maxA1 = rawA1;

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

#if STARTUP_SPEAKER_TEST
  drawStatusLine("Startup speaker test...");
  playStartupTone();
  display.fillRect(25, 445, 740, 20, C_BG);
#endif

  pinMode(FILTER_PIN, INPUT);

  for (int i = 0; i < GRAPH_W; i++) {
    waveformBuffer[i] = GRAPH_CENTER_Y;
  }

  currentClass = "LOW";
  lastClassForTone = "LOW";
  setFilter("LOW");
}

// ============================================================
// Loop
// ============================================================
void loop() {
  long sumA0 = 0;
  long sumA1 = 0;

  int minA0, maxA0, minA1, maxA1;

  acquireSamples(sumA0, sumA1, minA0, maxA0, minA1, maxA1);

  int avgA0 = sumA0 / FFT_SAMPLES;
  int avgA1 = sumA1 / FFT_SAMPLES;

  int p2pA0 = maxA0 - minA0;
  int p2pA1 = maxA1 - minA1;

  smoothedA0 = smoothValue(smoothedA0, avgA0, ADC_ALPHA, a0Initialized);
  smoothedA1 = smoothValue(smoothedA1, avgA1, ADC_ALPHA, a1Initialized);

  float voltageA0 = ((float)smoothedA0 * 3.3f) / 4095.0f;
  float voltageA1 = ((float)smoothedA1 * 3.3f) / 4095.0f;

  double rawFreq = computeDominantFrequency();
  smoothedFrequency = smoothValue(smoothedFrequency, rawFreq, FREQ_ALPHA, freqInitialized);

  String newClass;

  // NEW FIX:
  // Do NOT use average voltage for idle. Use peak-to-peak signal movement.
  if (p2pA0 < ACTIVE_P2P_THRESHOLD) {
    currentClass = "LOW";
    newClass = "LOW";
  }
  else {
    newClass = classifyVoiceStable(smoothedFrequency);
  }

  setFilter(newClass);

#if CLASS_TONE_ON_CHANGE
  if (newClass != lastClassForTone && millis() - lastToneTime > TONE_COOLDOWN_MS) {
    playClassTone(newClass);
    lastClassForTone = newClass;
    lastToneTime = millis();
  }
#endif

  clearDynamicPanels();

  drawFrequencyPanel(smoothedFrequency);
  drawClassPanel(newClass);
  drawModePanel(newClass);

  drawSignalPanel(35, smoothedA0, voltageA0, C_GREEN);
  drawSignalPanel(425, smoothedA1, voltageA1, C_YELLOW);

  drawWaveGrid();
  drawWaveform();

  String status = "P2P A0: ";
  status += p2pA0;
  status += " | LOW<250 MID<550 HIGH>=550";
  drawStatusLine(status);

  Serial.print("RawFreq: ");
  Serial.print(rawFreq, 1);
  Serial.print(" | SmoothFreq: ");
  Serial.print(smoothedFrequency, 1);
  Serial.print(" | Class: ");
  Serial.print(newClass);
  Serial.print(" | A0 avg: ");
  Serial.print((int)smoothedA0);
  Serial.print(" | A0 P2P: ");
  Serial.print(p2pA0);
  Serial.print(" | A1 avg: ");
  Serial.print((int)smoothedA1);
  Serial.print(" | A1 P2P: ");
  Serial.println(p2pA1);

  delay(40);
}
