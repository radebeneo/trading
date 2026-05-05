from  transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from typing import Tuple

device = "cuda:0" if torch.cuda.is_available() else "cpu"

tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert").to(device)
labels = ["positive", "negative", "neutral"]

def estimate_sentiment(news):
    if news:
        tokens = tokenizer(news, return_tensors="pt", padding=True).to(device)
        result = model(tokens["input_ids"], attention_mask=tokens["attention_mask"])["logits"]
        # Average logits across all articles → shape (3,)
        avg_logits = result.mean(dim=0)
        probabilities = torch.nn.functional.softmax(avg_logits, dim=0)
        best_idx = torch.argmax(probabilities).item()
        sentiment = labels[best_idx]
        probability = probabilities[best_idx].item()
        return probability, sentiment
    else:
        return 0, labels[-1]

if __name__ == "__main__":
    tensor, sentiment = estimate_sentiment(['markets responded negatively to the news!', 'traders were displeased!'])
    print(tensor, sentiment)
    print(torch.cuda.is_available())
