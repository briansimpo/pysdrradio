import scipy.signal as signal
import numpy as np

class Decoder:

    def __init__(self) -> None:
        pass

    def decode(self, samples, sample_rate, offset):
        
        # Convert samples to a numpy array
        x1 = np.array(samples).astype(np.complex64)

        # To mix the data down, generate a digital complex exponential
        # (with the same length as x1) with phase - offset/sample_rate
        fc1 = np.exp(-1.0j * 2.0 * np.pi * offset/sample_rate * np.arange(len(x1)))
        # Now, just multiply x1 and the digital complex exponential
        x2 = x1 * fc1

        # An FM broadcast signal has  a bandwidth of 200 kHz
        fm_broadcast = 200000
        n_taps = 64
        # Use Remez algorithm to design filter coefficients
        lpf = signal.remez(n_taps, [0, fm_broadcast, fm_broadcast + (sample_rate/2-fm_broadcast)/4, sample_rate/2], [1, 0], fs=sample_rate)
        x3 = signal.lfilter(lpf, 1.0, x2)

        decimation_rate = int(sample_rate/fm_broadcast)
        x4 = x3[0::decimation_rate]
        # Calculate the new sampling rate
        new_sample_rate = sample_rate/decimation_rate

        # Polar discriminator
        y5 = x4[1:] * np.conj(x4[:-1])
        x5 = np.angle(y5)

        # The de-emphasis filter
        # Given a signal 'x5' (in a numpy array) with sampling rate new_sample_rate
        d = new_sample_rate * 75e-6  # Calculate the # of samples to hit the -3dB point
        x = np.exp(-1 / d)  # Calculate the decay between each sample
        b = [1 - x]  # Create the filter coefficients
        a = [1, -x]
        x6 = signal.lfilter(b, a, x5)

        # Find a decimation rate to achieve audio sampling rate between 44-48 kHz
        audio_freq = 44100.0
        dec_audio = int(new_sample_rate/audio_freq)

        x7 = signal.decimate(x6, dec_audio)

        # Scale audio to adjust volume
        x7 *= 10000 / np.max(np.abs(x7))

        audio_samples = x7.astype(np.int16)

        return audio_samples