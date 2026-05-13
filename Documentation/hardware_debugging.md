# Hardware Debugging

This section documents common hardware testing and debugging areas from the project.

## Main Debugging Areas

- Microphone signal strength
- LM358 op-amp biasing
- Gain adjustment
- Filter output stability
- Arduino analog input readings
- Display output behavior
- Speaker/audio test output

## Notes

The microphone signal required proper biasing and gain tuning so the waveform stayed centered and usable for frequency analysis.

A stable reference voltage was important because the Arduino analog input cannot read negative voltage signals directly.
