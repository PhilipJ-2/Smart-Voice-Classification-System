# Classification Logic

The classification system uses FFT peak analysis to determine whether the incoming signal belongs to a low, mid, or high frequency group.

## Processing Flow

Microphone Input  
→ Signal Conditioning  
→ Arduino Analog Sampling  
→ FFT Processing  
→ Peak Frequency Detection  
→ Frequency Classification  
→ Display Output

## Classification Output

The system displays:

- LOW
- MID
- HIGH

based on the dominant detected frequency range.

## Notes

The classification logic was tested using multiple signal frequencies and microphone input conditions to improve stability and consistency.
