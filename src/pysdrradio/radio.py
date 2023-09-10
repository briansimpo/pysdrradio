import asyncio
import time
import pyaudio
from rtlsdr import RtlSdr
from .decoder import Decoder


class Radio:
	# RTL-SDR settings
	SAMPLE_RATE = 1140000  	# Sample rate
	SAMPLE_SIZE = 51200  	# Samples to capture
	OFFSET = 250000  		# Offset to capture at
	GAIN = 'auto'

	# Audio settings
	AUDIO_SAMPLE = 44100  	# Audio sample rate (Hz)
	AUDIO_CHANNELS = 1  	# Mono audio
	AUDIO_FORMAT = pyaudio.paInt16

	def __init__(self) -> None:
		# define receiver and playback
		self.receiver = None
		self.pyaudio = None
		self.stream = None
		self.loop = asyncio.get_event_loop()

		# define radio parameters
		self.sample_rate = Radio.SAMPLE_RATE
		self.sample_size = Radio.SAMPLE_SIZE
		self.gain = Radio.GAIN
		self.offset = Radio.OFFSET

		# define decoder
		self.decoder = Decoder()

	def set_sample_rate(self, sample_rate):
		self.sample_rate = sample_rate

	def set_sample_size(self, sample_size):
		self.sample_size = sample_size

	def set_offset(self, offset):
		self.offset = offset

	def set_gain(self, gain):
		self.gain = gain

	def tune(self, frequency):
		self.center_frequency = frequency

	def setup_receiver(self):
		# Capture center frequency at an offset to avoid DC spike
		center_frequency = self.center_frequency - self.offset 

		# Configure RTL-SDR device object
		self.sdr = RtlSdr()
		self.sdr.center_freq = center_frequency 
		self.sdr.sample_rate = self.sample_rate
		self.sdr.gain = self.gain
	
	def setup_playback(self):
		# define pyaudio
		self.pyaudio = pyaudio.PyAudio()
		self.stream = self.pyaudio.open(
			format=Radio.AUDIO_FORMAT,
			channels=Radio.AUDIO_CHANNELS,
			rate=Radio.AUDIO_SAMPLE,
			output=True
		)

	def capture(self, sample_size=8192000):
		self.setup_receiver()
		samples = self.sdr.read_samples(sample_size)
		sample_data = self.decoder.decode(samples, self.sample_rate, self.offset)
		return sample_data

	def play(self):
		try:
			self.loop.run_until_complete(self.streaming())
		except KeyboardInterrupt:
			self.stop()
		except Exception as e:
			print(f"An unexpected error occurred: {e}")
			self.stop()

	async def streaming(self):
		self.setup_receiver()
		self.setup_playback()
		try:
			async for samples in self.sdr.stream(self.sample_size):
				data = self.decoder.decode(samples, self.sample_rate, self.offset)
				self.stream.write(data.tobytes())
		except Exception as e:
			print(f"An error occurred during streaming: {e}")
		finally:
			await self.stop_sdr()

	async def stop_sdr(self):
		if self.sdr:
			try:
				await self.sdr.stop()
			except Exception as e:
				print(f"An error occurred while stopping the SDR")
			self.sdr.close()
			self.sdr = None

	def stop(self):
		if self.stream:
			try:
				self.stream.stop_stream()
				self.stream.close()
			except Exception as e:
				print(f"An error occurred while stopping audio playback: {e}")
			self.stream = None
	