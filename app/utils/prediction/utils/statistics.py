import numpy as np

def safe_mean(values):
    return float(np.mean(values)) if values else 0.0

def safe_std(values):
    return float(np.std(values)) if len(values) > 1 else 0.0
