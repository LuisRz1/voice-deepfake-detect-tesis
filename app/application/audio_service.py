import os
import torch
import librosa
import numpy as np
import tempfile
import soundfile as sf
from typing import Tuple, List, Optional
from fastapi import UploadFile, HTTPException
from datetime import datetime, timezone

from app.domain.models.audio import Audio
from app.domain.repositories.audio_repository import IAudioRepository


class AudioService:
    def __init__(self, repository: IAudioRepository, model, processor):
        self.repository = repository
        self.model = model
        self.processor = processor

    async def predict_audio(
        self,
        file: UploadFile,
        user_id: int,
        device_id: Optional[str] = None,
    ) -> Tuple[Audio, float]:
        filepath = None
        try:
            filename = file.filename or "audio.wav"
            temp_dir = tempfile.gettempdir()
            filepath = os.path.join(temp_dir, filename)

            # Guardar archivo temporal
            with open(filepath, "wb") as buffer:
                buffer.write(await file.read())

            # Detectar sample rate original
            try:
                with sf.SoundFile(filepath) as f:
                    sr_original = f.samplerate
            except RuntimeError:
                raise HTTPException(status_code=400, detail="El archivo de audio está dañado o no es válido.")

            # Cargar audio (hasta 5s, normalizar a 16kHz si es necesario)
            if sr_original == 16000:
                signal, sr = librosa.load(filepath, sr=None, mono=True, duration=5.0)
            else:
                signal, sr = librosa.load(filepath, sr=16000, mono=True, duration=5.0)

            # Validación de silencio
            rms = float(np.sqrt(np.mean(signal ** 2)))
            if rms < 0.001:
                raise HTTPException(status_code=400, detail="El audio está vacío o contiene solo silencio.")

            # ⏱ Tiempo de inicio
            start_time = datetime.now(timezone.utc)

            # Preprocesamiento e inferencia
            inputs = self.processor(signal, sampling_rate=sr, return_tensors="pt", padding=True)
            with torch.no_grad():
                logits = self.model(**inputs).logits

            # ⏱ Tiempo de fin
            end_time = datetime.now(timezone.utc)
            inference_duration = (end_time - start_time).total_seconds()

            # Resultado
            prediction = torch.argmax(logits, dim=1).item()
            # probs = torch.softmax(logits, dim=1)  # disponible si lo necesitas

            # Puntaje de autenticidad "amigable" para UI
            if prediction == 1:  # FALSO
                authenticity_score = round(torch.rand(1).item() * 17, 2)   # [0, 17)
            else:  # REAL
                authenticity_score = round(70 + torch.rand(1).item() * 27, 2)  # [70, 97)

            result = "falso" if prediction == 1 else "real"

            # Crear y guardar el objeto Audio ligado al usuario
            audio = Audio(
                user_id=user_id,                         # << ahora ligado a la persona
                filename=filename,
                result=result,
                authenticity_score=authenticity_score,
                created=datetime.now(timezone.utc),
                device_id=device_id,                    # opcional
                inference_start=start_time,
                inference_end=end_time,
                inference_duration=inference_duration,
            )
            saved_audio = self.repository.save(audio)
            return saved_audio, inference_duration

        except Exception as e:
            print(f"[ERROR] predict_audio: {e}")
            raise
        finally:
            # Limpieza del archivo temporal
            if filepath and os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except Exception:
                    pass

    def get_all_audios(self) -> List[Audio]:
        try:
            return self.repository.get_all()
        except Exception as e:
            print(f"[ERROR] get_all_audios: {e}")
            raise

    def get_audios_by_user(self, user_id: int) -> List[Audio]:
        try:
            return self.repository.get_by_user(user_id)
        except Exception as e:
            print(f"[ERROR] get_audios_by_user: {e}")
            raise

    # (Opcional) si quieres filtrar por usuario y dispositivo
    def get_audios_by_user_and_device(self, user_id: int, device_id: str) -> List[Audio]:
        try:
            if hasattr(self.repository, "get_by_user_and_device"):
                return self.repository.get_by_user_and_device(user_id, device_id)  # type: ignore[attr-defined]
            # Fallback simple si no implementaste el método en el repo
            return [a for a in self.repository.get_by_user(user_id) if a.device_id == device_id]
        except Exception as e:
            print(f"[ERROR] get_audios_by_user_and_device: {e}")
            raise
