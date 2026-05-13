% Signal Response and Filtering Analysis
% Smart Voice Classification System

clear;
clc;

fs = 1000;
t = 0:1/fs:1;

% Example input signal
input_signal = sin(2*pi*50*t) + 0.5*sin(2*pi*200*t);

% Low-pass filter design
fc = 100;
[b, a] = butter(2, fc/(fs/2), 'low');

% Filtered output
filtered_signal = filter(b, a, input_signal);

figure;
plot(t, filtered_signal);

xlabel('Time (s)');
ylabel('Amplitude');
title('Filtered Signal Response');
grid on;
