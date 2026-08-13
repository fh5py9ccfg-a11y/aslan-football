from math import exp, log

class TemperatureScaler:
    def __init__(self, temperature=1.0):
        if temperature <= 0:
            raise ValueError("temperature pozitif olmalıdır")
        self.temperature = float(temperature)

    def transform(self, probabilities):
        if any(p <= 0 or p >= 1 for p in probabilities):
            raise ValueError("Olasılıklar açık aralıkta olmalıdır")
        scaled = [exp(log(p) / self.temperature) for p in probabilities]
        total = sum(scaled)
        return tuple(round(x/total, 8) for x in scaled)

    def fit_grid(self, probabilities, outcomes, candidates=(0.75,1.0,1.25,1.5,2.0)):
        if len(probabilities) != len(outcomes) or not probabilities:
            raise ValueError("Kalibrasyon verisi geçersiz")
        best_t, best_loss = None, float("inf")
        for t in candidates:
            if t <= 0:
                continue
            loss = 0.0
            for probs, outcome in zip(probabilities, outcomes):
                calibrated = TemperatureScaler(t).transform(probs)
                loss += -log(max(calibrated[outcome], 1e-12))
            loss /= len(outcomes)
            if loss < best_loss:
                best_t, best_loss = t, loss
        if best_t is None:
            raise ValueError("Geçerli sıcaklık adayı yok")
        self.temperature = float(best_t)
        return self.temperature
