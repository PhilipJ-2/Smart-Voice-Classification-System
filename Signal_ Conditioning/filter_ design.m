# Filter Design

This section documents the signal filtering stage used after the microphone preamp.

## Purpose

The filter network helped reduce noise and improve signal quality before FFT analysis.

## Main Features

- RC filtering
- Signal smoothing
- Noise reduction
- Improved waveform stability

## Signal Path

Microphone  
→ LM358 Preamp  
→ Filter Network  
→ Arduino Analog Input

## Notes

Different resistor and capacitor values were tested to improve low, mid, and high frequency detection consistency.
