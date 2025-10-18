import math
import time

class OneEuro:

    def __init__(self, freq, min_cut=1.0, beta=0.0, d_cut=1.0):
        self.freq     = float(freq)   # sampling frequency (Hz)
        self.min_cut  = float(min_cut)
        self.beta     = float(beta)
        self.d_cut    = float(d_cut)
        self.x_prev   = None          # previous filtered value
        self.dx_prev  = 0.0           # previous filtered derivative
        self.t_prev   = None          # previous timestamp

    # ---------- helper: smoothing factor ----------
    def _alpha(self, cutoff):
        tau = 1.0 / (2 * math.pi * cutoff)
        te  = 1.0 / self.freq
        return 1.0 / (1.0 + tau / te)

    # ---------- main update ----------
    def __call__(self, x):
        t_now = time.time()
        if self.t_prev is None:            # first sample → init state
            self.x_prev = x
            self.t_prev = t_now
            return x

        # 1) derivative filtering
        dx      = (x - self.x_prev) * self.freq
        alpha_d = self._alpha(self.d_cut)
        dx_hat  = alpha_d * dx + (1 - alpha_d) * self.dx_prev

        # 2) signal filtering with adaptive cutoff
        cutoff  = self.min_cut + self.beta * abs(dx_hat)
        alpha   = self._alpha(cutoff)
        x_hat   = alpha * x + (1 - alpha) * self.x_prev

        # save state
        self.x_prev, self.dx_prev, self.t_prev = x_hat, dx_hat, t_now
        return x_hat