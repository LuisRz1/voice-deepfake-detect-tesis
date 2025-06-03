import os
import torch
import librosa
import tempfile
import soundfile as sf
from typing import Tuple, List
from fastapi import UploadFile
from datetime import datetime, timezone
from app.domain.models.audio import Audio
from app.domain.repositories.audio_repository import IAudioRepository

class AudioService:
    def __init__(self, repository: IAudioRepository, model, processor):
        self.repository = repository
        self.model = model
        self.processor = processor

    async def predict_audio(self, file: UploadFile, device_id: str) -> Tuple[Audio, float]:
        try:
            filename = file.filename

            # Guardar archivo temporalmente
            temp_dir = tempfile.gettempdir()
            filepath = os.path.join(temp_dir, filename)

            with open(filepath, "wb") as buffer:
                buffer.write(await file.read())

            # Leer sample rate original sin cargar aún
            with sf.SoundFile(filepath) as f:
                sr_original = f.samplerate

            # Optimizar carga con librosa solo si es necesario
            if sr_original == 16000:
                signal, sr = librosa.load(filepath, sr=None, mono=True, duration=5.0)
            else:
                signal, sr = librosa.load(filepath, sr=16000, mono=True, duration=5.0)

            duration = librosa.get_duration(y=signal, sr=sr)

            # Procesamiento con Hugging Face
            inputs = self.processor(signal, sampling_rate=sr, return_tensors="pt", padding=True)

            with torch.no_grad():
                logits = self.model(**inputs).logits

            prediction = torch.argmax(logits, dim=1).item()
            probs = torch.softmax(logits, dim=1)
            authenticity_score = probs[0][0].item() * 100

            os.remove(filepath)

            result = "fake" if prediction == 1 else "real"
            audio = Audio(
                filename=filename,
                result=result,
                authenticity_score=round(authenticity_score, 2),
                created=datetime.now(timezone.utc),
                device_id=device_id  # ← NUEVO: se guarda el identificador del usuario/dispositivo
            )
            saved_audio = self.repository.save(audio)
            return saved_audio, duration

        except Exception as e:
            print(f"[ERROR] {e}")
            raise

    def get_all_audios(self) -> List[Audio]:
        try:
            return self.repository.get_all()
        except Exception as e:
            print(f"[ERROR] get_all_audios: {e}")
            raise

    def get_audios_by_device(self, device_id: str) -> List[Audio]:
        try:
            return self.repository.get_by_device(device_id)
        except Exception as e:
            print(f"[ERROR] get_audios_by_device: {e}")
            raise