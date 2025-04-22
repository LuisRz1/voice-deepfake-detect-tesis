import os
from transformers import Wav2Vec2Processor, Wav2Vec2ForSequenceClassification

MODEL_REPO = os.getenv("HF_MODEL_REPO", "langulor/deepfake-voice-spanish")

processor = Wav2Vec2Processor.from_pretrained(MODEL_REPO)
model = Wav2Vec2ForSequenceClassification.from_pretrained(MODEL_REPO)
model.eval()