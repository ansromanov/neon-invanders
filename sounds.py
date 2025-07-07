"""Sound generation and management for Neon Invaders."""

import pygame
import numpy as np
from config import SOUND_ENABLED, SOUND_VOLUME


class SoundManager:
    """Manages all game sounds."""

    def __init__(self):
        """Initialize sound manager."""
        if not SOUND_ENABLED:
            return

        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        pygame.mixer.set_num_channels(8)

        # Generate and cache all sounds
        self.sounds = {
            "player_shoot": self._generate_laser_sound(),
            "enemy_shoot": self._generate_enemy_laser_sound(),
            "explosion": self._generate_explosion_sound(),
            "bonus_collect": self._generate_bonus_sound(),
            "wave_clear": self._generate_wave_clear_sound(),
            "game_over": self._generate_game_over_sound(),
            "power_up": self._generate_power_up_sound(),
            "shield_hit": self._generate_shield_hit_sound(),
        }

        # Set volume for all sounds
        for sound in self.sounds.values():
            sound.set_volume(SOUND_VOLUME)

    def play(self, sound_name: str):
        """Play a sound by name."""
        if not SOUND_ENABLED:
            return

        if sound_name in self.sounds:
            self.sounds[sound_name].play()

    def _generate_tone(
        self, frequency: float, duration: float, sample_rate: int = 22050
    ) -> np.ndarray:
        """Generate a pure sine wave tone."""
        frames = int(duration * sample_rate)
        arr = np.zeros(frames)
        for i in range(frames):
            arr[i] = np.sin(2 * np.pi * frequency * i / sample_rate)
        return arr

    def _generate_noise(self, duration: float, sample_rate: int = 22050) -> np.ndarray:
        """Generate white noise."""
        frames = int(duration * sample_rate)
        return np.random.normal(0, 0.1, frames)

    def _apply_envelope(
        self,
        sound: np.ndarray,
        attack: float = 0.01,
        decay: float = 0.1,
        sustain: float = 0.3,
        release: float = 0.2,
    ) -> np.ndarray:
        """Apply ADSR envelope to sound."""
        total_frames = len(sound)
        attack_frames = int(attack * total_frames)
        decay_frames = int(decay * total_frames)
        sustain_frames = int(sustain * total_frames)
        release_frames = total_frames - attack_frames - decay_frames - sustain_frames

        envelope = np.ones(total_frames)

        # Attack
        envelope[:attack_frames] = np.linspace(0, 1, attack_frames)

        # Decay
        decay_start = attack_frames
        decay_end = decay_start + decay_frames
        envelope[decay_start:decay_end] = np.linspace(1, 0.7, decay_frames)

        # Sustain
        sustain_start = decay_end
        sustain_end = sustain_start + sustain_frames
        envelope[sustain_start:sustain_end] = 0.7

        # Release
        release_start = sustain_end
        envelope[release_start:] = np.linspace(0.7, 0, release_frames)

        return sound * envelope

    def _generate_laser_sound(self) -> pygame.mixer.Sound:
        """Generate player laser sound - high pitched descending beep."""
        duration = 0.15
        sample_rate = 22050

        # Descending frequency sweep
        t = np.linspace(0, duration, int(sample_rate * duration))
        frequency = np.linspace(800, 400, len(t))

        sound = np.sin(2 * np.pi * frequency * t)
        sound = self._apply_envelope(
            sound, attack=0.01, decay=0.02, sustain=0.4, release=0.57
        )

        # Add slight resonance
        sound += 0.3 * np.sin(4 * np.pi * frequency * t)

        # Normalize and convert to 16-bit
        sound = np.clip(sound * 0.3, -1, 1)
        sound = (sound * 32767).astype(np.int16)

        # Create stereo sound
        stereo_sound = np.zeros((len(sound), 2), dtype=np.int16)
        stereo_sound[:, 0] = sound
        stereo_sound[:, 1] = sound

        return pygame.sndarray.make_sound(stereo_sound)

    def _generate_enemy_laser_sound(self) -> pygame.mixer.Sound:
        """Generate enemy laser sound - lower pitched ascending beep."""
        duration = 0.2
        sample_rate = 22050

        # Ascending frequency sweep
        t = np.linspace(0, duration, int(sample_rate * duration))
        frequency = np.linspace(200, 400, len(t))

        sound = np.sin(2 * np.pi * frequency * t)
        sound = self._apply_envelope(
            sound, attack=0.05, decay=0.05, sustain=0.3, release=0.6
        )

        # Add some buzz
        sound += 0.2 * np.sin(8 * np.pi * frequency * t)

        # Normalize and convert to 16-bit
        sound = np.clip(sound * 0.25, -1, 1)
        sound = (sound * 32767).astype(np.int16)

        # Create stereo sound
        stereo_sound = np.zeros((len(sound), 2), dtype=np.int16)
        stereo_sound[:, 0] = sound
        stereo_sound[:, 1] = sound

        return pygame.sndarray.make_sound(stereo_sound)

    def _generate_explosion_sound(self) -> pygame.mixer.Sound:
        """Generate explosion sound - noise burst with low frequency rumble."""
        duration = 0.4
        sample_rate = 22050

        # White noise
        noise = self._generate_noise(duration, sample_rate)

        # Low frequency rumble
        t = np.linspace(0, duration, int(sample_rate * duration))
        rumble = self._generate_tone(50, duration, sample_rate) * 0.5
        rumble += self._generate_tone(35, duration, sample_rate) * 0.3

        # Combine noise and rumble
        sound = noise * 0.6 + rumble

        # Apply explosive envelope
        envelope = np.exp(-t * 8)  # Quick decay
        sound = sound * envelope

        # Normalize and convert to 16-bit
        sound = np.clip(sound * 0.5, -1, 1)
        sound = (sound * 32767).astype(np.int16)

        # Create stereo sound
        stereo_sound = np.zeros((len(sound), 2), dtype=np.int16)
        stereo_sound[:, 0] = sound
        stereo_sound[:, 1] = sound

        return pygame.sndarray.make_sound(stereo_sound)

    def _generate_bonus_sound(self) -> pygame.mixer.Sound:
        """Generate bonus collection sound - ascending arpeggio."""
        duration = 0.3
        sample_rate = 22050

        # Three note ascending arpeggio
        note_duration = duration / 3
        t1 = np.linspace(0, note_duration, int(sample_rate * note_duration))

        # C, E, G notes
        note1 = self._generate_tone(523.25, note_duration, sample_rate)  # C5
        note2 = self._generate_tone(659.25, note_duration, sample_rate)  # E5
        note3 = self._generate_tone(783.99, note_duration, sample_rate)  # G5

        # Apply envelope to each note
        note1 = self._apply_envelope(
            note1, attack=0.1, decay=0.2, sustain=0.4, release=0.3
        )
        note2 = self._apply_envelope(
            note2, attack=0.1, decay=0.2, sustain=0.4, release=0.3
        )
        note3 = self._apply_envelope(
            note3, attack=0.1, decay=0.2, sustain=0.4, release=0.3
        )

        # Combine notes
        sound = np.concatenate([note1, note2, note3])

        # Normalize and convert to 16-bit
        sound = np.clip(sound * 0.3, -1, 1)
        sound = (sound * 32767).astype(np.int16)

        # Create stereo sound
        stereo_sound = np.zeros((len(sound), 2), dtype=np.int16)
        stereo_sound[:, 0] = sound
        stereo_sound[:, 1] = sound

        return pygame.sndarray.make_sound(stereo_sound)

    def _generate_wave_clear_sound(self) -> pygame.mixer.Sound:
        """Generate wave clear sound - triumphant fanfare."""
        duration = 0.8
        sample_rate = 22050

        t = np.linspace(0, duration, int(sample_rate * duration))

        # Major chord progression
        sound = np.zeros(len(t))

        # Add harmonics for richness
        frequencies = [261.63, 329.63, 392.00, 523.25]  # C major chord
        for i, freq in enumerate(frequencies):
            amplitude = 0.3 / (i + 1)
            sound += amplitude * np.sin(2 * np.pi * freq * t)

        # Apply envelope
        sound = self._apply_envelope(
            sound, attack=0.1, decay=0.1, sustain=0.6, release=0.2
        )

        # Normalize and convert to 16-bit
        sound = np.clip(sound * 0.4, -1, 1)
        sound = (sound * 32767).astype(np.int16)

        # Create stereo sound
        stereo_sound = np.zeros((len(sound), 2), dtype=np.int16)
        stereo_sound[:, 0] = sound
        stereo_sound[:, 1] = sound

        return pygame.sndarray.make_sound(stereo_sound)

    def _generate_game_over_sound(self) -> pygame.mixer.Sound:
        """Generate game over sound - descending sad tones."""
        duration = 1.0
        sample_rate = 22050

        # Four descending notes
        note_duration = duration / 4

        # Descending minor progression
        frequencies = [392.00, 349.23, 311.13, 261.63]  # G4, F4, Eb4, C4

        sound = np.array([])
        for freq in frequencies:
            note = self._generate_tone(freq, note_duration, sample_rate)
            note = self._apply_envelope(
                note, attack=0.05, decay=0.1, sustain=0.7, release=0.15
            )
            sound = np.concatenate([sound, note])

        # Normalize and convert to 16-bit
        sound = np.clip(sound * 0.3, -1, 1)
        sound = (sound * 32767).astype(np.int16)

        # Create stereo sound
        stereo_sound = np.zeros((len(sound), 2), dtype=np.int16)
        stereo_sound[:, 0] = sound
        stereo_sound[:, 1] = sound

        return pygame.sndarray.make_sound(stereo_sound)

    def _generate_power_up_sound(self) -> pygame.mixer.Sound:
        """Generate power-up activation sound - energetic sweep up."""
        duration = 0.4
        sample_rate = 22050

        t = np.linspace(0, duration, int(sample_rate * duration))

        # Frequency sweep from low to high
        frequency = np.linspace(200, 1200, len(t))

        # Generate sweep with harmonics
        sound = np.sin(2 * np.pi * frequency * t)
        sound += 0.3 * np.sin(2 * np.pi * frequency * 2 * t)  # Octave
        sound += 0.2 * np.sin(2 * np.pi * frequency * 3 * t)  # Fifth

        # Apply envelope
        sound = self._apply_envelope(
            sound, attack=0.2, decay=0.1, sustain=0.5, release=0.2
        )

        # Add shimmer effect
        shimmer = np.sin(2 * np.pi * 50 * t) * 0.1
        sound = sound * (1 + shimmer)

        # Normalize and convert to 16-bit
        sound = np.clip(sound * 0.3, -1, 1)
        sound = (sound * 32767).astype(np.int16)

        # Create stereo sound with slight delay for width
        stereo_sound = np.zeros((len(sound) + 100, 2), dtype=np.int16)
        stereo_sound[: len(sound), 0] = sound
        stereo_sound[100 : len(sound) + 100, 1] = sound

        return pygame.sndarray.make_sound(stereo_sound[: len(sound)])

    def _generate_shield_hit_sound(self) -> pygame.mixer.Sound:
        """Generate shield hit sound - metallic clang."""
        duration = 0.2
        sample_rate = 22050

        t = np.linspace(0, duration, int(sample_rate * duration))

        # Metallic sound with multiple harmonics
        sound = np.zeros(len(t))
        base_freq = 800

        # Add dissonant harmonics for metallic sound
        harmonics = [1, 1.6, 2.3, 3.7, 4.9]
        amplitudes = [0.5, 0.3, 0.2, 0.15, 0.1]

        for harmonic, amplitude in zip(harmonics, amplitudes):
            sound += amplitude * np.sin(2 * np.pi * base_freq * harmonic * t)

        # Quick attack and decay for impact
        envelope = np.exp(-t * 20)
        sound = sound * envelope

        # Add slight ring modulation for metallic effect
        ring = np.sin(2 * np.pi * 130 * t)
        sound = sound * (1 + 0.3 * ring)

        # Normalize and convert to 16-bit
        sound = np.clip(sound * 0.4, -1, 1)
        sound = (sound * 32767).astype(np.int16)

        # Create stereo sound
        stereo_sound = np.zeros((len(sound), 2), dtype=np.int16)
        stereo_sound[:, 0] = sound
        stereo_sound[:, 1] = sound

        return pygame.sndarray.make_sound(stereo_sound)


# Global sound manager instance
sound_manager = SoundManager()
