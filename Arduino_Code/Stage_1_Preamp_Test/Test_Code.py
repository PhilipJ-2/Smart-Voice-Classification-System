#include "Arduino_GigaDisplay_GFX.h"
#include <arduinoFFT.h>
#include <math.h>

GigaDisplay_GFX display;

#define MIC_PIN A0
#define FFT_SAMPLES 128
#define SAMPLING_FREQUENCY 8000

double vReal[FFT_SAMPLES];
double vImag[FFT_SAMPLES];

ArduinoFFT<double> FFT = ArduinoFFT<double>(vReal, vImag, FFT_SAMPLES, SAMPLING_FREQUENCY);

String currentClass = "LOW";

const int graphX = 30;
const int graphY = 260;
const int graphW = 740;
const int graphH = 160;
const int centerY = graphY + graphH / 2;

float phaseOffset = 0.0f;

String classifyVoiceStable(double freq) {
  if (currentClass == "LOW") {
    if (freq >= 500.0) currentClass = "HIGH";
    else if (freq >= 250.0) currentClass = "MID";
  } else if (currentClass == "MID") {
    if (freq >= 500.0) currentClass = "HIGH";
    else if (freq < 200.0) currentClass = "LOW";
  } else {
    if (freq < 450.0 && freq >= 200.0) currentClass = "MID";
    else if (freq < 200.0) currentClass = "LOW";
  }
  return currentClass;
}

uint16_t classColor(const String& voiceClass) {
  if (voiceClass == "LOW") return 0x07FF;   // cyan
  if (voiceClass == "MID") return 0xFFE0;   // yellow
  return 0xF81F;                            // magenta
}

void drawStaticUI() {
  display.fillScreen(0x0000);

  display.setTextColor(0xFFFF);
  display.setTextSize(3);
  display.setCursor(20, 15);
  display.println("SMART MIC");

  display.drawRect(20, 60, 350, 110, 0xFFFF);
  display.drawRect(400, 60, 320, 110, 0xFFFF);
  display.drawRect(20, 190, 700, 35, 0xFFFF);
  display.drawRect(20, 250, 760, 180, 0xFFFF);

  display.setTextSize(2);
  display.setCursor(30, 70);
  display.println("FREQUENCY");

  display.setCursor(410, 70);
  display.println("VOICE CLASS");

  display.setCursor(30, 170);
  display.println("SIGNAL LEVEL");

  display.setCursor(30, 230);
  display.println("OSCILLOSCOPE VIEW");
}

void drawWaveformGrid() {
  display.fillRect(graphX + 1, graphY + 1, graphW - 2, graphH - 2, 0x0000);

  for (int x = graphX; x <= graphX + graphW; x += 92) {
    display.drawLine(x, graphY, x, graphY + graphH, 0x2104);
  }

  for (int y = graphY + 20; y < graphY + graphH; y += 20) {
    display.drawLine(graphX, y, graphX + graphW, y, 0x2104);
  }

  display.drawLine(graphX, centerY, graphX + graphW, centerY, 0x7BEF);
}

void drawSyntheticWaveform(String voiceClass, double peakFreq) {
  float cyclesAcrossScreen;
  float phaseStep;
  int amplitude;

  if (voiceClass == "LOW") {
    cyclesAcrossScreen = 2.0f;
    phaseStep = 0.12f;
    amplitude = 26;
  } else if (voiceClass == "MID") {
    cyclesAcrossScreen = 4.0f;
    phaseStep = 0.20f;
    amplitude = 34;
  } else {
    cyclesAcrossScreen = 7.0f;
    phaseStep = 0.32f;
    amplitude = 42;
  }

  // Small influence from real detected frequency
  if (peakFreq > 0.0) {
    float tweak = (float)(peakFreq / 1000.0);
    if (tweak > 0.25f) tweak = 0.25f;
    cyclesAcrossScreen += tweak;
  }

  phaseOffset += phaseStep;

  for (int i = 1; i < graphW; i++) {
    float t1 = ((float)(i - 1) / (float)graphW) * 2.0f * PI * cyclesAcrossScreen + phaseOffset;
    float t2 = ((float)i / (float)graphW) * 2.0f * PI * cyclesAcrossScreen + phaseOffset;

    int x1 = graphX + i - 1;
    int x2 = graphX + i;

    int y1 = centerY - (int)(amplitude * sin(t1));
    int y2 = centerY - (int)(amplitude * sin(t2));

    display.drawLine(x1, y1, x2, y2, 0x07E0);
  }
}

void updateLevelBar(int rawAvg) {
  int fillW = map(rawAvg, 0, 4095, 0, 698);
  display.fillRect(21, 191, 698, 33, 0x0000);
  display.fillRect(21, 191, fillW, 33, 0x07E0);
  display.drawLine(370, 190, 370, 225, 0xF800);
}

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);

  display.begin();
  display.setRotation(1);

  drawStaticUI();
}

void loop() {
  long rawSum = 0;

  for (int i = 0; i < FFT_SAMPLES; i++) {
    int raw = analogRead(MIC_PIN);
    rawSum += raw;

    vReal[i] = raw;
    vImag[i] = 0.0;

    delayMicroseconds(125);
  }

  int rawAvg = rawSum / FFT_SAMPLES;
  float voltage = (rawAvg * 3.3f) / 4095.0f;

  double mean = 0.0;
  for (int i = 0; i < FFT_SAMPLES; i++) mean += vReal[i];
  mean /= FFT_SAMPLES;

  for (int i = 0; i < FFT_SAMPLES; i++) vReal[i] -= mean;

  FFT.windowing(FFTWindow::Hamming, FFTDirection::Forward);
  FFT.compute(FFTDirection::Forward);
  FFT.complexToMagnitude();

  double peakFreq = FFT.majorPeak();
  String voiceClass = classifyVoiceStable(peakFreq);
  uint16_t color = classColor(voiceClass);

  display.fillRect(30, 95, 330, 60, 0x0000);
  display.fillRect(410, 95, 300, 60, 0x0000);
  display.fillRect(30, 435, 520, 25, 0x0000);

  display.setTextColor(0x07E0);
  display.setTextSize(4);
  display.setCursor(35, 105);
  display.print(peakFreq, 1);
  display.setTextSize(2);
  display.print(" Hz");

  display.fillRoundRect(455, 100, 180, 45, 8, color);
  display.setTextColor(0x0000);
  display.setTextSize(3);
  display.setCursor(505, 110);
  display.print(voiceClass);

  display.setTextColor(0xFFFF);
  display.setTextSize(2);
  display.setCursor(30, 438);
  display.print("ADC: ");
  display.print(rawAvg);
  display.print("   Bias: ");
  display.print(voltage, 2);
  display.print(" V");

  updateLevelBar(rawAvg);

  drawWaveformGrid();
  drawSyntheticWaveform(voiceClass, peakFreq);

  delay(30);
}
