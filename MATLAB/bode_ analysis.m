% Bode Plot and Frequency Response Analysis
% Smart Voice Classification System

clear;
clc;

% Example RC filter values
R = 1000;          % Resistance in ohms
C = 0.1e-6;        % Capacitance in farads

% Transfer function
num = [1];
den = [R*C 1];

system_tf = tf(num, den);

% Generate bode plot
figure;
bode(system_tf);
grid on;

title('RC Filter Bode Plot');
