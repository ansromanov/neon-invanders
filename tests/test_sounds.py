"""Unit tests for sound generation and management."""

import os
import sys
from unittest.mock import MagicMock, patch

import numpy as np
import pygame
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import SOUND_VOLUME
from src.sounds import SoundManager


class TestSoundManager:
    """Test cases for SoundManager functionality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        pygame.init()
        pygame.mixer.quit()  # Quit first to ensure clean state
        yield
        pygame.mixer.quit()
        pygame.quit()

    @patch("src.sounds.SOUND_ENABLED", True)
    @patch("pygame.mixer.init")
    @patch("pygame.mixer.set_num_channels")
    def test_sound_manager_initialization_enabled(
        self, mock_set_channels, mock_mixer_init
    ):
        """Test sound manager initialization when sound is enabled."""
        with (
            patch.object(SoundManager, "_generate_laser_sound") as mock_laser,
            patch.object(
                SoundManager, "_generate_enemy_laser_sound"
            ) as mock_enemy_laser,
            patch.object(SoundManager, "_generate_explosion_sound") as mock_explosion,
            patch.object(SoundManager, "_generate_bonus_sound") as mock_bonus,
            patch.object(SoundManager, "_generate_wave_clear_sound") as mock_wave_clear,
            patch.object(SoundManager, "_generate_game_over_sound") as mock_game_over,
            patch.object(SoundManager, "_generate_power_up_sound") as mock_power_up,
            patch.object(SoundManager, "_generate_shield_hit_sound") as mock_shield_hit,
        ):
            # Create mock sounds
            mock_sounds = {
                name: MagicMock()
                for name in [
                    "laser",
                    "enemy_laser",
                    "explosion",
                    "bonus",
                    "wave_clear",
                    "game_over",
                    "power_up",
                    "shield_hit",
                ]
            }

            mock_laser.return_value = mock_sounds["laser"]
            mock_enemy_laser.return_value = mock_sounds["enemy_laser"]
            mock_explosion.return_value = mock_sounds["explosion"]
            mock_bonus.return_value = mock_sounds["bonus"]
            mock_wave_clear.return_value = mock_sounds["wave_clear"]
            mock_game_over.return_value = mock_sounds["game_over"]
            mock_power_up.return_value = mock_sounds["power_up"]
            mock_shield_hit.return_value = mock_sounds["shield_hit"]

            sound_manager = SoundManager()

            # Check mixer initialization
            mock_mixer_init.assert_called_once_with(
                frequency=22050, size=-16, channels=2, buffer=512
            )
            mock_set_channels.assert_called_once_with(8)

            # Check sounds dictionary
            assert hasattr(sound_manager, "sounds")
            assert isinstance(sound_manager.sounds, dict)
            assert len(sound_manager.sounds) == 8

            # Check all sounds have volume set
            for sound in mock_sounds.values():
                sound.set_volume.assert_called_once_with(SOUND_VOLUME)

    @patch("src.sounds.SOUND_ENABLED", False)
    def test_sound_manager_initialization_disabled(self):
        """Test sound manager initialization when sound is disabled."""
        sound_manager = SoundManager()

        # When sound is disabled, nothing should be initialized
        assert not hasattr(sound_manager, "sounds") or sound_manager.sounds == {}

    @patch("src.sounds.SOUND_ENABLED", True)
    @patch("pygame.mixer.init")
    @patch("pygame.mixer.set_num_channels")
    @patch("pygame.sndarray.make_sound")
    def test_play_existing_sound_enabled(
        self, mock_make_sound, mock_set_channels, mock_mixer_init
    ):
        """Test playing an existing sound when enabled."""
        mock_sound = MagicMock()
        mock_make_sound.return_value = mock_sound

        sound_manager = SoundManager()

        # Test playing a sound
        sound_manager.play("player_shoot")

        mock_sound.play.assert_called_once()

    def test_play_sound_disabled(self):
        """Test playing sound when sound is disabled."""
        # Test with patching at the module level since play() imports SOUND_ENABLED
        with (
            patch("src.sounds.SOUND_ENABLED", False),
            patch("src.config.SOUND_ENABLED", False),
        ):
            sound_manager = SoundManager()

            # Should not raise any exception
            sound_manager.play("any_sound")

            # When sound is disabled, sounds dict should not exist
            assert not hasattr(sound_manager, "sounds")

    @patch("src.sounds.SOUND_ENABLED", True)
    @patch("pygame.mixer.init")
    @patch("pygame.mixer.set_num_channels")
    @patch("pygame.sndarray.make_sound")
    def test_play_non_existing_sound(
        self, mock_make_sound, mock_set_channels, mock_mixer_init
    ):
        """Test playing a non-existing sound doesn't crash."""
        mock_sound = MagicMock()
        mock_make_sound.return_value = mock_sound

        sound_manager = SoundManager()

        # Should not raise any exception
        sound_manager.play("non_existing_sound")

        # The non-existing sound should not call play
        mock_sound.play.assert_not_called()

    def test_generate_tone(self):
        """Test tone generation."""
        sound_manager = SoundManager()
        frequency = 440  # A4
        duration = 0.1
        sample_rate = 22050

        tone = sound_manager._generate_tone(frequency, duration, sample_rate)

        # Check output shape
        expected_frames = int(duration * sample_rate)
        assert len(tone) == expected_frames

        # Check it's a sine wave (values between -1 and 1)
        assert np.all(tone >= -1) and np.all(tone <= 1)

    def test_generate_noise(self):
        """Test noise generation."""
        sound_manager = SoundManager()
        duration = 0.1
        sample_rate = 22050

        noise = sound_manager._generate_noise(duration, sample_rate)

        # Check output shape
        expected_frames = int(duration * sample_rate)
        assert len(noise) == expected_frames

        # Check it's noise (statistical properties)
        assert -0.5 < np.mean(noise) < 0.5  # Mean should be close to 0
        assert 0.05 < np.std(noise) < 0.15  # Standard deviation around 0.1

    def test_apply_envelope(self):
        """Test ADSR envelope application."""
        sound_manager = SoundManager()

        # Create a constant signal
        signal = np.ones(1000)

        # Apply envelope
        enveloped = sound_manager._apply_envelope(
            signal, attack=0.1, decay=0.2, sustain=0.5, release=0.2
        )

        # Check shape preserved
        assert len(enveloped) == len(signal)

        # Check envelope properties
        # Attack: should start at 0 and rise
        assert enveloped[0] < 0.1

        # Peak should be around attack end
        attack_end = int(0.1 * len(signal))
        assert 0.9 < enveloped[attack_end] <= 1.0

        # Sustain level should be 0.7
        sustain_start = int(0.3 * len(signal))
        sustain_end = int(0.8 * len(signal))
        assert np.all(np.abs(enveloped[sustain_start:sustain_end] - 0.7) < 0.1)

        # Release: should end near 0
        assert enveloped[-1] < 0.1

    @patch("pygame.sndarray.make_sound")
    def test_generate_laser_sound(self, mock_make_sound):
        """Test laser sound generation."""
        mock_sound = MagicMock()
        mock_make_sound.return_value = mock_sound

        # Create sound manager without initialization to test individual method
        sound_manager = SoundManager.__new__(SoundManager)
        result = sound_manager._generate_laser_sound()

        # Check that make_sound was called
        mock_make_sound.assert_called_once()

        # Check the input to make_sound
        call_args = mock_make_sound.call_args[0][0]
        assert isinstance(call_args, np.ndarray)
        assert call_args.dtype == np.int16
        assert call_args.shape[1] == 2  # Stereo

        assert result == mock_sound

    @patch("pygame.sndarray.make_sound")
    def test_generate_enemy_laser_sound(self, mock_make_sound):
        """Test enemy laser sound generation."""
        mock_sound = MagicMock()
        mock_make_sound.return_value = mock_sound

        sound_manager = SoundManager.__new__(SoundManager)
        result = sound_manager._generate_enemy_laser_sound()

        mock_make_sound.assert_called_once()
        call_args = mock_make_sound.call_args[0][0]
        assert isinstance(call_args, np.ndarray)
        assert call_args.dtype == np.int16
        assert call_args.shape[1] == 2  # Stereo

        assert result == mock_sound

    @patch("pygame.sndarray.make_sound")
    def test_generate_explosion_sound(self, mock_make_sound):
        """Test explosion sound generation."""
        mock_sound = MagicMock()
        mock_make_sound.return_value = mock_sound

        sound_manager = SoundManager.__new__(SoundManager)
        result = sound_manager._generate_explosion_sound()

        mock_make_sound.assert_called_once()
        call_args = mock_make_sound.call_args[0][0]
        assert isinstance(call_args, np.ndarray)
        assert call_args.dtype == np.int16
        assert call_args.shape[1] == 2  # Stereo

        assert result == mock_sound

    @patch("pygame.sndarray.make_sound")
    def test_generate_bonus_sound(self, mock_make_sound):
        """Test bonus collection sound generation."""
        mock_sound = MagicMock()
        mock_make_sound.return_value = mock_sound

        sound_manager = SoundManager.__new__(SoundManager)
        result = sound_manager._generate_bonus_sound()

        mock_make_sound.assert_called_once()
        call_args = mock_make_sound.call_args[0][0]
        assert isinstance(call_args, np.ndarray)
        assert call_args.dtype == np.int16
        assert call_args.shape[1] == 2  # Stereo

        assert result == mock_sound

    @patch("pygame.sndarray.make_sound")
    def test_generate_wave_clear_sound(self, mock_make_sound):
        """Test wave clear sound generation."""
        mock_sound = MagicMock()
        mock_make_sound.return_value = mock_sound

        sound_manager = SoundManager.__new__(SoundManager)
        result = sound_manager._generate_wave_clear_sound()

        mock_make_sound.assert_called_once()
        assert result == mock_sound

    @patch("pygame.sndarray.make_sound")
    def test_generate_game_over_sound(self, mock_make_sound):
        """Test game over sound generation."""
        mock_sound = MagicMock()
        mock_make_sound.return_value = mock_sound

        sound_manager = SoundManager.__new__(SoundManager)
        result = sound_manager._generate_game_over_sound()

        mock_make_sound.assert_called_once()
        assert result == mock_sound

    @patch("pygame.sndarray.make_sound")
    def test_generate_power_up_sound(self, mock_make_sound):
        """Test power-up sound generation."""
        mock_sound = MagicMock()
        mock_make_sound.return_value = mock_sound

        sound_manager = SoundManager.__new__(SoundManager)
        result = sound_manager._generate_power_up_sound()

        mock_make_sound.assert_called_once()
        assert result == mock_sound

    @patch("pygame.sndarray.make_sound")
    def test_generate_shield_hit_sound(self, mock_make_sound):
        """Test shield hit sound generation."""
        mock_sound = MagicMock()
        mock_make_sound.return_value = mock_sound

        sound_manager = SoundManager.__new__(SoundManager)
        result = sound_manager._generate_shield_hit_sound()

        mock_make_sound.assert_called_once()
        assert result == mock_sound

    def test_sound_names_mapping(self):
        """Test that sound names match expected game events."""
        expected_sounds = {
            "player_shoot",
            "enemy_shoot",
            "explosion",
            "bonus_collect",
            "wave_clear",
            "game_over",
            "power_up",
            "shield_hit",
        }

        with (
            patch("src.sounds.SOUND_ENABLED", True),
            patch("pygame.mixer.init"),
            patch("pygame.mixer.set_num_channels"),
            patch("pygame.sndarray.make_sound", return_value=MagicMock()),
        ):
            sound_manager = SoundManager()

            # Check all expected sounds are present
            assert set(sound_manager.sounds.keys()) == expected_sounds

    @patch("src.sounds.sound_manager", MagicMock())
    def test_module_level_sound_manager_exists(self):
        """Test that the module-level sound_manager is available."""
        from src import sounds

        # The sound_manager should exist
        assert hasattr(sounds, "sound_manager")
        assert isinstance(sounds.sound_manager, (SoundManager, MagicMock))
