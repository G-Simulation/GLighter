"""YAMNet (Google, Apache-2.0) in plain numpy - no ML runtime needed.

Model data: model/yamnet.npz (BatchNorm folded into the convolutions, float16),
model/yamnet_class_map.csv (521 AudioSet classes).
"""
import csv
import os
import numpy as np

SR = 16000
PATCH = 15600            # 0.975 s -> exactly one 96x64 patch
HOP = 7800               # 0.4875 s, ~50 % overlap
_DIR = os.environ.get("LAERM_MODEL_DIR") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "model")   # Kopie ohne Modell: eingebautes nehmen
_LAYERS = [(2, 32)] + [(1, 64), (2, 128), (1, 128), (2, 256), (1, 256), (2, 512),
                      (1, 512), (1, 512), (1, 512), (1, 512), (1, 512), (2, 1024), (1, 1024)]


def _mel_matrix():
    n_mel, n_bins, lo, hi = 64, 257, 125.0, 7500.0
    h2m = lambda f: 1127.0 * np.log(1.0 + f / 700.0)
    edges = np.linspace(h2m(lo), h2m(hi), n_mel + 2)
    spec = h2m(np.linspace(0.0, SR / 2.0, n_bins)[1:])
    lower = (spec[:, None] - edges[None, :-2]) / (edges[1:-1] - edges[:-2])[None, :]
    upper = (edges[None, 2:] - spec[:, None]) / (edges[2:] - edges[1:-1])[None, :]
    w = np.maximum(0.0, np.minimum(lower, upper))
    return np.pad(w, ((1, 0), (0, 0))).astype(np.float32)


class YamNet:
    def __init__(self):
        z = np.load(os.path.join(_DIR, "yamnet.npz"))
        self.w = {k: z[k].astype(np.float32) for k in z.files}
        with open(os.path.join(_DIR, "yamnet_class_map.csv"), newline="", encoding="utf-8") as f:
            r = csv.reader(f)
            next(r)
            self.names = [row[2] for row in r]
        self.mel = _mel_matrix()
        self.win = (0.5 - 0.5 * np.cos(2 * np.pi * np.arange(400) / 400)).astype(np.float32)

    # ---- features ----
    def logmel(self, x):
        x = np.asarray(x, dtype=np.float32)
        n = 1 + (len(x) - 400) // 160
        if n < 1:
            return np.zeros((0, 64), np.float32)
        idx = np.arange(400)[None, :] + 160 * np.arange(n)[:, None]
        mag = np.abs(np.fft.rfft(x[idx] * self.win, 512, axis=1)).astype(np.float32)
        return np.log(mag @ self.mel + 0.001).astype(np.float32)

    # ---- network ----
    @staticmethod
    def _pad(x, k, s):
        # TF "SAME" padding for NHWC with batch of patches: x (N,H,W,C)
        out = []
        for n in (x.shape[1], x.shape[2]):
            o = -(-n // s)
            tot = max((o - 1) * s + k - n, 0)
            out.append((tot // 2, tot - tot // 2))
        return np.pad(x, ((0, 0), out[0], out[1], (0, 0))), -(-x.shape[1] // s), -(-x.shape[2] // s)

    def _conv3(self, x, k, b, stride):  # standard 3x3 conv, in-channels = 1
        xp, oh, ow = self._pad(x, 3, stride)
        N = x.shape[0]
        out = np.zeros((N, oh, ow, k.shape[-1]), np.float32)
        for i in range(3):
            for j in range(3):
                sl = xp[:, i:i + stride * oh:stride, j:j + stride * ow:stride, :]
                out += sl * k[i, j, 0, :]
        return np.maximum(out + b, 0)

    def _dw(self, x, k, b, stride):
        xp, oh, ow = self._pad(x, 3, stride)
        out = np.zeros((x.shape[0], oh, ow, x.shape[3]), np.float32)
        for i in range(3):
            for j in range(3):
                out += xp[:, i:i + stride * oh:stride, j:j + stride * ow:stride, :] * k[i, j, :]
        return np.maximum(out + b, 0)

    def patches_scores(self, patches):
        """patches: (N,96,64) log-mel -> (N,521) sigmoid scores."""
        w = self.w
        x = patches[..., None].astype(np.float32)
        x = self._conv3(x, w["l1_k"], w["l1_b"], 2)
        for i, (s, _) in enumerate(_LAYERS[1:], start=2):
            x = self._dw(x, w["l%d_dk" % i], w["l%d_db" % i], s)
            N, H, W, C = x.shape
            x = np.maximum(x.reshape(-1, C) @ w["l%d_pk" % i] + w["l%d_pb" % i], 0).reshape(N, H, W, -1)
        x = x.mean(axis=(1, 2)) @ w["fc_k"] + w["fc_b"]
        return 1.0 / (1.0 + np.exp(-np.clip(x, -30, 30)))

    def patches_scores_emb(self, patches):
        """Wie patches_scores, zusaetzlich das 1024-stellige Embedding je Fenster."""
        w = self.w
        x = patches[..., None].astype(np.float32)
        x = self._conv3(x, w["l1_k"], w["l1_b"], 2)
        for i, (s, _) in enumerate(_LAYERS[1:], start=2):
            x = self._dw(x, w["l%d_dk" % i], w["l%d_db" % i], s)
            N, H, W, C = x.shape
            x = np.maximum(x.reshape(-1, C) @ w["l%d_pk" % i] + w["l%d_pb" % i], 0).reshape(N, H, W, -1)
        e = x.mean(axis=(1, 2))
        z = e @ w["fc_k"] + w["fc_b"]
        return 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30))), e

    def scores(self, wav, max_patches=60):
        """wav: float mono 16 kHz -> (patches, 521) scores, patches 0.975 s hop 0.4875 s."""
        wav = np.asarray(wav, dtype=np.float32)
        if len(wav) < PATCH:
            wav = np.pad(wav, (0, PATCH - len(wav)))
        starts = list(range(0, len(wav) - PATCH + 1, HOP))
        if len(starts) > max_patches:
            starts = [starts[int(i)] for i in np.linspace(0, len(starts) - 1, max_patches)]
        feats = np.stack([self.logmel(wav[s:s + PATCH])[:96] for s in starts])
        out = []
        for i in range(0, len(feats), 8):
            out.append(self.patches_scores(feats[i:i + 8]))
        return np.concatenate(out)

    def scores_emb(self, wav, max_patches=400):
        """Alle Fenster der Reihe nach (kein Ausduennen, damit die Zeiten stimmen): (Scores, Embeddings)."""
        wav = np.asarray(wav, dtype=np.float32)
        if len(wav) < PATCH:
            wav = np.pad(wav, (0, PATCH - len(wav)))
        starts = list(range(0, len(wav) - PATCH + 1, HOP))[:max_patches]
        feats = np.stack([self.logmel(wav[s:s + PATCH])[:96] for s in starts])
        sc, em = [], []
        for i in range(0, len(feats), 8):
            a, b = self.patches_scores_emb(feats[i:i + 8]); sc.append(a); em.append(b)
        return np.concatenate(sc), np.concatenate(em)
