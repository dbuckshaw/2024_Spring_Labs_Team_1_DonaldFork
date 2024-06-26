from scipy.io.wavfile import read
import numpy as np
import pyaudio
import wave

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 48000
CHUNK = 512
RECORD_SECONDS = 5

audio = pyaudio.PyAudio()

# programatically get the left/right indexes, assumes left was plugged in first
indexes = []

info = audio.get_host_api_info_by_index(0)
numdevices = info.get("deviceCount")

for i in range(0, numdevices):
    if (
        audio.get_device_info_by_host_api_device_index(0, i).get("maxInputChannels")
    ) > 0 and "USB Composite Device: Audio" in audio.get_device_info_by_host_api_device_index(
        0, i
    ).get(
        "name"
    ):
        indexes.append(i)

if len(indexes) != 2:
    raise SystemExit("Incorrect number of microphones, I exit")

# start recording
left_stream = audio.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    frames_per_buffer=CHUNK,
    input_device_index=indexes[0],
)

right_stream = audio.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    frames_per_buffer=CHUNK,
    input_device_index=indexes[1],
)

left_frames = []
right_frames = []

for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
    # It overflows, hopefully just ignoring it is fine
    left_data = left_stream.read(CHUNK, exception_on_overflow=False)
    right_data = right_stream.read(CHUNK, exception_on_overflow=False)
    left_frames.append(left_data)
    right_frames.append(right_data)

# stop recording
left_stream.stop_stream()
right_stream.stop_stream()
left_stream.close()
right_stream.close()
audio.terminate()

# create the output files
waveFile = wave.open("left.wav", "wb")
waveFile.setnchannels(CHANNELS)
waveFile.setsampwidth(audio.get_sample_size(FORMAT))
waveFile.setframerate(RATE)
waveFile.writeframes(b"".join(left_frames))
waveFile.close()

waveFile = wave.open("right.wav", "wb")
waveFile.setnchannels(CHANNELS)
waveFile.setsampwidth(audio.get_sample_size(FORMAT))
waveFile.setframerate(RATE)
waveFile.writeframes(b"".join(right_frames))
waveFile.close()

# read in that data
sampling_rate, left = read("left.wav")
_, right = read("right.wav")

# run correlation
corr = np.fft.ifft(
    np.fft.fft(left, len(left) + len(right))
    * np.fft.fft(right[::-1], len(right) + len(right))
)

# determine direction
max = np.argmax(corr)
adjusted_max = max - (len(corr) / 2)
delay = adjusted_max * (1 / sampling_rate)

if delay < 0:
    print("LEFT")
else:
    print("RIGHT")
