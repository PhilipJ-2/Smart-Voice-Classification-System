% Waveform Visualization Script
% Smart Voice Classification System

clear;
clc;

fs = 1000;                 % Sampling frequency
t = 0:1/fs:1;              % Time vector

% Example waveform
signal = sin(2*pi*50*t);

figure;
plot(t, signal);

xlabel('Time (s)');
ylabel('Amplitude');
title('Microphone Signal Waveform');
grid on;
