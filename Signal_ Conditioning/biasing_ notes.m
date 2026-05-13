# Signal Biasing Notes

The microphone signal was biased around a DC reference voltage so the Arduino analog input could safely read the waveform.

## Purpose

Arduino analog inputs cannot process negative voltage signals directly. A reference voltage was added to shift the waveform into a readable range.

## Reference Voltage

The target reference voltage was approximately:

- 1.65 V for 3.3 V operation

## Main Components

- Voltage divider resistors
- Coupling capacitors
- LM358 op-amp bias input
- Arduino analog input

## Notes

Proper biasing helped reduce clipping and improved FFT stability during signal processing.
