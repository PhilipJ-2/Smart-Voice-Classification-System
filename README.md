# 🎙️ Smart Voice Classification System

![Arduino](https://img.shields.io/badge/Platform-Arduino%20GIGA-blue)
![Signal Processing](https://img.shields.io/badge/Focus-Signal%20Processing-green)
![Op Amp](https://img.shields.io/badge/Circuit-LM358%20Op--Amp-orange)
![Status](https://img.shields.io/badge/Status-Completed-brightgreen)

---

## 📖 Overview

The **Smart Voice Classification System** is an Arduino GIGA R1 based embedded signal processing project designed to classify microphone input into **LOW**, **MID**, and **HIGH** frequency ranges.

The system combines analog electronics, signal conditioning, FFT processing, real-time waveform visualization, and embedded classification logic.

---

## ✨ Project Features

- Microphone audio input
- LM358 op-amp preamplifier
- DC biasing around 1.65 V
- RC signal filtering
- Arduino analog sampling
- FFT frequency analysis
- LOW / MID / HIGH classification
- Real-time waveform display
- GIGA Display Shield interface
- Simulation/demo mode
- Speaker/audio testing output

---

## 🛠 Hardware Used

- Arduino GIGA R1 WiFi
- Arduino GIGA Display Shield
- LM358 op-amp
- Electret microphone / microphone module
- Resistors and capacitors
- RC filter network
- Speaker/audio output stage
- Breadboard and jumper wires
- LEDs for classification outputs

---

## 🔊 Signal Flow

```text
Microphone
→ LM358 Op-Amp Preamp
→ Biasing / Signal Conditioning
→ RC Filter Network
→ Arduino Analog Input
→ FFT Processing
→ Frequency Classification
→ GIGA Display Output
```

---

## 🧠 Engineering Concepts Demonstrated

- Analog signal conditioning
- Op-amp gain tuning
- DC biasing for ADC input
- RC filter design
- FFT signal processing
- Embedded systems programming
- Real-time waveform visualization
- Frequency classification logic
- Hardware debugging and validation
- Analog-to-digital signal conversion

---

## 📂 Repository Structure

```text
Smart-Voice-Classification-System/

├── Arduino_Code/
│   ├── Stage_1_Preamp_Test/
│   ├── Stage_2_Filtering/
│   ├── Stage_3_FFT_Processing/
│   ├── Stage_4_Display_System/
│   ├── Mic_Tester/
│   └── Final_System/
│
├── Circuit_Diagrams/
├── Documentation/
├── FFT_Analysis/
├── Images/
├── MATLAB/
├── Signal_Conditioning/
├── Videos/
└── README.md
```

---

## ⚙️ Development Stages

### Stage 1 — Preamp Testing
Initial microphone and LM358 op-amp testing to verify signal amplification and biasing.

### Stage 2 — Filtering
RC filtering and signal conditioning to improve stability before sampling.

### Stage 3 — FFT Processing
Frequency analysis using FFT to identify dominant frequency regions.

### Stage 4 — Display System
Real-time waveform visualization and classification display using the GIGA Display Shield.

### Final System
Integrated microphone input, op-amp circuit, filtering, FFT classification, display output, and demo mode.

---

## 📊 MATLAB & Analysis

MATLAB scripts were used for:

- Bode plot analysis
- Waveform visualization
- Filter response testing
- Signal behavior comparison

---

## 📷 Project Photos

### Full Hardware Build
![Full System](Images/full_system.jpg)

### Op-Amp and Signal Conditioning Circuit
![Op Amp Circuit](Images/op_amp_circuit.jpg)

### GIGA Display Waveform Output
![Display Output](Images/display_output.jpg)

---

## 🎥 Demo Video

[Watch Project Demo](Videos/system_demo.mp4)

---

## 🚀 Future Improvements

- Improve microphone noise rejection
- Add automatic gain control
- Train a TinyML model for better classification
- Design a custom PCB
- Add wireless data logging
- Improve waveform scrolling and UI layout
- Add more advanced audio feature extraction

---

## 👨‍💻 Author

**Philip Perry**  
Bachelor of Science in Electrical Power Engineering Technology @ University of Houston  
Minor in Computer Science Engineering Technology  
U.S. Army Veteran & Former Sergeant
