import io
import time
from typing import Iterable
from faster_whisper.transcribe import Segment
from numpy import ndarray
import ollama
from os import getenv
from faster_whisper import WhisperModel
from .logger_config import logger_whisper, logger_diastr
import torchaudio
import torchaudio.functional as F
from pyannote.audio import Pipeline
import onnxruntime as ort
import os
import tempfile
import torch

# Настройка ONNX Runtime перед загрузкой модели
ort.set_default_logger_severity(3)  # Уменьшаем уровень логов ONNX Runtime

# Создаем оптимизированные настройки для ONNX Runtime
onnx_session_options = ort.SessionOptions()
onnx_session_options.graph_optimization_level = (
    ort.GraphOptimizationLevel.ORT_ENABLE_ALL
)
onnx_session_options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL

torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True


# ollama._client._client = None  # Сбросить клиент

# os.environ.pop('HTTP_PROXY', None)
# os.environ.pop('HTTPS_PROXY', None)


class Whisper_model:
    """
    Необходимые функции для Whisper модели
    """

    def __init__(self) -> None:
        """
        Подготовка Whisper модели
        """
        # 1. VAD (Voice Activity Detection)
        # Оптимизация разделения реплик
        self.vad_params = {
            "threshold": 0.5,  # порог обнаружения речи (по умолчанию ~0.5)
            "min_speech_duration_ms": 200,  # мин. длительность сегмента речи (мс)
            "max_speech_duration_s": 10,  # макс. длительность (с)
            "min_silence_duration_ms": 200,  # мин. тишина между сегментами (мс)
        }

        self.model = WhisperModel(
            model_size_or_path=str(
                getenv("WHISPER_MODEL")
            ),  # Размер и версия модели Whisper, определяет точность и скорость
            device="cuda",  # Устройство для вычислений: "cuda" - использование GPU, "cpu" - процессор
            compute_type="int8",  # Формат вычислений, влияет на скорость и потребление памяти, например "float16"
        )

        # Загружаем модель диаризации
        self.pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.0",
            use_auth_token=getenv("HF_KEY"),
        )
        self.pipeline.to(torch.device("cuda"))

        # Расширенные настройки параметров
        params = {
            # Параметры сегментации (разделение на сегменты с речью)
            "segmentation": {
                "min_duration_off": 0.05,  # минимальная продолжительность паузы между речью (в секундах)
            },
            # Параметры кластеризации (группировка сегментов по спикерам)
            "clustering": {
                "method": "centroid",  # метод кластеризации ('average', 'complete', 'single')
                "threshold": 0.35,  # порог для кластеризации
                "min_cluster_size": 1,  # минимальное количество сегментов в кластере
            },
        }
        # Применение параметров к конвейеру
        self.pipeline.instantiate(params)

    @staticmethod
    def update_audio(audio: io.BytesIO) -> str:
        """
        Предобработка (улучшение) звука.

        Args:
            audio (io.BytesIO): аудио в байтах

        Returns:
            io.BytesIO: Улучшенное аудио
        """
        # Загрузка аудио (исходный sample_rate)
        waveform, original_sample_rate = torchaudio.load(audio, format="mp3")
        new_sample_rate = 16000  # Новая частота дискретизации (16000 Гц)

        # Изменение дискретизации
        resampled_waveform = torchaudio.functional.resample(
            waveform, orig_freq=original_sample_rate, new_freq=new_sample_rate
        )

        # Добавление отступа в 0.5 секунду в начале
        silence_duration = 0.5  # 0.5 секунд
        silence_samples = int(silence_duration * new_sample_rate)
        # Создаём тишину
        silence = torch.zeros((resampled_waveform.size(0), silence_samples))
        # Добавляем в начало
        resampled_waveform = torch.cat([silence, resampled_waveform], dim=1)

        # Применение ФНЧ (фильтр низких частот, убирает высокочастотный шум)
        resampled_waveform = F.lowpass_biquad(
            resampled_waveform, new_sample_rate, cutoff_freq=4000
        )

        # Применение ФВЧ (фильтр высоких частот, убирает гул)
        resampled_waveform = F.highpass_biquad(
            resampled_waveform, new_sample_rate, cutoff_freq=80
        )

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = temp_file.name  # Получаем путь к временному файлу

        torchaudio.save(temp_path, resampled_waveform, new_sample_rate, format="wav")

        # Сохранение в байты в новой дискретизации
        return temp_path

    def _diarization(self, audio):
        # Применяем диаризацию
        start_time = time.time()  # Начало отсчета
        diarization = self.pipeline(
            audio, num_speakers=2, min_speakers=2, max_speakers=2
        )
        end_time = time.time()
        logger_diastr.info(f"Время диаризации: {(end_time-start_time):.2f} секунд")
        start_time = time.time()  # Начало отсчета
        segments, _ = self.model.transcribe(
            audio=audio,  # Аудио
            language="ru",  # Язык
            task="transcribe",  # Задача транскрибировать
            vad_filter=True,  # Включение VAD
            vad_parameters=self.vad_params,  # 1. Настройки VAD
            chunk_length=20,  # Длина чанка в секундах
            repetition_penalty=1,  # штраф за повторы слов (1.0 = нет штрафа)
            temperature=0,  # Умеренная случайность (0-1), чем больше тем креативнее модель
            initial_prompt="Участники разговора: менеджер 'Греческой химчистки Ева Дейли' или Клиент.",  # Подсказка для модели
            beam_size=5,  # Количество вариантов генерации
        )
        os.unlink(audio)  # Удаляем временный файл
        # 4. Сопоставление спикеров с текстом
        aligned_segments = []
        speaker_change_penalty = 0.3  # Penalt for frequent speaker changes
        last_speaker = None

        for segment in segments:
            # Находим спикера для текущего временного отрезка
            speaker = None
            max_overlap = 0
            overlap_threshold = 0.05  # Minimum overlap ratio to consider
            speaker_scores = {}

            for turn, _, spk in diarization.itertracks(yield_label=True):
                # Calculate overlap between segment and turn
                overlap_start = max(segment.start, turn.start)
                overlap_end = min(segment.end, turn.end)
                overlap_duration = max(0, overlap_end - overlap_start)

                # Calculate overlap ratio relative to segment duration
                segment_duration = segment.end - segment.start
                overlap_ratio = (
                    overlap_duration / segment_duration if segment_duration > 0 else 0
                )

                # Apply continuity bonus if same as last speaker
                if spk == last_speaker and overlap_ratio > 0:
                    overlap_ratio += speaker_change_penalty

                speaker_scores[spk] = speaker_scores.get(spk, 0) + overlap_ratio

            # Select speaker with highest score
            if speaker_scores:
                speaker = max(speaker_scores.items(), key=lambda x: x[1])[0]
                if speaker_scores[speaker] >= overlap_threshold:
                    last_speaker = speaker
                else:
                    speaker = None

                # Track speaker with maximum overlap
                if overlap_ratio > max_overlap and overlap_ratio >= overlap_threshold:
                    max_overlap = overlap_ratio
                    speaker = spk

            # Only add segment if we found a speaker with sufficient overlap
            if speaker is not None:

                aligned_segments.append(
                    {
                        "start": segment.start,
                        "end": segment.end,
                        "text": segment.text,
                        "speaker": speaker,
                    }
                )

        end_time = time.time()  # Начало отсчета
        logger_diastr.info(f"Время транскрибации: {(end_time-start_time):.2f} секунд")

        return aligned_segments

    def get_transcribe(self, audio: io.BytesIO) -> str:
        """
        Обработка начального аудио-файла, создание текста по ролям

        Args:
            audio (io.BytesIO): Аудио в форме байтов

        Returns:
            str: транскрибированный текст
        """

        audio = Whisper_model.update_audio(audio)  # Обработка звука
        segments = self._diarization(audio)

        # Post-process to improve speaker assignment based on conversation patterns
        segments = self._improve_speaker_assignment(segments)

        total_text = ""
        # Вывод результатов
        for seg in segments:
            total_text += f"[{seg['speaker']}]: {seg['text']}\n"

        total_text = self.get_role_text(audio)  # Получение текста по ролям

        return audio

    def _improve_speaker_assignment(self, segments):
        """Post-process segments to ensure better speaker alternation"""
        if len(segments) < 2:
            return segments
        # Count initial speaker distribution
        speaker_counts = {}
        for seg in segments:
            speaker_counts[seg["speaker"]] = speaker_counts.get(seg["speaker"], 0) + 1
        # If one speaker dominates (>80%), force alternation in question-answer patterns
        total = sum(speaker_counts.values())
        max_ratio = max(speaker_counts.values()) / total if total > 0 else 0

        if max_ratio > 0.8 and len(speaker_counts) == 2:
            speakers = list(speaker_counts.keys())
            # Look for question patterns
            for i in range(len(segments) - 1):
                curr_text = segments[i]["text"].lower()
                # If current ends with question and next starts without question, alternate speakers
                if "?" in curr_text or any(
                    q in curr_text
                    for q in ["сколько", "какой", "какие", "что", "где", "когда"]
                ):
                    if segments[i]["speaker"] == segments[i + 1]["speaker"]:
                        # Alternate the speaker for the answer
                        other_speaker = (
                            speakers[1]
                            if segments[i]["speaker"] == speakers[0]
                            else speakers[0]
                        )
                        segments[i + 1]["speaker"] = other_speaker
        return segments


whisper_model = Whisper_model()


class LLM_model:

    @staticmethod
    def generate_answer(system: str, prompt: str) -> str:
        response = ollama.generate(  # Генерация
            model=str(getenv("MODEL")),
            system=system,
            prompt=prompt,
            options={
                # "top_k": 50,  # ограничивает выбор топ-K наиболее вероятных токенов
                # "top_p": 0.9,  # nucleus sampling (отбирает токены с кумулятивной вероятностью до top_p)
                "temperature": 0.6,  # чем выше, тем более случайным будет ответ (0 = детерминировано)
                # "num_predict": 100,  # максимальное количество генерируемых токенов
                # "repeat_penalty": 1.1,  # штраф за повторения (чем выше, тем меньше повторов)
                # "seed": 42,  # фиксирует seed для воспроизводимости
            },
        )
        return response["response"]
