import os
import uuid
import torch
import librosa
import tempfile
from fastapi import UploadFile
from datetime import datetime, timezone
from app.domain.models.audio import Audio
from app.domain.repositories.audio_repository import IAudioRepository

class AudioService:
    def __init__(self, repository: IAudioRepository, model, processor):
        self.repository = repository
        self.model = model
        self.processor = processor

    async def predict_audio(self, file: UploadFile) -> Audio:
        try:
            ext = file.filename.split(".")[-1]
            filename = f"audio_{uuid.uuid4()}.{ext}"

            temp_dir = tempfile.gettempdir()
            filepath = os.path.join(temp_dir, filename)

            with open(filepath, "wb") as buffer:
                buffer.write(await file.read())

            signal, _ = librosa.load(filepath, sr=16000)
            inputs = self.processor(signal, sampling_rate=16000, return_tensors="pt", padding=True)

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
            )
            return self.repository.save(audio)

        except Exception as e:
            print(f"[ERROR] {e}")
            raise