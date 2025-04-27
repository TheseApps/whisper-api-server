"""
Модуль transcriber_service.py содержит класс TranscriptionService,
который отвечает за обработку и транскрибацию аудиофайлов.
"""

import os
import uuid
import tempfile
import time
import librosa
from typing import Dict, Tuple

from .utils import logger
from .history_logger import HistoryLogger
from .audio_sources import AudioSource


class TranscriptionService:
    """Сервис для обработки и транскрибации аудиофайлов."""

    def __init__(self, transcriber, config: Dict):
        """
        Инициализация сервиса транскрибации.

        Args:
            transcriber: Экземпляр транскрайбера.
            config: Словарь с конфигурацией.
        """
        self.transcriber = transcriber
        self.config = config
        self.max_file_size_mb = self.config.get("max_file_size", 100)  # Default 100MB

        # Объект журналирования
        self.history = HistoryLogger(config)

    def get_audio_duration(self, file_path: str) -> float:
        """
        Определяет длительность аудиофайла в секундах.

        Args:
            file_path: Путь к аудиофайлу.

        Returns:
            Длительность в секундах.
        """
        try:
            y, sr = librosa.load(file_path, sr=None)
            duration = librosa.get_duration(y=y, sr=sr)
            return duration
        except Exception as e:
            logger.error(f"Ошибка при определении длительности файла: {e}")
            return 0.0

    def transcribe_from_source(self, source: AudioSource, params: Dict = None) -> Tuple[Dict, int]:
        """
        Транскрибирует аудиофайл из указанного источника.

        Args:
            source: Источник аудиофайла.
            params: Дополнительные параметры для транскрибации.

        Returns:
            Кортеж (JSON-ответ, HTTP-код).
        """
        # Получаем файл из источника
        file, filename, error = source.get_audio_file()

        # Обрабатываем ошибки получения файла
        if error:
            return {"error": error}, 400

        if not file:
            return {"error": "Failed to get audio file"}, 400

        # Извлекаем параметры из запроса, если они есть
        params = params or {}
        language = params.get('language', self.config.get('language', 'en'))
        temperature = float(params.get('temperature', 0.0))
        prompt = params.get('prompt', '')

        # Проверяем, запрошены ли временные метки
        return_timestamps = params.get('return_timestamps', self.config.get('return_timestamps', False))
        # Преобразуем строковое значение в булево, если необходимо
        if isinstance(return_timestamps, str):
            return_timestamps = return_timestamps.lower() in ('true', 't', 'yes', 'y', '1')

        # Временно изменяем настройку return_timestamps в транскрайбере
        original_return_timestamps = self.transcriber.return_timestamps
        self.transcriber.return_timestamps = return_timestamps

        # Сохраняем файл во временный файл
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, str(uuid.uuid4()) + "_" + os.path.basename(filename))
        
        try:
            file.save(temp_file_path)
            
            # Определяем длительность аудиофайла
            duration = self.get_audio_duration(temp_file_path)
    
            # Для файлов из внешних источников (URL, base64), закрываем их и выполняем очистку
            if hasattr(source, 'cleanup'):
                file.file.close()  # Закрываем файловый объект
                source.cleanup()  # Очищаем временные файлы источника
    
            try:
                start_time = time.time()
                result = self.transcriber.process_file(temp_file_path)
                processing_time = time.time() - start_time
    
                # Формируем ответ в зависимости от return_timestamps
                if return_timestamps:
                    response = {
                        "segments": result.get("segments", []),
                        "text": result.get("text", ""),
                        "processing_time": processing_time,
                        "response_size_bytes": len(str(result).encode('utf-8')),
                        "duration_seconds": duration,
                        "model": os.path.basename(self.config["model_path"])
                    }
                else:
                    # Если не запрашивались временные метки, result - это строка
                    response = {
                        "text": result,
                        "processing_time": processing_time,
                        "response_size_bytes": len(str(result).encode('utf-8')),
                        "duration_seconds": duration,
                        "model": os.path.basename(self.config["model_path"])
                    }
    
                # Журналирование результата
                self.history.save(response, filename)
    
                return response, 200
    
            except Exception as e:
                logger.error(f"Ошибка при транскрибации: {e}")
                error_details = str(e)
                # Include more details if subprocess error occurred
                if hasattr(e, 'stderr') and e.stderr:
                    error_details += f" - Subprocess error: {e.stderr.decode('utf-8', errors='replace')}"
                return {"error": error_details, "details": f"Error processing audio file: {type(e).__name__}"}, 500
    
        except Exception as e:
            logger.error(f"Ошибка при сохранении или обработке файла: {e}")
            return {"error": str(e), "details": f"Error saving or processing file: {type(e).__name__}"}, 500
            
        finally:
            # Восстанавливаем оригинальное значение return_timestamps
            self.transcriber.return_timestamps = original_return_timestamps

            # Очистка временных файлов
            if os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except Exception as e:
                    logger.warning(f"Failed to remove temp file {temp_file_path}: {e}")
                    
            if os.path.exists(temp_dir):
                try:
                    os.rmdir(temp_dir)
                except Exception as e:
                    logger.warning(f"Failed to remove temp directory {temp_dir}: {e}")
