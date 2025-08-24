import numpy as np
import pandas as pd
import os

try:
    import joblib
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.model_selection import train_test_split

    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("Warning: scikit-learn and joblib not available. ML features disabled.")


class MLAdvisor:
    def __init__(self):
        self.model = None
        self.trained = False
        self.ml_available = ML_AVAILABLE
        self.model_path = "logs/ml_model.joblib"

    def train_from_csv(self, csv_path="logs/training_data.csv"):
        if not self.ml_available or not os.path.exists(csv_path):
            print("No se puede entrenar: Faltan librerías o datos.")
            return

        df = pd.read_csv(csv_path)
        if len(df) < 50:  # No entrenar si hay muy pocos datos
            print(f"Datos insuficientes para entrenar ({len(df)} muestras).")
            return

        X = df.drop("outcome", axis=1).values
        y = df["outcome"]

        # Asegurarse de que y tenga un tipo compatible para stratify
        y_stratify = np.array(y)

        # No estratificar si hay menos de 2 muestras de alguna clase
        if len(np.unique(y_stratify)) < 2 or np.min(np.bincount(y_stratify)) < 2:
            y_stratify = None

        # Dividir datos para validación (opcional pero buena práctica)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y_stratify
        )

        print(f"Entrenando modelo con {len(X_train)} muestras...")
        self.model = DecisionTreeClassifier(max_depth=7, random_state=42)
        self.model.fit(X_train, y_train)
        self.trained = True

        # Evaluar el modelo
        accuracy = self.model.score(X_test, y_test)
        print(f"Entrenamiento completado. Precisión del modelo: {accuracy:.2f}")
        self.save_model()

    def train(self, X, y):
        if not self.ml_available:
            raise Exception(
                "ML libraries not available. Install scikit-learn and joblib."
            )
        self.model = DecisionTreeClassifier(max_depth=5, random_state=42)
        self.model.fit(X, y)
        self.trained = True

    def advise(self, features):
        if not self.trained or not self.ml_available or self.model is None:
            return 0.5  # Neutral probability if ML is not available
        try:
            proba = self.model.predict_proba(features.reshape(1, -1))
            return proba[0][1]  # Probability of positive class
        except:
            return 0.5

    def save_model(self):
        if self.ml_available and self.trained:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            joblib.dump(self.model, self.model_path)
            print(f"Modelo guardado en {self.model_path}")

    def load_model(self):
        if self.ml_available and os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                self.trained = True
                print(f"Modelo cargado desde {self.model_path}")
            except Exception as e:
                print(f"No se pudo cargar el modelo: {e}")
