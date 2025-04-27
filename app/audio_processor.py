"""
Модуль audio_processor.py содержит класс AudioProcessor, предназначенный для предобработки аудиофайлов 
перед их использованием в системах распознавания речи. Класс предоставляет методы для конвертации 
аудио в формат WAV с частотой дискретизации 16 кГц, нормализации уровня громкости, 
добавления тишины в начало записи, а также для удаления временных файлов, созданных в процессе обработки. 
"""

import os
import subprocess
import tempfile
import uuid
from typing import Dict, Tuple

# Импорт классов и функций из других модулей
from .utils import logger

class AudioProcessor:
    """Класс для предобработки аудиофайлов перед распознаванием."""
    
    def __init__(self, config: Dict):
        """
        Инициализация обработчика аудио.
        
        Args:
            config: Словарь с параметрами конфигурации.
        """
        self.config = config
        self.norm_level = config.get("norm_level", "-0.5")
        self.compand_params = config.get("compand_params", "0.3,1 -90,-90,-70,-70,-60,-20,0,0 -5 0 0.2")
    
    def convert_to_wav(self, input_path: str) -> str:
        """
        Конвертация входного аудиофайла в WAV формат с частотой дискретизации 16 кГц.
        
        Args:
            input_path: Путь к исходному аудиофайлу.
            
        Returns:
            Путь к сконвертированному WAV-файлу.
        """

        audio_rate = self.config["audio_rate"]

        # Проверка расширения файла
        if input_path.lower().endswith('.wav'):
            # Проверяем, нужно ли преобразовывать WAV-файл (например, если частота не 16 кГц)
            try:
                info = subprocess.check_output(['soxi', input_path]).decode()
                if f'{audio_rate} Hz' in info:
                    logger.info(f"Файл {input_path} уже в формате WAV с частотой {audio_rate} Гц")
                    return input_path
            except subprocess.CalledProcessError as e:
                logger.warning(f"Не удалось получить информацию о WAV-файле {input_path}: {e}")
                # Продолжаем конвертацию, чтобы быть уверенными в формате
            except FileNotFoundError:
                logger.warning("Command 'soxi' not found. Make sure SOX is installed and in your PATH.")
                # Continue conversion without checking sample rate

        # Создаем временный файл для WAV
        temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(temp_dir, f"{uuid.uuid4()}.wav")
        
        # Команда для конвертации
        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel", "warning",
            "-i", input_path,
            "-ar", f"{audio_rate}",
            "-ac", "1",  # Монофонический звук
            output_path
        ]
        
        logger.info(f"Конвертация в WAV: {' '.join(cmd)}")
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"Файл конвертирован в WAV: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            error_msg = f"Ошибка при конвертации в WAV: {e}"
            if e.stderr:
                error_msg += f" - {e.stderr.decode('utf-8', errors='replace')}"
            logger.error(error_msg)
            raise RuntimeError(f"Failed to convert audio file: {error_msg}")
        except FileNotFoundError:
            error_msg = "Command 'ffmpeg' not found. Make sure ffmpeg is installed and in your PATH."
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def normalize_audio(self, input_path: str) -> str:
        """
        Нормализация аудиофайла с использованием sox.
        
        Args:
            input_path: Путь к WAV-файлу.
            
        Returns:
            Путь к нормализованному WAV-файлу.
        """
        # Создаем временный файл для нормализованного аудио
        temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(temp_dir, f"{uuid.uuid4()}_normalized.wav")
        
        # Команда для нормализации аудио с помощью sox
        cmd = [
            "sox", 
            input_path, 
            output_path, 
            "norm", self.norm_level,
            "compand"
        ] + self.compand_params.split()
        
        logger.info(f"Нормализация аудио: {' '.join(cmd)}")
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"Аудио нормализовано: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            error_msg = f"Ошибка при нормализации аудио: {e}"
            if e.stderr:
                error_msg += f" - {e.stderr.decode('utf-8', errors='replace')}"
            logger.error(error_msg)
            raise RuntimeError(f"Failed to normalize audio: {error_msg}")
        except FileNotFoundError:
            error_msg = "Command 'sox' not found. Make sure SOX is installed and in your PATH."
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def add_silence(self, input_path: str) -> str:
        """
        Добавляет тишину в начало аудиофайла.
        
        Args:
            input_path: Путь к аудиофайлу.
            
        Returns:
            Путь к аудиофайлу с добавленной тишиной.
        """
        # Создаем временный файл
        temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(temp_dir, f"{uuid.uuid4()}_silence.wav")
        
        # Команда для добавления тишины в начало файла
        cmd = [
            "sox",
            input_path,
            output_path,
            "pad", "2.0", "1.0"  # Добавление тишины в начале и в конце (секунды)
        ]
        
        logger.info(f"Добавление тишины: {' '.join(cmd)}")
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"Тишина добавлена: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            error_msg = f"Ошибка при добавлении тишины: {e}"
            if e.stderr:
                error_msg += f" - {e.stderr.decode('utf-8', errors='replace')}"
            logger.error(error_msg)
            raise RuntimeError(f"Failed to add silence to audio: {error_msg}")
        except FileNotFoundError:
            error_msg = "Command 'sox' not found. Make sure SOX is installed and in your PATH."
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def cleanup_temp_files(self, file_paths: list):
        """
        Удаление временных файлов и директорий.
        
        Args:
            file_paths: Список путей к временным файлам.
        """
        for path in file_paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
                    logger.debug(f"Удален временный файл: {path}")
                    
                    # Попытка удалить директорию, если она пуста
                    temp_dir = os.path.dirname(path)
                    if os.path.exists(temp_dir) and not os.listdir(temp_dir):
                        os.rmdir(temp_dir)
                        logger.debug(f"Удалена временная директория: {temp_dir}")
            except Exception as e:
                logger.warning(f"Не удалось очистить временный файл {path}: {e}")
    
    def process_audio(self, input_path: str) -> Tuple[str, list]:
        """
        Полная обработка аудиофайла: конвертация, нормализация и добавление тишины.
        
        Args:
            input_path: Путь к исходному аудиофайлу.
            
        Returns:
            Кортеж: (путь к обработанному файлу, список временных файлов для удаления)
        """
        temp_files = []
        
        try:
            # Конвертация в WAV
            wav_path = self.convert_to_wav(input_path)
            if wav_path != input_path:  # Если был создан временный файл
                temp_files.append(wav_path)
            
            # Нормализация
            normalized_path = self.normalize_audio(wav_path)
            temp_files.append(normalized_path)
            
            # Добавление тишины
            silence_path = self.add_silence(normalized_path)
            temp_files.append(silence_path)
            
            return silence_path, temp_files
        
        except Exception as e:
            logger.error(f"Ошибка при обработке аудио {input_path}: {e}")
            self.cleanup_temp_files(temp_files)
            raise
