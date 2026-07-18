from audiomentations import AddGaussianNoise
import soundfile as sf

samples, rate = sf.read("../audio/clean.wav")

augment = AddGaussianNoise(min_amplitude=0.001,
                           max_amplitude=0.015,
                           p=1)

augmented = augment(samples=samples,
                    sample_rate=rate)

sf.write("../audio/noisy.wav",
         augmented,
         rate)