#include "Arduino_GigaDisplay_GFX.h"
#include <arduinoFFT.h>
#include <SPI.h>
#include <math.h>

// ============================================================
// SMART MIC - VERSION 3
// Final polished dashboard version
//
// Features:
// - A0 = pre-filter signal
// - A1 = post-filter signal
// - FFT on A0
// - Stable LOW / MID / HIGH classification
// - MCP4131 digital potentiometer control
// - Post-filter waveform display with persistence smoothing
// - Clean dashboard layout
// ============================================================

// ============================================================
// DISPLAY
// ============================================================
GigaDisplay_GFX display;

// ============================================================
// PIN DEFINITIONS
// ============================================================
#define PRE_FILTER_PIN   A0   // LM358 output (before digital pot/filter)
#define POST_FILTER_PIN  A1   // filter output node (after digital pot/filter)
#define POT_CS           10   // MCP4131 chip select

// ============================================================
// FFT SETTINGS
// ============================================================
#define FFT_SAMPLES 128
#define SAMPLING_FREQUENCY 8000

double vReal[FFT_SAMPLES];
double vImag[FFT_SAMPLES];
ArduinoFFT<double> FFT = ArduinoFFT<double>(vReal, vImag, FFT_SAMPLES, SAMPLING_FREQUENCY);

// ============================================================
// TUNING CONSTANTS
// ============================================================

// Classification thresholds
const double LOW_TO_MID_FREQ   = 250.0;
const double MID_TO_HIGH_FREQ  = 500.0;
const double MID_TO_LOW_FREQ   = 200.0;
const double HIGH_TO_MID_FREQ  = 450.0;

// Pot values for LOW / MID / HIGH
const byte POT_LOW_VALUE  = 110;
const byte POT_MID_VALUE  = 70;
const byte POT_HIGH_VALUE = 25;

// Smoothing factors
const double FREQ_ALPHA = 0.16;    // lower = more stable
const double ADC_ALPHA  = 0.18;
const double WAVE_ALPHA = 0.12;

// Waveform scale
const float WAVEFORM_SCALE = 0.045f;

// ============================================================
// UI LAYOUT
// ============================================================

// Screen size is effectively landscape after setRotation(1)
const int SCREEN_W = 800;
const int SCREEN_H = 480;

// Header
const int TITLE_X = 20;
const int TITLE_Y = 12;

// Top row
const int BOX_FREQ_X = 20;
const int BOX_FREQ_Y = 55;
const int BOX_FREQ_W = 300;
const int BOX_FREQ_H = 95;

const int BOX_CLASS_X = 340;
const int BOX_CLASS_Y = 55;
const int BOX_CLASS_W = 220;
const int BOX_CLASS_H = 95;

const int BOX_POT_X = 580;
const int BOX_POT_Y = 55;
const int BOX_POT_W = 200;
const int BOX_POT_H = 95;

// Middle row
const int BOX_PRE_X = 20;
const int BOX_PRE_Y = 170;
const int BOX_PRE_W = 370;
const int BOX_PRE_H = 110;

const int BOX_POST_X = 410;
const int BOX_POST_Y = 170;
const int BOX_POST_W = 370;
const int BOX_POST_H = 110;

// Bottom waveform area
const int BOX_WAVE_X = 20;
const int BOX_WAVE_Y = 300;
const int BOX_WAVE_W = 760;
const int BOX_WAVE_H = 150;

// Inner graph area
const int GRAPH_X = 35;
const int GRAPH_Y = 325;
const int GRAPH_W = 730;
const int GRAPH_H = 95;
const int GRAPH_CENTER_Y = GRAPH_Y + GRAPH_H / 2;

// Footer / status
const int STATUS_X = 25;
const int STATUS_Y = 445;

// ============================================================
// COLORS (RGB565)
// ============================================================
const uint16_t C_BG       = 0x0000;
const uint16_t C_WHITE    = 0xFFFF;
const uint16_t C_GREEN    = 0x07E0;
const uint16_t C_CYAN     = 0x07FF;
const uint16_t C_YELLOW   = 0xFFE0;
const uint16_t C_MAGENTA  = 0xF81F;
const uint16_t C_RED      = 0xF800;
const uint16_t C_GRID     = 0x2104;
const uint16_t C_CENTER   = 0x7BEF;
const uint16_t C_BLUEBAR  = 0x001F;

// ============================================================
// GLOBAL STATE
// ============================================================
String currentClass = "LOW";
byte currentPotValue = POT_LOW_VALUE;

double smoothedFrequency = 0.0;
bool freqInitialized = false;

double smoothedPreADC = 0.0;
double smoothedPostADC = 0.0;
bool adcInitialized = false;

int waveformRaw[GRAPH_W];
int waveformSmooth[GRAPH_W];

String statusText = "READY";

// ============================================================
// DIGITAL POT CONTROL
// ============================================================
void setPot(byte value) {
  digitalWrite(POT_CS, LOW);
  SPI.transfer(0b00010001);  // write command for pot 0
  SPI.transfer(value);
  digitalWrite(POT_CS, HIGH);
  currentPotValue = value;
}

// ============================================================
// CLASSIFICATION
// ============================================================
String classifyVoiceStable(double freq) {
  if (currentClass == "LOW") {
    if (freq >= MID_TO_HIGH_FREQ) currentClass = "HIGH";
    else if (freq >= LOW_TO_MID_FREQ) currentClass = "MID";
  }
  else if (currentClass == "MID") {
    if (freq >= MID_TO_HIGH_FREQ) currentClass = "HIGH";
    else if (freq < MID_TO_LOW_FREQ) currentClass = "LOW";
  }
  else { // HIGH
    if (freq < HIGH_TO_MID_FREQ && freq >= MID_TO_LOW_FREQ) currentClass = "MID";
    else if (freq < MID_TO_LOW_FREQ) currentClass = "LOW";
  }

  return currentClass;
}

uint16_t classColor(const String& cls) {
  if (cls == "LOW") return C_CYAN;
  if (cls == "MID") return C_YELLOW;
  return C_MAGENTA;
}

byte potValueForClass(const String& cls) {
  if (cls == "LOW") return POT_LOW_VALUE;
  if (cls == "MID") return POT_MID_VALUE;
  return POT_HIGH_VALUE;
}

// ============================================================
// SMOOTHING HELPERS
// ============================================================
double smoothValue(double oldVal, double newVal, double alpha, bool& initialized) {
  if (!initialized) {
    initialized = true;
    return newVal;
  }
  return (1.0 - alpha) * oldVal + alpha * newVal;
}

// ============================================================
// DISPLAY HELPERS
// ============================================================
void drawFrame(int x, int y, int w, int h) {
  display.drawRect(x, y, w, h, C_WHITE);
}

void drawTitleText(int x, int y, const char* txt) {
  display.setTextColor(C_WHITE);
  display.setTextSize(2);
  display.setCursor(x, y);
  display.println(txt);
}

void drawStaticDashboard() {
  display.fillScreen(C_BG);

  display.setTextColor(C_WHITE);
  display.setTextSize(3);
  display.setCursor(TITLE_X, TITLE_Y);
  display.println("SMART MIC");

  drawFrame(BOX_FREQ_X,  BOX_FREQ_Y,  BOX_FREQ_W,  BOX_FREQ_H);
  drawFrame(BOX_CLASS_X, BOX_CLASS_Y, BOX_CLASS_W, BOX_CLASS_H);
  drawFrame(BOX_POT_X,   BOX_POT_Y,   BOX_POT_W,   BOX_POT_H);

  drawFrame(BOX_PRE_X,   BOX_PRE_Y,   BOX_PRE_W,   BOX_PRE_H);
  drawFrame(BOX_POST_X,  BOX_POST_Y,  BOX_POST_W,  BOX_POST_H);

  drawFrame(BOX_WAVE_X,  BOX_WAVE_Y,  BOX_WAVE_W,  BOX_WAVE_H);

  drawTitleText(30, 68,   "FREQUENCY");
  drawTitleText(350, 68,  "VOICE CLASS");
  drawTitleText(590, 68,  "DIGITAL POT");

  drawTitleText(30, 182,  "A0 PRE-FILTER");
  drawTitleText(420, 182, "A1 POST-FILTER");

  drawTitleText(30, 310,  "POST-FILTER WAVEFORM");
}

void clearDynamicPanels() {
  display.fillRect(30, 95, 280, 45, C_BG);
  display.fillRect(360, 95, 180, 45, C_BG);
  display.fillRect(600, 95, 160, 45, C_BG);

  display.fillRect(30, 208, 350, 60, C_BG);
  display.fillRect(420, 208, 350, 60, C_BG);

  display.fillRect(STATUS_X, STATUS_Y, 730, 18, C_BG);
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

void drawClassPanel(const String& cls) {
  uint16_t color = classColor(cls);

  display.fillRect(380, 98, 150, 40, C_BG);
  display.fillRoundRect(385, 100, 140, 36, 8, color);

  display.setTextColor(C_BG);
  display.setTextSize(3);

  if (cls == "LOW") {
    display.setCursor(425, 106);
  } else if (cls == "MID") {
    display.setCursor(425, 106);
  } else {
    display.setCursor(415, 106);
  }

  display.print(cls);
}

void drawPotPanel(byte potVal) {
  display.setTextColor(C_WHITE);
  display.setTextSize(3);
  display.setCursor(620, 104);
  display.print("  ");
  display.setCursor(620, 104);
  display.print(potVal);
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

void drawStatusLine(const String& txt) {
  display.setTextColor(C_WHITE);
  display.setTextSize(2);
  display.setCursor(STATUS_X, STATUS_Y);
  display.print(txt);
}

// ============================================================
// WAVEFORM
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
    waveformRaw[i] = waveformRaw[i + 1];
    waveformSmooth[i] = waveformSmooth[i + 1];
  }

  int centered = rawPost - 2048;
  int yRaw = GRAPH_CENTER_Y - (int)(centered * WAVEFORM_SCALE);

  if (yRaw < GRAPH_Y + 2) yRaw = GRAPH_Y + 2;
  if (yRaw > GRAPH_Y + GRAPH_H - 2) yRaw = GRAPH_Y + GRAPH_H - 2;

  waveformRaw[GRAPH_W - 1] = yRaw;

  // Smooth the last point against previous smooth point
  if (GRAPH_W >= 2) {
    int prev = waveformSmooth[GRAPH_W - 2];
    int smoothed = (int)((1.0 - WAVE_ALPHA) * prev + WAVE_ALPHA * yRaw);
    waveformSmooth[GRAPH_W - 1] = smoothed;
  } else {
    waveformSmooth[GRAPH_W - 1] = yRaw;
  }
}

void drawWaveform() {
  // Dim green shadow trace
  for (int i = 1; i < GRAPH_W; i++) {
    display.drawLine(GRAPH_X + i - 1, waveformRaw[i - 1],
                     GRAPH_X + i,     waveformRaw[i],
                     0x03E0);  // dimmer green
  }

  // Bright smoothed trace
  for (int i = 1; i < GRAPH_W; i++) {
    display.drawLine(GRAPH_X + i - 1, waveformSmooth[i - 1],
                     GRAPH_X + i,     waveformSmooth[i],
                     C_GREEN);
  }
}

// ============================================================
// DATA ACQUISITION
// ============================================================
void acquireSamples(long& sumA0, long& sumA1) {
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
// SETUP
// ============================================================
void setup() {
  Serial.begin(115200);
  analogReadResolution(12);

  // SPI / Digital Pot
  pinMode(POT_CS, OUTPUT);
  digitalWrite(POT_CS, HIGH);
  SPI.begin();

  // Display
  display.begin();
  display.setRotation(1);

  drawStaticDashboard();

  // Initialize waveform buffers to center line
  for (int i = 0; i < GRAPH_W; i++) {
    waveformRaw[i] = GRAPH_CENTER_Y;
    waveformSmooth[i] = GRAPH_CENTER_Y;
  }

  setPot(currentPotValue);
  statusText = "System initialized";
}

// ============================================================
// LOOP
// ============================================================
void loop() {
  long sumA0 = 0;
  long sumA1 = 0;

  acquireSamples(sumA0, sumA1);

  int avgA0 = sumA0 / FFT_SAMPLES;
  int avgA1 = sumA1 / FFT_SAMPLES;

  smoothedPreADC = smoothValue(smoothedPreADC, avgA0, ADC_ALPHA, adcInitialized);
  smoothedPostADC = smoothValue(smoothedPostADC, avgA1, ADC_ALPHA, adcInitialized);

  float voltageA0 = ((float)smoothedPreADC * 3.3f) / 4095.0f;
  float voltageA1 = ((float)smoothedPostADC * 3.3f) / 4095.0f;

  double rawFreq = computeDominantFrequency();
  smoothedFrequency = smoothValue(smoothedFrequency, rawFreq, FREQ_ALPHA, freqInitialized);

  String newClass = classifyVoiceStable(smoothedFrequency);
  byte desiredPot = potValueForClass(newClass);

  if (desiredPot != currentPotValue) {
    setPot(desiredPot);
  }

  // Status string
  statusText = "Tracking input -> FFT -> class -> pot -> filter";

  // UI update
  clearDynamicPanels();
  drawFrequencyPanel(smoothedFrequency);
  drawClassPanel(newClass);
  drawPotPanel(currentPotValue);

  drawSignalPanel(35,  smoothedPreADC,  voltageA0, C_GREEN);
  drawSignalPanel(425, smoothedPostADC, voltageA1, C_YELLOW);

  drawWaveGrid();
  drawWaveform();
  drawStatusLine(statusText);

  // Serial debug
  Serial.print("Freq: ");
  Serial.print(smoothedFrequency, 1);
  Serial.print(" Hz | Class: ");
  Serial.print(newClass);
  Serial.print(" | Pot: ");
  Serial.print(currentPotValue);
  Serial.print(" | A0: ");
  Serial.print((int)smoothedPreADC);
  Serial.print(" | A1: ");
  Serial.println((int)smoothedPostADC);

  delay(40);
}
