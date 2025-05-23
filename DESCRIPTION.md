# Структура проекта Whisper API Service

Проект представляет собой локальный API-сервис для распознавания речи, построенный на основе модели Whisper. Сервис разработан как OpenAI-совместимый API, что позволяет использовать его в качестве локальной альтернативы облачным сервисам распознавания речи.

## Основные файлы

### Корневые файлы
- **server.py** - точка входа в приложение, инициализирует и запускает сервис
- **server.sh** - bash-скрипт для запуска сервера с опциональным обновлением conda-окружения
- **config.json** - конфигурационный файл с настройками сервиса
- **requirements.txt** - зависимости проекта для conda/pip

### Модуль `app`

#### app/\_\_init\_\_.py
Содержит основной класс `WhisperServiceAPI`, который инициализирует приложение, загружает конфигурацию и запускает сервер на указанном порту.

#### app/logger.py
Настройка логирования для всех компонентов приложения.

#### app/transcriber.py
Содержит класс `WhisperTranscriber`, который загружает модель Whisper и выполняет распознавание речи. Класс определяет оптимальное устройство для вычислений (CPU, CUDA, MPS) и поддерживает ускорение с помощью Flash Attention 2.

#### app/audio_processor.py
Содержит класс `AudioProcessor` для предобработки аудиофайлов перед их транскрибацией. Включает методы для:
- Конвертации в WAV с частотой 16 кГц
- Нормализации уровня громкости
- Добавления тишины в начало записи
- Очистки временных файлов

#### app/audio_sources.py
Содержит абстрактный класс `AudioSource` и его конкретные реализации для различных источников аудио:
- `UploadedFileSource` - для файлов, загруженных через HTTP-запрос
- `URLSource` - для файлов, доступных по URL
- `Base64Source` - для аудио, закодированного в base64
- `LocalFileSource` - для локальных файлов на сервере
- `FakeFile` - вспомогательный класс для унификации обработки из разных источников

#### app/routes.py
Содержит классы:
- `TranscriptionService` - сервис для обработки и транскрибации аудиофайлов
- `Routes` - регистрирует все эндпоинты API, включая OpenAI-совместимые маршруты

## Основные классы и их описание

### WhisperServiceAPI
Основной класс приложения, инициализирует сервис, загружает конфигурацию и запускает сервер с использованием Waitress.

### WhisperTranscriber
Класс для распознавания речи с использованием модели Whisper. Определяет оптимальное устройство для вычислений, загружает модель с учетом доступного оборудования и выполняет транскрибацию аудиофайлов.

### AudioProcessor
Класс для предобработки аудиофайлов. Выполняет конвертацию, нормализацию и добавление тишины в начало записи для улучшения качества распознавания.

### AudioSource (и наследники)
Абстрактный класс и его реализации для работы с различными источниками аудиофайлов. Обеспечивает унифицированный интерфейс для получения аудиофайлов из разных источников.

### TranscriptionService
Сервис, объединяющий логику обработки запросов и транскрибации аудио. Принимает источник аудио, обрабатывает его и возвращает результат транскрибации.

### Routes
Класс, регистрирующий все маршруты API сервиса, включая совместимые с OpenAI эндпоинты для интеграции с существующими клиентами.

## API Endpoints

Сервис предоставляет несколько эндпоинтов, включая:
- `/health` - проверка статуса сервиса
- `/config` - получение текущей конфигурации
- `/local/transcriptions` - транскрибация локального файла на сервере
- `/v1/models` - получение списка доступных моделей (OpenAI-совместимый)
- `/v1/audio/transcriptions` - транскрибация загруженного файла (OpenAI-совместимый)
- `/v1/audio/transcriptions/url` - транскрибация по URL
- `/v1/audio/transcriptions/base64` - транскрибация из base64
- `/v1/audio/transcriptions/multipart` - транскрибация файла из multipart-формы

Сервис разработан таким образом, чтобы обеспечить максимальную гибкость в использовании и интеграцию с существующими системами, поддерживающими API OpenAI Whisper.