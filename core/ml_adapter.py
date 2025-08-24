import numpy as np

try:
    import joblib
    from sklearn.tree import DecisionTreeClassifier

    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("Warning: scikit-learn and joblib not available. ML features disabled.")


class MLAdvisor:
    def __init__(self):
        self.model = None
        self.trained = False
        self.ml_available = ML_AVAILABLE

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

    def save_model(self, filename):
        if self.ml_available and self.trained:
            joblib.dump(self.model, filename)

    def load_model(self, filename):
        if self.ml_available:
            self.model = joblib.load(filename)
            self.trained = True
