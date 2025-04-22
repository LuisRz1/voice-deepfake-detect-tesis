import os
import uuid
import torch
import librosa
import tempfile
from fastapi import UploadFile
from datetime import datetime, timezone
from app.domain.models.audio import Audio
from app.infrastructure.model_loader import model, processor
from app.infrastructure.database.audio_repo_impl import SQLAudioRepository

async def predict_audio(file: UploadFile) -> Audio:
    try:
        ext = file.filename.split(".")[-1]
        filename = f"audio_{uuid.uuid4()}.{ext}"

        temp_dir = tempfile.gettempdir()
        filepath = os.path.join(temp_dir, filename)

        with open(filepath, "wb") as buffer:
            buffer.write(await file.read())

        signal, _ = librosa.load(filepath, sr=16000)
        inputs = processor(signal, sampling_rate=16000, return_tensors="pt", padding=True)

        with torch.no_grad():
            logits = model(**inputs).logits

        prediction = torch.argmax(logits, dim=1).item()
        confidence = torch.softmax(logits, dim=1).max().item() * 100
        os.remove(filepath)  # Limpieza

        result = "fake" if prediction == 1 else "real"
        audio = Audio(
            filename=filename,
            result=result,
            confidence=round(confidence, 2),
            created=datetime.now(timezone.utc),
        )
        return SQLAudioRepository().save(audio)

    except Exception as e:
        print(f"[ERROR] {e}")
        raise
