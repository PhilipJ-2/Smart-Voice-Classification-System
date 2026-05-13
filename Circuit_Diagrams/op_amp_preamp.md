# LM358 Microphone Preamp

This section documents the microphone preamplifier stage used to condition the audio signal before Arduino sampling.

## Purpose

The preamp boosts the microphone signal and centers it around a DC reference voltage so the Arduino can safely read the waveform.

## Main Parts

- Electret microphone module
- LM358 op-amp
- Bias/reference voltage near 1.65 V
- Gain-setting resistors
- Coupling capacitors
- Arduino analog input

## Notes

The signal must stay centered around the reference voltage to prevent clipping and distortion before FFT processing.
