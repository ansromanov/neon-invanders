"""Sound generation and management for Neon Invaders."""

import numpy as np
import pygame

from .config import SOUND_ENABLED, SOUND_VOLUME


class SoundManager:
    """Manages all game sounds."""

    def __init__(self):
        """Initialize sound manager."""
        self.sound_enabled = SOUND_ENABLED
        self.music_playing = False
        self.music_channels = []
        self.current_theme = 0
        self.all_music_themes = []

        if not self.sound_enabled:
            return

        self.sounds = {}

        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        pygame.mixer.set_num_channels(12)  # Increased for music channels

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

        # Generate background music
        self._generate_all_music_themes()

    def play(self, sound_name: str):
        """Play a sound by name."""
        if not self.sound_enabled:
            return

        if sound_name in self.sounds:
            self.sounds[sound_name].play()

    def play_music(self, theme_index: int = 0):
        """Start playing background music with specified theme."""
        if not self.sound_enabled or not self.all_music_themes:
            return

        # Stop current music if playing
        if self.music_playing:
            self.stop_music()

        # Select theme based on index
        self.current_theme = theme_index % 3  # We have 3 themes
        current_tracks = self.all_music_themes[self.current_theme]

        # Play each track on its own channel with looping
        for i, track in enumerate(current_tracks):
            channel_index = 8 + i
            # Ensure we don't exceed available channels
            if channel_index < pygame.mixer.get_num_channels():
                channel = pygame.mixer.Channel(
                    channel_index
                )  # Use channels 8, 9, 10 for music
                channel.play(track, loops=-1)  # Loop indefinitely
                channel.set_volume(SOUND_VOLUME * 0.3)  # Music quieter than SFX
                self.music_channels.append(channel)

        self.music_playing = True

    def stop_music(self):
        """Stop playing background music."""
        for channel in self.music_channels:
            channel.stop()
        self.music_channels.clear()
        self.music_playing = False

    def set_music_volume(self, volume: float):
        """Set volume for background music."""
        for channel in self.music_channels:
            channel.set_volume(volume * 0.3)  # Keep music quieter than SFX

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
        release: float = 0.2,  # noqa: ARG002
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

        for harmonic, amplitude in zip(harmonics, amplitudes, strict=False):
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

    def _generate_all_music_themes(self):
        """Generate all music themes for different levels."""
        self.all_music_themes = []

        # Theme 1: Original Synthwave (Levels 1-3)
        self.all_music_themes.append(self._generate_theme_1())

        # Theme 2: Dark Techno (Levels 4-6)
        self.all_music_themes.append(self._generate_theme_2())

        # Theme 3: Epic Boss Battle (Levels 7+)
        self.all_music_themes.append(self._generate_theme_3())

    def _generate_theme_1(self) -> list[pygame.mixer.Sound]:
        """Generate original synthwave theme."""
        # Music parameters
        bpm = 120
        beat_duration = 60.0 / bpm
        bar_duration = beat_duration * 4
        loop_duration = bar_duration * 4  # 4-bar loop
        sample_rate = 22050

        return [
            self._generate_bass_track(loop_duration, sample_rate, "theme1"),
            self._generate_lead_track(loop_duration, sample_rate, "theme1"),
            self._generate_arpeggio_track(loop_duration, sample_rate, "theme1"),
        ]

    def _generate_theme_2(self) -> list[pygame.mixer.Sound]:
        """Generate dark techno theme."""
        # Faster tempo for intensity
        bpm = 140
        beat_duration = 60.0 / bpm
        bar_duration = beat_duration * 4
        loop_duration = bar_duration * 4
        sample_rate = 22050

        return [
            self._generate_bass_track(loop_duration, sample_rate, "theme2"),
            self._generate_lead_track(loop_duration, sample_rate, "theme2"),
            self._generate_arpeggio_track(loop_duration, sample_rate, "theme2"),
        ]

    def _generate_theme_3(self) -> list[pygame.mixer.Sound]:
        """Generate epic boss battle theme."""
        # Even faster for epic feel
        bpm = 160
        beat_duration = 60.0 / bpm
        bar_duration = beat_duration * 4
        loop_duration = bar_duration * 4
        sample_rate = 22050

        return [
            self._generate_bass_track(loop_duration, sample_rate, "theme3"),
            self._generate_lead_track(loop_duration, sample_rate, "theme3"),
            self._generate_arpeggio_track(loop_duration, sample_rate, "theme3"),
        ]

    def _generate_bass_track(
        self, duration: float, sample_rate: int, theme: str = "theme1"
    ) -> pygame.mixer.Sound:
        """Generate bass track for different themes."""
        frames = int(duration * sample_rate)
        t = np.linspace(0, duration, frames)
        sound = np.zeros(frames)

        if theme == "theme1":
            # Original synthwave bassline
            bass_pattern = [
                (55.0, 0.5),  # A1
                (55.0, 0.5),  # A1
                (82.41, 0.5),  # E2
                (55.0, 0.5),  # A1
                (65.41, 0.5),  # C2
                (65.41, 0.5),  # C2
                (73.42, 0.5),  # D2
                (82.41, 0.5),  # E2
            ]
        elif theme == "theme2":
            # Dark techno bassline - lower and more aggressive
            bass_pattern = [
                (41.20, 0.25),  # E1
                (41.20, 0.25),  # E1
                (43.65, 0.25),  # F1
                (41.20, 0.25),  # E1
                (36.71, 0.5),  # D1
                (36.71, 0.5),  # D1
                (32.70, 0.5),  # C1
                (36.71, 0.5),  # D1
            ]
        else:  # theme3
            # Epic boss battle - dramatic and heavy
            bass_pattern = [
                (27.50, 0.75),  # A0
                (32.70, 0.25),  # C1
                (36.71, 0.5),  # D1
                (41.20, 0.5),  # E1
                (43.65, 0.5),  # F1
                (41.20, 0.5),  # E1
                (36.71, 0.5),  # D1
                (27.50, 0.5),  # A0
            ]

        # Create bass line
        current_time = 0
        for freq, note_duration in bass_pattern * 2:  # Repeat pattern twice
            note_frames = int(note_duration * sample_rate)
            if current_time + note_frames > frames:
                note_frames = frames - current_time

            # Generate bass note with saw wave for that analog feel
            note_t = t[current_time : current_time + note_frames]
            # Saw wave
            note = 2 * (note_t * freq % 1) - 1
            # Add sub bass sine wave
            note += 0.5 * np.sin(2 * np.pi * freq * note_t)

            # Apply envelope
            envelope = np.ones(len(note))
            attack_frames = int(0.01 * sample_rate)
            release_frames = int(0.05 * sample_rate)
            if len(note) > attack_frames:
                envelope[:attack_frames] = np.linspace(0, 1, attack_frames)
            if len(note) > release_frames:
                envelope[-release_frames:] = np.linspace(1, 0, release_frames)

            sound[current_time : current_time + note_frames] = note * envelope * 0.3
            current_time += note_frames

        # Apply low-pass filter effect (simple averaging)
        filtered = np.convolve(sound, np.ones(5) / 5, mode="same")

        # Normalize and convert
        filtered = np.clip(filtered, -1, 1)
        filtered = (filtered * 32767).astype(np.int16)

        # Create stereo
        stereo_sound = np.zeros((len(filtered), 2), dtype=np.int16)
        stereo_sound[:, 0] = filtered
        stereo_sound[:, 1] = filtered

        return pygame.sndarray.make_sound(stereo_sound)

    def _generate_lead_track(
        self, duration: float, sample_rate: int, theme: str = "theme1"
    ) -> pygame.mixer.Sound:
        """Generate lead melody track for different themes."""
        frames = int(duration * sample_rate)
        t = np.linspace(0, duration, frames)
        sound = np.zeros(frames)

        if theme == "theme1":
            # Original synthwave melody
            lead_pattern = [
                (440.0, 0.75),  # A4
                (523.25, 0.25),  # C5
                (659.25, 0.5),  # E5
                (523.25, 0.5),  # C5
                (440.0, 1.0),  # A4
                (392.0, 0.5),  # G4
                (349.23, 0.5),  # F4
                (440.0, 1.0),  # A4
            ]
        elif theme == "theme2":
            # Dark techno lead - minor scale, mysterious
            lead_pattern = [
                (329.63, 0.5),  # E4
                (349.23, 0.5),  # F4
                (329.63, 0.5),  # E4
                (293.66, 0.5),  # D4
                (261.63, 1.0),  # C4
                (293.66, 0.5),  # D4
                (329.63, 0.5),  # E4
                (349.23, 1.0),  # F4
            ]
        else:  # theme3
            # Epic boss battle - heroic and dramatic
            lead_pattern = [
                (523.25, 0.5),  # C5
                (587.33, 0.5),  # D5
                (659.25, 0.5),  # E5
                (698.46, 0.5),  # F5
                (783.99, 1.0),  # G5
                (698.46, 0.5),  # F5
                (659.25, 0.5),  # E5
                (523.25, 1.0),  # C5
            ]

        # Create lead melody
        current_time = 0
        for freq, note_duration in lead_pattern:
            note_frames = int(note_duration * sample_rate)
            if current_time + note_frames > frames:
                note_frames = frames - current_time

            # Generate lead with detuned saw waves for that classic synth sound
            note_t = t[current_time : current_time + note_frames]
            # Two slightly detuned oscillators
            osc1 = 2 * (note_t * freq % 1) - 1
            osc2 = 2 * (note_t * (freq * 1.01) % 1) - 1
            note = (osc1 + osc2) * 0.5

            # Apply envelope with longer attack for smooth sound
            envelope = np.ones(len(note))
            attack_frames = int(0.05 * sample_rate)
            decay_frames = int(0.1 * sample_rate)
            release_frames = int(0.1 * sample_rate)

            if len(note) > attack_frames:
                envelope[:attack_frames] = np.linspace(0, 1, attack_frames)
            if len(note) > attack_frames + decay_frames:
                envelope[attack_frames : attack_frames + decay_frames] = np.linspace(
                    1, 0.7, decay_frames
                )
            if len(note) > release_frames:
                envelope[-release_frames:] = np.linspace(0.7, 0, release_frames)

            sound[current_time : current_time + note_frames] = note * envelope * 0.15
            current_time += note_frames

        # Apply vibrato for that synth feel
        vibrato_rate = 5  # Hz
        vibrato_depth = 0.02
        vibrato = 1 + vibrato_depth * np.sin(2 * np.pi * vibrato_rate * t)
        sound = sound * vibrato

        # Normalize and convert
        sound = np.clip(sound, -1, 1)
        sound = (sound * 32767).astype(np.int16)

        # Create stereo with slight panning
        stereo_sound = np.zeros((len(sound), 2), dtype=np.int16)
        stereo_sound[:, 0] = sound * 0.7  # Slightly left
        stereo_sound[:, 1] = sound * 0.3

        return pygame.sndarray.make_sound(stereo_sound)

    def _generate_arpeggio_track(
        self, duration: float, sample_rate: int, theme: str = "theme1"
    ) -> pygame.mixer.Sound:
        """Generate arpeggio track for different themes."""
        frames = int(duration * sample_rate)
        t = np.linspace(0, duration, frames)
        sound = np.zeros(frames)

        if theme == "theme1":
            # Original synthwave arpeggio
            arp_notes = [
                220.0,  # A3
                277.18,  # C#4
                329.63,  # E4
                440.0,  # A4
            ]
            note_multiplier = 1.0
        elif theme == "theme2":
            # Dark techno - minor arpeggio, faster
            arp_notes = [
                164.81,  # E3
                196.00,  # G3
                220.0,  # A3
                261.63,  # C4
            ]
            note_multiplier = 1.5  # Faster arpeggios
        else:  # theme3
            # Epic boss battle - dramatic sweeping arpeggios
            arp_notes = [
                130.81,  # C3
                164.81,  # E3
                196.00,  # G3
                261.63,  # C4
                329.63,  # E4
                392.00,  # G4
            ]
            note_multiplier = 2.0  # Even faster for intensity

        # Calculate note duration based on theme
        if theme == "theme1":
            bpm = 120
        elif theme == "theme2":
            bpm = 140
        else:
            bpm = 160

        sixteenth_duration = (60.0 / bpm) / 4 / note_multiplier

        # Create arpeggio
        current_time = 0
        note_index = 0
        while current_time < frames:
            note_frames = int(sixteenth_duration * sample_rate)
            if current_time + note_frames > frames:
                note_frames = frames - current_time

            freq = arp_notes[note_index % len(arp_notes)]
            note_t = t[current_time : current_time + note_frames]

            # Square wave with PWM for that classic sound
            pwm_width = 0.3 + 0.2 * np.sin(2 * np.pi * 0.5 * note_t)  # Slow PWM
            note = np.where((note_t * freq % 1) < pwm_width, 1, -1)

            # Quick envelope
            envelope = np.ones(len(note))
            attack_frames = int(0.005 * sample_rate)
            release_frames = int(0.02 * sample_rate)
            if len(note) > attack_frames:
                envelope[:attack_frames] = np.linspace(0, 1, attack_frames)
            if len(note) > release_frames:
                envelope[-release_frames:] = np.linspace(1, 0, release_frames)

            sound[current_time : current_time + note_frames] = note * envelope * 0.1
            current_time += note_frames
            note_index += 1

        # Add delay effect
        delay_time = int(0.375 * sample_rate)  # Dotted eighth delay
        delay_feedback = 0.4
        delayed = np.zeros_like(sound)
        if delay_time < len(sound):
            delayed[delay_time:] = sound[:-delay_time] * delay_feedback
            sound += delayed

        # Normalize and convert
        sound = np.clip(sound, -1, 1)
        sound = (sound * 32767).astype(np.int16)

        # Create stereo with wide panning
        stereo_sound = np.zeros((len(sound), 2), dtype=np.int16)
        # Pan arpeggio to the right
        stereo_sound[:, 0] = sound * 0.3
        stereo_sound[:, 1] = sound * 0.7

        return pygame.sndarray.make_sound(stereo_sound)


# Global sound manager instance
sound_manager = SoundManager()
