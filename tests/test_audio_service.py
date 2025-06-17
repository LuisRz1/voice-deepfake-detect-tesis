import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import torch
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import UploadFile, HTTPException
from app.infrastructure.model_loader import model, processor  # ← usa tus reales
from app.application.audio_service import AudioService
from app.domain.models.audio import Audio
from datetime import datetime, timedelta, timezone

@pytest.mark.asyncio
async def test_predict_audio_real():
    # Mock de archivo de audio
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "real_audio.wav"
    mock_file.read = AsyncMock(return_value=b"dummy audio bytes")

    # Mock del modelo que devuelve logits válidos para clase 0 (real)
    class MockModel:
        def __init__(self, logits_tensor):
            self._logits = logits_tensor
        def __call__(self, **kwargs):
            return type('Output', (object,), {"logits": self._logits})

    logits_tensor = torch.tensor([[0.9, 0.1]])  # clase 0 = real
    mock_model = MockModel(logits_tensor)

    # Mock del processor
    mock_processor = MagicMock(return_value={"input_values": torch.randn(1, 16000)})

    # Mock del repositorio
    mock_repo = MagicMock()
    mock_repo.save = MagicMock(side_effect=lambda audio: audio)

    # Instancia del servicio
    service = AudioService(mock_repo, mock_model, mock_processor)

    with patch("librosa.load", return_value=(torch.randn(80000).numpy(), 16000)), \
         patch("soundfile.SoundFile") as mock_sf, \
         patch("os.remove"), \
         patch("app.application.audio_service.datetime") as mock_datetime:

        fake_start = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        fake_end = fake_start + timedelta(seconds=1)
        mock_datetime.now.side_effect = [fake_start, fake_end, fake_end]
        mock_datetime.timezone = timezone

        mock_sf.return_value.__enter__.return_value.samplerate = 16000

        # Ejecutar predicción
        audio, duration = await service.predict_audio(mock_file, "device123")

        # Verificaciones
        assert isinstance(audio, Audio)
        assert audio.result == "real"
        assert 70 <= audio.authenticity_score <= 97
        assert duration == 1.0
        assert audio.device_id == "device123"

        # Mostrar salida
        print(f"Resultado: {audio.result}, Score: {audio.authenticity_score}, Duración: {duration}")


@pytest.mark.asyncio
async def test_predict_audio_fake():
    # Mock de archivo de audio
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "fake_audio.wav"
    mock_file.read = AsyncMock(return_value=b"dummy audio bytes")

    # Mock del modelo que devuelve logits válidos
    class MockModel:
        def __init__(self, logits_tensor):
            self._logits = logits_tensor
        def __call__(self, **kwargs):
            return type('Output', (object,), {"logits": self._logits})

    logits_tensor = torch.tensor([[0.1, 0.9]])  # clase 1 = fake
    mock_model = MockModel(logits_tensor)

    # Mock del processor
    mock_processor = MagicMock(return_value={"input_values": torch.randn(1, 16000)})

    # Mock del repositorio
    mock_repo = MagicMock()
    mock_repo.save = MagicMock(side_effect=lambda audio: audio)

    # Instancia del servicio
    service = AudioService(mock_repo, mock_model, mock_processor)

    # Patches necesarios
    with patch("librosa.load", return_value=(torch.randn(80000).numpy(), 16000)), \
         patch("soundfile.SoundFile") as mock_sf, \
         patch("os.remove"), \
         patch("app.application.audio_service.datetime") as mock_datetime:

        # Simular tiempo de inferencia
        fake_start = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        fake_end = fake_start + timedelta(seconds=1)
        mock_datetime.now.side_effect = [fake_start, fake_end, fake_end]
        mock_datetime.timezone = timezone

        mock_sf.return_value.__enter__.return_value.samplerate = 16000

        # Ejecutar predicción
        audio, duration = await service.predict_audio(mock_file, "device123")

        # Verificaciones
        assert isinstance(audio, Audio)
        assert audio.result == "falso"
        assert 0 <= audio.authenticity_score <= 17
        assert duration == 1.0
        assert audio.device_id == "device123"
        print(f"Resultado: {audio.result}, Score: {audio.authenticity_score}, Duración: {duration}")

def test_get_audios_by_device():
    from app.domain.models.audio import Audio
    from app.application.audio_service import AudioService

    # Datos simulados
    fake_audios = [
        Audio(id=1, filename="audio1.wav", result="real", authenticity_score=82.1, created=datetime.now(timezone.utc), device_id="device123"),
        Audio(id=2, filename="audio2.wav", result="falso", authenticity_score=8.7, created=datetime.now(timezone.utc), device_id="device123"),
    ]

    # Mock del repositorio
    mock_repo = MagicMock()
    mock_repo.get_by_device = MagicMock(return_value=fake_audios)

    # Servicio (modelo y processor pueden ser None para este caso)
    service = AudioService(repository=mock_repo, model=None, processor=None)

    result = service.get_audios_by_device("device123")

    # Verificaciones
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0].filename == "audio1.wav"
    assert result[1].result == "falso"
    mock_repo.get_by_device.assert_called_once_with("device123")

    print(" Historial recuperado correctamente:", [a.filename for a in result])


@pytest.mark.asyncio
async def test_predict_audio_silencioso():
    # 🎧 Archivo simulado (vacío o en silencio)
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "silencio.wav"
    mock_file.read = AsyncMock(return_value=b"dummy audio bytes")

    # Modelo simulado (no importa, no llega a usarse)
    mock_model = MagicMock()
    mock_processor = MagicMock()
    mock_repo = MagicMock()

    service = AudioService(mock_repo, mock_model, mock_processor)

    with patch("librosa.load", return_value=(torch.zeros(80000).numpy(), 16000)), \
         patch("soundfile.SoundFile") as mock_sf, \
         patch("os.remove"), \
         patch("app.application.audio_service.datetime") as mock_datetime:

        # Simulación de audio válido estructuralmente
        mock_sf.return_value.__enter__.return_value.samplerate = 16000

        # Tiempo falso para inferencia
        fake_start = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        fake_end = fake_start + timedelta(seconds=1)
        mock_datetime.now.side_effect = [fake_start, fake_end, fake_end]
        mock_datetime.timezone = timezone

        # Ejecutar y verificar que se lanza error por silencio
        with pytest.raises(HTTPException) as exc_info:
            await service.predict_audio(mock_file, "device123")

        assert exc_info.value.status_code == 400
        assert "silencio" in exc_info.value.detail.lower()

        print(" Audio silencioso correctamente rechazado:", exc_info.value.detail)

@pytest.mark.asyncio
async def test_predict_audio_archivo_danado():
    # 🎧 Archivo simulado (no es un audio válido)
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "archivo_danado.wav"
    mock_file.read = AsyncMock(return_value=b"contenido invalido")

    # Modelo y processor no se usan
    mock_model = MagicMock()
    mock_processor = MagicMock()
    mock_repo = MagicMock()

    service = AudioService(mock_repo, mock_model, mock_processor)

    with patch("soundfile.SoundFile", side_effect=RuntimeError("formato no soportado")), \
         patch("os.remove"), \
         patch("app.application.audio_service.datetime") as mock_datetime:

        # Tiempo falso para consistencia
        fake_now = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.side_effect = [fake_now]
        mock_datetime.timezone = timezone

        # Verifica que se lanza un error por archivo dañado
        with pytest.raises(HTTPException) as exc_info:
            await service.predict_audio(mock_file, "device123")

        assert exc_info.value.status_code == 400
        assert "no es válido" in exc_info.value.detail.lower()

        print(" Archivo dañado correctamente rechazado:", exc_info.value.detail)

import io
from fastapi import UploadFile
from pathlib import Path

@pytest.mark.asyncio
async def test_predict_audio_real_desde_archivo():
    audio_path = Path("tests/resources/audio.wav")
    assert audio_path.exists(), "El archivo no existe en la ruta indicada."

    with open(audio_path, "rb") as f:
        audio_bytes = f.read()

    upload_file = UploadFile(filename="audio_real.wav", file=io.BytesIO(audio_bytes))

    # Repositorio falso
    mock_repo = MagicMock()
    mock_repo.save = MagicMock(side_effect=lambda audio: audio)

    # Instancia del servicio real
    service = AudioService(mock_repo, model, processor)

    # Solo parcheamos la eliminación del archivo temporal
    with patch("os.remove"):
        audio, duration = await service.predict_audio(upload_file, "device123")

        # Validaciones
        assert isinstance(audio, Audio)
        assert audio.result in ["real", "falso"]
        assert 0 <= audio.authenticity_score <= 100
        assert duration > 0.0  # ahora mide el tiempo real
        print(f" Resultado: {audio.result}, Score: {audio.authenticity_score}, Tiempo de inferencia: {duration:.4f}s")