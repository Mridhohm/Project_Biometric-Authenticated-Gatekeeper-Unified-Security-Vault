"""
Live Biometric Face Scanner (Streamlit Components v2).
=====================================================
Komponen HTML/CSS/JS native berbasis ``st.components.v2`` yang menjaga aliran
kamera webcam tetap **live secara kontinu** dengan deteksi keberadaan wajah,
kotak pelacak HUD real-time, serta umpan balik kemiripan langsung tanpa perlu
membekukan layar menjadi foto statis ("live scan", bukan "live take").
"""

from __future__ import annotations

import base64
import binascii
import json
import time
from typing import Optional

import streamlit as st

_MAX_CAPTURE_BYTES = 10 * 1024 * 1024  # 10 MB batas aman payload base64

_SCANNER_HTML = """
<div class="kv-cam-shell" data-state="boot">
  <div class="kv-cam-head">
    <div class="kv-cam-title">
      <span class="kv-live-dot"></span>
      <span class="kv-mode-label">LIVE FACE SCANNER</span>
    </div>
    <span class="kv-cam-badge">MENGHUBUNGKAN...</span>
  </div>

  <div class="kv-cam-stage">
    <video class="kv-cam-video" autoplay playsinline muted></video>
    <canvas class="kv-hud-canvas"></canvas>

    <div class="kv-cam-placeholder" hidden>
      <div class="kv-ph-title">Kamera Tidak Tersedia</div>
      <div class="kv-ph-sub">Izinkan akses webcam pada browser atau alihkan sumber citra ke mode Unggah foto.</div>
    </div>
  </div>

  <div class="kv-meter-wrap" hidden>
    <div class="kv-meter-track">
      <div class="kv-meter-fill"></div>
      <div class="kv-meter-thresh"></div>
    </div>
    <span class="kv-meter-label">0%</span>
  </div>

  <div class="kv-cam-foot">
    <div class="kv-cam-hint">Menunggu izin kamera browser...</div>
    <div class="kv-cam-actions">
      <button type="button" class="kv-btn kv-btn-ghost kv-btn-pause" hidden>Jeda</button>
      <button type="button" class="kv-btn kv-btn-primary kv-btn-snap" hidden>Kunci Sampel</button>
      <button type="button" class="kv-btn kv-btn-ghost kv-btn-retry" hidden>Coba Lagi</button>
    </div>
  </div>

  <canvas class="kv-cam-work" hidden></canvas>
  <canvas class="kv-cam-analysis" hidden></canvas>
</div>
"""

_SCANNER_CSS = """
:host {
  display: block;
  width: 100%;
  font-family: "Inter", "Segoe UI", system-ui, -apple-system, sans-serif;
  color: #EFE8EA;
}

* {
  box-sizing: border-box;
}

.kv-cam-shell {
  background: linear-gradient(180deg, rgba(16, 19, 24, 0.96), rgba(9, 10, 14, 0.98));
  border: 1px solid rgba(70, 238, 227, 0.30);
  border-radius: 12px;
  padding: 12px;
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.48), inset 0 1px 0 rgba(70, 238, 227, 0.08);
  transition: border-color 0.25s ease, box-shadow 0.25s ease;
}

.kv-cam-shell[data-tone="ok"] {
  border-color: rgba(0, 255, 157, 0.78);
  box-shadow: 0 0 26px rgba(0, 255, 157, 0.16);
}

.kv-cam-shell[data-tone="scan"] {
  border-color: rgba(70, 238, 227, 0.72);
  box-shadow: 0 0 22px rgba(70, 238, 227, 0.14);
}

.kv-cam-shell[data-tone="warn"] {
  border-color: rgba(252, 238, 10, 0.65);
}

.kv-cam-shell[data-tone="error"] {
  border-color: rgba(255, 82, 102, 0.78);
  box-shadow: 0 0 20px rgba(255, 82, 102, 0.14);
}

.kv-cam-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 10px;
}

.kv-cam-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 0.74rem;
  font-weight: 700;
  letter-spacing: 0.09em;
  text-transform: uppercase;
  color: #B4BECB;
}

.kv-live-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #46EEE3;
  box-shadow: 0 0 9px #46EEE3;
  animation: kv-pulse 1.3s ease-in-out infinite;
}

.kv-cam-shell[data-tone="ok"] .kv-live-dot {
  background: #00FF9D;
  box-shadow: 0 0 10px #00FF9D;
}

.kv-cam-shell[data-tone="warn"] .kv-live-dot {
  background: #FCEE0A;
  box-shadow: 0 0 9px #FCEE0A;
}

.kv-cam-shell[data-tone="error"] .kv-live-dot,
.kv-cam-shell[data-state="paused"] .kv-live-dot,
.kv-cam-shell[data-state="error"] .kv-live-dot {
  background: #FF5266;
  box-shadow: 0 0 9px #FF5266;
  animation: none;
}

@keyframes kv-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.45; transform: scale(0.84); }
}

.kv-cam-badge {
  font-family: "JetBrains Mono", "Consolas", monospace;
  font-size: 0.69rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  padding: 3px 9px;
  border-radius: 999px;
  background: rgba(70, 238, 227, 0.12);
  color: #46EEE3;
  border: 1px solid rgba(70, 238, 227, 0.36);
  white-space: nowrap;
}

.kv-cam-shell[data-tone="ok"] .kv-cam-badge {
  background: rgba(0, 255, 157, 0.15);
  color: #00FF9D;
  border-color: rgba(0, 255, 157, 0.50);
}

.kv-cam-shell[data-tone="warn"] .kv-cam-badge {
  background: rgba(252, 238, 10, 0.13);
  color: #FCEE0A;
  border-color: rgba(252, 238, 10, 0.45);
}

.kv-cam-shell[data-tone="error"] .kv-cam-badge {
  background: rgba(255, 82, 102, 0.15);
  color: #FF7888;
  border-color: rgba(255, 82, 102, 0.48);
}

.kv-cam-stage {
  position: relative;
  width: 100%;
  aspect-ratio: 4 / 3;
  max-height: 360px;
  border-radius: 10px;
  overflow: hidden;
  background: radial-gradient(circle at 50% 45%, #121822 0%, #06070A 100%);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.kv-cam-video {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transform: scaleX(-1);
}

.kv-hud-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.kv-cam-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 20px;
  gap: 8px;
  background: rgba(8, 10, 14, 0.92);
  z-index: 3;
}

.kv-cam-placeholder[hidden] {
  display: none;
}

.kv-ph-title {
  font-size: 0.95rem;
  font-weight: 700;
  color: #FF7888;
}

.kv-ph-sub {
  font-size: 0.80rem;
  color: #8E9BAE;
  max-width: 310px;
  line-height: 1.45;
}

.kv-meter-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 9px;
}

.kv-meter-wrap[hidden] {
  display: none;
}

.kv-meter-track {
  position: relative;
  flex: 1;
  height: 6px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  overflow: hidden;
}

.kv-meter-fill {
  height: 100%;
  width: 0%;
  border-radius: 999px;
  background: linear-gradient(90deg, #46EEE3, #00FF9D);
  transition: width 0.22s ease, background 0.22s ease;
}

.kv-cam-shell[data-tone="error"] .kv-meter-fill {
  background: linear-gradient(90deg, #FF5266, #FCEE0A);
}

.kv-meter-thresh {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 70%;
  width: 2px;
  background: rgba(255, 255, 255, 0.55);
}

.kv-meter-label {
  font-family: "JetBrains Mono", "Consolas", monospace;
  font-size: 0.72rem;
  font-weight: 700;
  color: #C7D0DB;
  min-width: 44px;
  text-align: right;
}

.kv-cam-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-top: 10px;
  flex-wrap: wrap;
}

.kv-cam-hint {
  font-size: 0.79rem;
  color: #9CA7B5;
  flex: 1 1 200px;
  line-height: 1.35;
}

.kv-cam-actions {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.kv-btn {
  appearance: none;
  border-radius: 8px;
  padding: 6px 12px;
  font-size: 0.77rem;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid transparent;
  transition: background 0.16s ease, border-color 0.16s ease, transform 0.12s ease;
}

.kv-btn:active {
  transform: translateY(1px);
}

.kv-btn[hidden] {
  display: none;
}

.kv-btn-primary {
  background: rgba(70, 238, 227, 0.16);
  color: #46EEE3;
  border-color: rgba(70, 238, 227, 0.55);
}

.kv-btn-primary:hover {
  background: rgba(70, 238, 227, 0.25);
  border-color: #46EEE3;
}

.kv-btn-ghost {
  background: rgba(255, 255, 255, 0.05);
  color: #D5DCE4;
  border-color: rgba(255, 255, 255, 0.16);
}

.kv-btn-ghost:hover {
  background: rgba(255, 255, 255, 0.11);
  border-color: rgba(255, 255, 255, 0.30);
}
"""

_SCANNER_JS = r"""
export default function(component) {
  const { parentElement, data, setStateValue } = component;

  const kv = parentElement.__kv || (parentElement.__kv = {
    mounted: false,
    stream: null,
    rafId: null,
    paused: false,
    regLocked: false,
    regReadyMs: 0,
    lastFrameTs: 0,
    lastDetectTs: 0,
    lastEmitTs: 0,
    nativeDetector: null,
    nativeBusy: false,
    nativeFailed: false,
    faceDetected: false,
    faceQuality: 0,
    faceBox: null,
    smoothBox: null,
    scanPhase: 0,
    data: {},
    setStateValue: null,
    dom: null,
    destroy: null,
    applyData: null,
  });

  kv.data = data || {};
  kv.setStateValue = setStateValue;

  const shell = parentElement.querySelector(".kv-cam-shell");
  if (!shell) return;

  const domChanged = !kv.dom || kv.dom.shell !== shell;
  if (domChanged) {
    kv.dom = {
      shell,
      modeLabel: shell.querySelector(".kv-mode-label"),
      badge: shell.querySelector(".kv-cam-badge"),
      video: shell.querySelector(".kv-cam-video"),
      hudCanvas: shell.querySelector(".kv-hud-canvas"),
      placeholder: shell.querySelector(".kv-cam-placeholder"),
      phTitle: shell.querySelector(".kv-ph-title"),
      phSub: shell.querySelector(".kv-ph-sub"),
      meterWrap: shell.querySelector(".kv-meter-wrap"),
      meterFill: shell.querySelector(".kv-meter-fill"),
      meterThresh: shell.querySelector(".kv-meter-thresh"),
      meterLabel: shell.querySelector(".kv-meter-label"),
      hint: shell.querySelector(".kv-cam-hint"),
      btnPause: shell.querySelector(".kv-btn-pause"),
      btnSnap: shell.querySelector(".kv-btn-snap"),
      btnRetry: shell.querySelector(".kv-btn-retry"),
      workCanvas: shell.querySelector(".kv-cam-work"),
      analysisCanvas: shell.querySelector(".kv-cam-analysis"),
    };
  }

  const d = kv.dom;
  const ctxWork = d.workCanvas.getContext("2d");
  const ctxAna = d.analysisCanvas.getContext("2d", { willReadFrequently: true });
  const ctxHud = d.hudCanvas.getContext("2d");

  function setTone(tone, badgeText, hintText) {
    d.shell.dataset.tone = tone;
    d.badge.textContent = badgeText;
    if (hintText !== undefined) {
      d.hint.textContent = hintText;
    }
  }

  function updateMeter() {
    const cfg = kv.data || {};
    const thresh = Number.isFinite(cfg.threshold) ? cfg.threshold : 70;
    d.meterThresh.style.left = `${Math.max(10, Math.min(95, thresh))}%`;

    if (cfg.mode === "login" && Number.isFinite(cfg.sim)) {
      const pct = Math.max(0, Math.min(100, Math.round(cfg.sim)));
      d.meterWrap.hidden = false;
      d.meterFill.style.width = `${pct}%`;
      d.meterLabel.textContent = `${pct}%`;
      return;
    }

    if (kv.stream && !kv.paused) {
      const pct = Math.max(0, Math.min(100, Math.round(kv.faceQuality * 100)));
      d.meterWrap.hidden = false;
      d.meterFill.style.width = `${pct}%`;
      d.meterLabel.textContent = kv.faceDetected ? "SIAP" : "CARI";
      return;
    }

    d.meterWrap.hidden = true;
  }

  function refreshHudStatus() {
    const cfg = kv.data || {};
    const mode = cfg.mode === "register" ? "register" : "login";
    const ready = cfg.ready !== false;
    const thresh = Number.isFinite(cfg.threshold) ? cfg.threshold : 70;
    const hasSim = Number.isFinite(cfg.sim);

    d.modeLabel.textContent = mode === "register"
      ? "LIVE FACE SCAN // DAFTAR"
      : "LIVE FACE SCAN // MASUK";

    if (!kv.stream) {
      d.btnPause.hidden = true;
      d.btnSnap.hidden = true;
      return;
    }

    d.btnPause.hidden = false;
    d.btnPause.textContent = kv.paused ? "Lanjutkan" : "Jeda";

    if (mode === "register") {
      d.btnSnap.hidden = false;
      d.btnSnap.textContent = kv.regLocked ? "Perbarui Sampel" : "Kunci Sampel";
    } else {
      d.btnSnap.hidden = !ready;
      d.btnSnap.textContent = "Pindai Sekarang";
    }

    if (kv.paused) {
      d.shell.dataset.state = "paused";
      setTone("warn", "DIJEDA", "Pemindaian live dijeda. Klik Lanjutkan untuk memindai ulang.");
      updateMeter();
      return;
    }

    d.shell.dataset.state = "live";

    if (mode === "login") {
      if (!ready) {
        setTone(
          "warn",
          kv.faceDetected ? "SIAP // ISI KREDENSIAL" : "MENUNGGU KREDENSIAL",
          "Isi Nama pengguna dan Kata sandi (tekan Enter), kamera tetap memindai secara live."
        );
      } else if (hasSim && cfg.sim >= thresh) {
        setTone("ok", `COCOK ${Math.round(cfg.sim)}%`, "Identitas biometrik terverifikasi. Membuka Vault...");
      } else if (cfg.note && !hasSim) {
        setTone("error", "VERIFIKASI DITOLAK", cfg.note);
      } else if (hasSim && kv.faceDetected) {
        const pct = Math.round(cfg.sim);
        setTone(
          "error",
          `KEMIRIPAN ${pct}%`,
          cfg.note || `Pindai live aktif (${pct}% dari minimum ${thresh}%). Posisikan wajah tegak dan jelas.`
        );
      } else if (kv.faceDetected) {
        setTone("scan", "MEMINDAI LIVE...", "Wajah terdeteksi — mencocokkan vektor biometrik secara langsung...");
      } else {
        setTone("warn", "CARI WAJAH", "Posisikan wajah di tengah bingkai untuk pemindaian live otomatis.");
      }
    } else {
      if (kv.regLocked) {
        setTone(
          "ok",
          "SAMPEL TERSEDIA // LIVE",
          "Sampel wajah tersimpan sambil kamera tetap live. Klik Perbarui Sampel jika ingin mengulang."
        );
      } else if (kv.faceDetected) {
        setTone(
          "scan",
          "WAJAH TERDETEKSI",
          "Wajah terkunci di area pindai — menahan posisi sejenak untuk sampel optimal..."
        );
      } else {
        setTone("warn", "ARAHKAN WAJAH", "Hadapkan wajah ke tengah bingkai atau klik Kunci Sampel.");
      }
    }

    updateMeter();
  }

  kv.applyData = refreshHudStatus;

  function emitLiveFrame(force = false) {
    if (!kv.stream || kv.paused || d.video.readyState < 2) return;
    if (!d.video.videoWidth || !d.video.videoHeight) return;
    if (!force && !kv.faceDetected) return;

    const tw = 480;
    const th = 360;
    if (d.workCanvas.width !== tw || d.workCanvas.height !== th) {
      d.workCanvas.width = tw;
      d.workCanvas.height = th;
    }

    const vw = d.video.videoWidth;
    const vh = d.video.videoHeight;
    const targetAspect = tw / th;
    const srcAspect = vw / vh;
    let sx = 0, sy = 0, sw = vw, sh = vh;
    if (srcAspect > targetAspect) {
      sw = Math.round(vh * targetAspect);
      sx = Math.round((vw - sw) / 2);
    } else {
      sh = Math.round(vw / targetAspect);
      sy = Math.round((vh - sh) / 2);
    }

    ctxWork.drawImage(d.video, sx, sy, sw, sh, 0, 0, tw, th);
    const dataUrl = d.workCanvas.toDataURL("image/jpeg", 0.85);
    const uid = `${force ? "m" : "a"}-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;

    if (typeof kv.setStateValue === "function") {
      kv.setStateValue("capture", JSON.stringify({ id: uid, ts: Date.now(), dataUrl }));
    }
    kv.lastEmitTs = performance.now();
  }

  function analyzeHeuristic() {
    const aw = 96;
    const ah = 72;
    if (d.analysisCanvas.width !== aw || d.analysisCanvas.height !== ah) {
      d.analysisCanvas.width = aw;
      d.analysisCanvas.height = ah;
    }
    ctxAna.drawImage(d.video, 0, 0, aw, ah);
    const img = ctxAna.getImageData(0, 0, aw, ah).data;

    let skinCount = 0;
    let centerTotal = 0;
    let lumaSum = 0;
    let gradSum = 0;
    let minX = aw, minY = ah, maxX = 0, maxY = 0;

    const x0 = Math.floor(aw * 0.22);
    const x1 = Math.floor(aw * 0.78);
    const y0 = Math.floor(ah * 0.14);
    const y1 = Math.floor(ah * 0.86);

    for (let y = y0; y < y1; y++) {
      for (let x = x0; x < x1; x++) {
        const i = (y * aw + x) * 4;
        const r = img[i];
        const g = img[i + 1];
        const b = img[i + 2];

        const yLuma = 0.299 * r + 0.587 * g + 0.114 * b;
        const cb = 128 - 0.168736 * r - 0.331264 * g + 0.5 * b;
        const cr = 128 + 0.5 * r - 0.418688 * g - 0.081312 * b;

        lumaSum += yLuma;
        centerTotal++;

        if (x + 1 < x1) {
          const iNext = i + 4;
          const yNext = 0.299 * img[iNext] + 0.587 * img[iNext + 1] + 0.114 * img[iNext + 2];
          gradSum += Math.abs(yLuma - yNext);
        }

        const isSkinCbCr = cb >= 72 && cb <= 133 && cr >= 131 && cr <= 183;
        const isWarmTone = r > 45 && g > 28 && r >= g * 0.94 && r > b * 1.04 && yLuma > 34 && yLuma < 236;
        if (isSkinCbCr || isWarmTone) {
          skinCount++;
          if (x < minX) minX = x;
          if (x > maxX) maxX = x;
          if (y < minY) minY = y;
          if (y > maxY) maxY = y;
        }
      }
    }

    if (centerTotal === 0) return { detected: false, quality: 0, box: null };

    const meanLuma = lumaSum / centerTotal;
    const meanGrad = gradSum / centerTotal;
    const skinRatio = skinCount / centerTotal;

    const goodLight = meanLuma >= 34 && meanLuma <= 232;
    const hasFeatures = meanGrad >= 2.6;
    const hasSkin = skinRatio >= 0.16;

    const quality = Math.min(
      1,
      Math.max(
        0,
        (goodLight ? 0.30 : 0.05) +
          Math.min(0.40, skinRatio * 1.05) +
          Math.min(0.30, meanGrad / 14)
      )
    );

    let box = null;
    if (hasSkin && hasFeatures && goodLight && maxX > minX && maxY > minY) {
      const padX = (maxX - minX) * 0.12;
      const padY = (maxY - minY) * 0.14;
      box = {
        x: Math.max(0.08, (minX - padX) / aw),
        y: Math.max(0.06, (minY - padY) / ah),
        w: Math.min(0.84, (maxX - minX + padX * 2) / aw),
        h: Math.min(0.88, (maxY - minY + padY * 2) / ah),
      };
    }

    return {
      detected: Boolean(box && quality >= 0.48),
      quality,
      box,
    };
  }

  function triggerDetect() {
    if (!kv.stream || d.video.readyState < 2 || !d.video.videoWidth) return;

    if ("FaceDetector" in window && !kv.nativeFailed && !kv.nativeBusy) {
      if (!kv.nativeDetector) {
        try {
          kv.nativeDetector = new window.FaceDetector({ fastMode: true, maxDetectedFaces: 1 });
        } catch (_e) {
          kv.nativeFailed = true;
        }
      }
      if (kv.nativeDetector) {
        kv.nativeBusy = true;
        kv.nativeDetector.detect(d.video)
          .then((faces) => {
            kv.nativeBusy = false;
            if (faces && faces.length > 0) {
              const bb = faces[0].boundingBox;
              const vw = d.video.videoWidth || 1;
              const vh = d.video.videoHeight || 1;
              kv.faceDetected = true;
              kv.faceQuality = 0.96;
              kv.faceBox = {
                x: Math.max(0.04, bb.x / vw),
                y: Math.max(0.04, bb.y / vh),
                w: Math.min(0.92, bb.width / vw),
                h: Math.min(0.92, bb.height / vh),
              };
            } else {
              const hRes = analyzeHeuristic();
              kv.faceDetected = hRes.detected;
              kv.faceQuality = hRes.quality;
              kv.faceBox = hRes.box;
            }
          })
          .catch(() => {
            kv.nativeBusy = false;
            kv.nativeFailed = true;
          });
        return;
      }
    }

    const res = analyzeHeuristic();
    kv.faceDetected = res.detected;
    kv.faceQuality = res.quality;
    kv.faceBox = res.box;
  }

  function drawHud(dtMs) {
    const rect = d.hudCanvas.getBoundingClientRect();
    const cw = Math.max(200, Math.round(rect.width || 480));
    const ch = Math.max(150, Math.round(rect.height || 360));
    if (d.hudCanvas.width !== cw || d.hudCanvas.height !== ch) {
      d.hudCanvas.width = cw;
      d.hudCanvas.height = ch;
    }

    ctxHud.clearRect(0, 0, cw, ch);
    if (!kv.stream) return;

    const cfg = kv.data || {};
    const tone = d.shell.dataset.tone || "scan";
    let stroke = "#46EEE3";
    let glow = "rgba(70, 238, 227, 0.25)";
    if (tone === "ok") {
      stroke = "#00FF9D";
      glow = "rgba(0, 255, 157, 0.30)";
    } else if (tone === "warn") {
      stroke = "#FCEE0A";
      glow = "rgba(252, 238, 10, 0.24)";
    } else if (tone === "error") {
      stroke = "#FF5266";
      glow = "rgba(255, 82, 102, 0.28)";
    }

    // Smooth mirrored target tracking box (video is mirrored via CSS scaleX(-1))
    if (kv.faceBox) {
      const mx = Math.max(0.04, 1 - (kv.faceBox.x + kv.faceBox.w));
      const target = { x: mx, y: kv.faceBox.y, w: kv.faceBox.w, h: kv.faceBox.h };
      if (!kv.smoothBox) {
        kv.smoothBox = target;
      } else {
        const k = Math.min(1, dtMs / 110);
        kv.smoothBox = {
          x: kv.smoothBox.x + (target.x - kv.smoothBox.x) * k,
          y: kv.smoothBox.y + (target.y - kv.smoothBox.y) * k,
          w: kv.smoothBox.w + (target.w - kv.smoothBox.w) * k,
          h: kv.smoothBox.h + (target.h - kv.smoothBox.h) * k,
        };
      }
    } else {
      kv.smoothBox = null;
    }

    const bx = kv.smoothBox ? kv.smoothBox.x * cw : cw * 0.27;
    const by = kv.smoothBox ? kv.smoothBox.y * ch : ch * 0.14;
    const bw = kv.smoothBox ? kv.smoothBox.w * cw : cw * 0.46;
    const bh = kv.smoothBox ? kv.smoothBox.h * ch : ch * 0.72;
    const cLen = Math.max(14, Math.min(28, Math.min(bw, bh) * 0.18));

    ctxHud.save();
    ctxHud.strokeStyle = stroke;
    ctxHud.lineWidth = kv.smoothBox ? 2.4 : 1.7;
    ctxHud.shadowColor = glow;
    ctxHud.shadowBlur = 10;

    // 4 corner tracking brackets
    ctxHud.beginPath();
    ctxHud.moveTo(bx, by + cLen); ctxHud.lineTo(bx, by); ctxHud.lineTo(bx + cLen, by);
    ctxHud.moveTo(bx + bw - cLen, by); ctxHud.lineTo(bx + bw, by); ctxHud.lineTo(bx + bw, by + cLen);
    ctxHud.moveTo(bx, by + bh - cLen); ctxHud.lineTo(bx, by + bh); ctxHud.lineTo(bx + cLen, by + bh);
    ctxHud.moveTo(bx + bw - cLen, by + bh); ctxHud.lineTo(bx + bw, by + bh); ctxHud.lineTo(bx + bw, by + bh - cLen);
    ctxHud.stroke();

    // Sweeping live laser beam when actively scanning
    if (!kv.paused && cfg.ready !== false) {
      kv.scanPhase = (kv.scanPhase + dtMs * 0.00055) % 1;
      const ly = by + kv.scanPhase * bh;
      const grad = ctxHud.createLinearGradient(bx, ly, bx + bw, ly);
      grad.addColorStop(0, "rgba(70, 238, 227, 0)");
      grad.addColorStop(0.5, stroke);
      grad.addColorStop(1, "rgba(70, 238, 227, 0)");
      ctxHud.strokeStyle = grad;
      ctxHud.lineWidth = 1.8;
      ctxHud.beginPath();
      ctxHud.moveTo(bx + 6, ly);
      ctxHud.lineTo(bx + bw - 6, ly);
      ctxHud.stroke();
    }

    // Subtle telemetry label attached to tracking frame
    ctxHud.shadowBlur = 0;
    ctxHud.font = '600 11px "JetBrains Mono", Consolas, monospace';
    ctxHud.fillStyle = stroke;
    let tag = kv.faceDetected ? "FACE LOCK // LIVE" : "SCANNING AREA...";
    if (cfg.mode === "login" && Number.isFinite(cfg.sim)) {
      tag = `MATCH ${Math.round(cfg.sim)}% // LIVE`;
    }
    ctxHud.fillText(tag, bx + 4, Math.max(16, by - 7));
    ctxHud.restore();
  }

  function tick(now) {
    if (!kv.mounted) return;
    const dtMs = kv.lastFrameTs ? Math.min(120, now - kv.lastFrameTs) : 16;
    kv.lastFrameTs = now;

    if (kv.stream && !kv.paused && d.video.readyState >= 2) {
      if (now - kv.lastDetectTs >= 140) {
        kv.lastDetectTs = now;
        triggerDetect();
        refreshHudStatus();
      }

      const cfg = kv.data || {};
      const mode = cfg.mode === "register" ? "register" : "login";

      if (mode === "login") {
        if (cfg.ready !== false && kv.faceDetected && now - kv.lastEmitTs >= 620) {
          emitLiveFrame(false);
        }
      } else if (!kv.regLocked) {
        if (kv.faceDetected && kv.faceQuality >= 0.56) {
          kv.regReadyMs += dtMs;
          if (kv.regReadyMs >= 950) {
            kv.regLocked = true;
            emitLiveFrame(true);
            refreshHudStatus();
          }
        } else {
          kv.regReadyMs = Math.max(0, kv.regReadyMs - dtMs * 1.4);
        }
      }
    }

    drawHud(dtMs);
    kv.rafId = requestAnimationFrame(tick);
  }

  async function ensureCamera() {
    if (kv.stream) {
      if (d.video.srcObject !== kv.stream) {
        d.video.srcObject = kv.stream;
        try { await d.video.play(); } catch (_e) {}
      }
      d.placeholder.hidden = true;
      d.btnRetry.hidden = true;
      refreshHudStatus();
      return;
    }

    d.placeholder.hidden = true;
    d.btnRetry.hidden = true;
    setTone("scan", "MENGHUBUNGKAN...", "Meminta izin akses webcam untuk pemindaian live...");

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      d.shell.dataset.state = "error";
      d.placeholder.hidden = false;
      d.phTitle.textContent = "Kamera Tidak Didukung";
      d.phSub.textContent = "Browser tidak menyediakan API kamera pada konteks ini. Gunakan Unggah foto.";
      setTone("error", "NO CAMERA API", "API kamera browser tidak tersedia.");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user", width: { ideal: 640 }, height: { ideal: 480 } },
        audio: false,
      });
      if (!kv.mounted) {
        stream.getTracks().forEach((t) => t.stop());
        return;
      }
      kv.stream = stream;
      d.video.srcObject = stream;
      await d.video.play();
      refreshHudStatus();
    } catch (err) {
      d.shell.dataset.state = "error";
      d.placeholder.hidden = false;
      d.btnRetry.hidden = false;
      const denied = err && (err.name === "NotAllowedError" || err.name === "PermissionDeniedError");
      d.phTitle.textContent = denied ? "Izin Kamera Ditolak" : "Kamera Gagal Dibuka";
      d.phSub.textContent = denied
        ? "Izinkan kamera pada ikon gembok/kamera di address bar browser lalu klik Coba Lagi."
        : "Pastikan webcam terhubung dan tidak sedang dipakai aplikasi lain.";
      setTone("error", denied ? "IZIN DITOLAK" : "KAMERA ERROR", "Akses webcam gagal.");
    }
  }

  function destroy() {
    kv.mounted = false;
    if (kv.rafId) {
      cancelAnimationFrame(kv.rafId);
      kv.rafId = null;
    }
    if (kv.stream) {
      kv.stream.getTracks().forEach((t) => t.stop());
      kv.stream = null;
    }
    if (d.video) {
      d.video.srcObject = null;
    }
  }

  kv.destroy = destroy;

  d.btnPause.onclick = () => {
    kv.paused = !kv.paused;
    refreshHudStatus();
  };

  d.btnSnap.onclick = () => {
    if (!kv.stream) return;
    if ((kv.data || {}).mode === "register") {
      kv.regLocked = true;
      kv.regReadyMs = 0;
    }
    emitLiveFrame(true);
    refreshHudStatus();
  };

  d.btnRetry.onclick = () => {
    ensureCamera();
  };

  if (!kv.mounted) {
    kv.mounted = true;
    kv.lastFrameTs = 0;
    ensureCamera();
    kv.rafId = requestAnimationFrame(tick);
  } else {
    ensureCamera();
  }

  refreshHudStatus();
  return destroy;
}
"""

_FACE_SCANNER = st.components.v2.component(
    "krypt_face_scanner",
    html=_SCANNER_HTML,
    css=_SCANNER_CSS,
    js=_SCANNER_JS,
    isolate_styles=True,
)


def _decode_data_url(data_url: object) -> Optional[bytes]:
    """Decode JPEG/PNG data-URL dari browser menjadi byte mentah yang valid."""
    if not isinstance(data_url, str) or "," not in data_url:
        return None
    header, b64_payload = data_url.split(",", 1)
    if "data:image/" not in header or ";base64" not in header:
        return None
    try:
        raw = base64.b64decode(b64_payload, validate=True)
    except (binascii.Error, ValueError):
        return None
    if not raw or len(raw) > _MAX_CAPTURE_BYTES:
        return None
    return raw


def _parse_capture_payload(raw_value: object) -> tuple[Optional[bytes], Optional[str]]:
    """Parse state ``capture`` dari komponen live JS menjadi ``(image_bytes, capture_id)``."""
    if isinstance(raw_value, str) and raw_value.startswith("{"):
        try:
            payload = json.loads(raw_value)
        except json.JSONDecodeError:
            return None, None
        img_bytes = _decode_data_url(payload.get("dataUrl"))
        cap_id = payload.get("id")
        if img_bytes and isinstance(cap_id, str):
            return img_bytes, cap_id
    elif isinstance(raw_value, dict):
        img_bytes = _decode_data_url(raw_value.get("dataUrl"))
        cap_id = raw_value.get("id")
        if img_bytes and isinstance(cap_id, str):
            return img_bytes, cap_id
    return None, None


def _get_cached_frame(cache_key: str, *, mode: str) -> tuple[Optional[bytes], Optional[str]]:
    """Kembalikan cache frame jika masih berlaku (mode login membatasi umur frame)."""
    cached = st.session_state.get(cache_key)
    if not cached:
        return None, None
    if mode == "login" and (time.time() - float(cached.get("ts") or 0.0) > 3.0):
        st.session_state.pop(cache_key, None)
        return None, None
    return cached["bytes"], cached["id"]


def render_live_face_scanner(
    key: str,
    *,
    mode: str = "login",
    ready: bool = True,
    similarity: Optional[float] = None,
    status_note: str = "",
    threshold: float = 0.70,
) -> tuple[Optional[bytes], Optional[str]]:
    """
    Render komponen pemindai wajah live secara kontinu di Streamlit.

    Selama ``mode == "login"``, kamera tetap aktif (live stream) tanpa membekukan
    tampilan menjadi foto statis, dan mengirimkan frame periodik ketika wajah
    terdeteksi serta ``ready`` bernilai ``True``.

    Returns
    -------
    tuple[Optional[bytes], Optional[str]]
        ``(image_bytes, capture_id)`` terbaru atau ``(None, None)`` jika belum ada frame.
    """
    resolved_mode = "register" if mode == "register" else "login"
    cache_key = f"{key}_live_cache"
    result = _FACE_SCANNER(
        key=f"{key}_live",
        data={
            "mode": resolved_mode,
            "ready": bool(ready),
            "sim": round(float(similarity) * 100.0, 1) if similarity is not None else None,
            "threshold": round(float(threshold) * 100.0),
            "note": str(status_note or ""),
        },
        default={"capture": None},
        on_capture_change=lambda: None,
        width="stretch",
    )

    raw_capture = result.get("capture") if isinstance(result, dict) else getattr(result, "capture", None)
    if raw_capture is None:
        return _get_cached_frame(cache_key, mode=resolved_mode)

    img_bytes, cap_id = _parse_capture_payload(raw_capture)
    if img_bytes and cap_id:
        st.session_state[cache_key] = {"bytes": img_bytes, "id": cap_id, "ts": time.time()}
        return img_bytes, cap_id

    return _get_cached_frame(cache_key, mode=resolved_mode)


def clear_live_cache(key: str) -> None:
    """Bersihkan cache frame live scanner pada session state."""
    st.session_state.pop(f"{key}_live_cache", None)
