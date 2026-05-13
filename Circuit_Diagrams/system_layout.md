# System Layout

This section documents the full hardware layout for the Smart Voice Classification System.

## Major Subsystems

- Microphone input
- LM358 op-amp preamp
- Signal conditioning/filter network
- Arduino GIGA R1 WiFi
- GIGA Display Shield
- FFT processing firmware
- Low/mid/high classification output
- Speaker/audio test output

## Signal Flow

Microphone → Op-Amp Preamp → Filter Network → Arduino Analog Input → FFT Processing → Display Output → Classification Result

## Notes

The system was designed to combine analog signal conditioning with embedded digital signal processing and real-time visual feedback.
