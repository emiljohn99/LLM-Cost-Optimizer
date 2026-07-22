import pandas as pd
import joblib
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report

DATA_PATH = "../data/prompts.csv"
MODEL_PATH = "model.pkl"
EMBEDDER_NAME = "all-MiniLM-L6-v2"

df = pd.read_csv(DATA_PATH)

X_train_text, X_test_text, y_train, y_test = train_test_split(
    df["prompt"], df["difficulty"],
    test_size=0.2, random_state=42, stratify=df["difficulty"]
)

print("Loading embedder...")
embedder = SentenceTransformer(EMBEDDER_NAME)

print("Embedding prompts...")
X_train = embedder.encode(X_train_text.tolist(), show_progress_bar=True)
X_test = embedder.encode(X_test_text.tolist(), show_progress_bar=True)

print("Training classifier...")
clf = LogisticRegression(max_iter=1000)
clf.fit(X_train, y_train)

y_pred = clf.predict(X_test)
print("\nAccuracy:", accuracy_score(y_test, y_pred))
print("\nConfusion matrix (rows=true, cols=pred):")
labels = sorted(df["difficulty"].unique())
print(labels)
print(confusion_matrix(y_test, y_pred, labels=labels))
print("\nClassification report:")
print(classification_report(y_test, y_pred))

joblib.dump(clf, MODEL_PATH)
print(f"\nSaved trained classifier to {MODEL_PATH}")