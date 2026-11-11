"""
Krypt Vault - Live Browser Face Scanner Component
=================================================

Bidirectional Streamlit Components v2 HUD camera scanner using browser
``getUserMedia`` with real-time framing, luminance, and motion-stability
analysis in the center facial ROI before auto-locking a snapshot for
``modules.auth_biometric``.
"""

from __future__ import annotations

import base64
import binascii
from typing import Optional

import streamlit as st

_MAX_CAPTURE_BYTES = 10 * 1024 * 1024

_SCANNER_HTML = """
<div class="kv-scan-wrap">
  <div id="stage" class="kv-stage is-idle">
    <video id="video" autoplay playsinline muted></video>
    <img id="snapshot" alt="Pratinjau wajah terkunci" />

    <div class="kv-hud">
      <div class="kv-corner tl"></div>
      <div class="kv-corner tr"></div>
      <div class="kv-corner bl"></div>
      <div class="kv-corner br"></div>

      <div id="reticle" class="kv-reticle">
        <div class="kv-face-ring"></div>
        <div id="laser" class="kv-laser"></div>
      </div>

      <div class="kv-top-bar">
        <span id="badge" class="kv-badge">STANDBY</span>
        <span id="telemetry" class="kv-telemetry">LUX -- // STABIL --%</span>
      </div>
    </div>

    <div id="errorBox" class="kv-overlay" hidden>
      <div class="kv-err-title">AKSES KAMERA TIDAK TERSEDIA</div>
      <div id="errorMsg" class="kv-err-msg"></div>
      <button id="btnRetry" type="button" class="kv-btn kv-btn-primary">Coba Lagi</button>
    </div>
  </div>

  <div class="kv-meter-row">
    <div class="kv-meter-track">
      <div id="progressFill" class="kv-meter-fill"></div>
    </div>
    <span id="progressText" class="kv-meter-pct">0%</span>
  </div>

  <div class="kv-footer">
    <span id="hint" class="kv-hint">Menginisialisasi sensor kamera...</span>
    <div class="kv-actions">
      <button id="btnCapture" type="button" class="kv-btn kv-btn-cyan" hidden>Pindai Sekarang</button>
      <button id="btnRescan" type="button" class="kv-btn kv-btn-primary" hidden>Pindai Ulang</button>
    </div>
  </div>
</div>
"""

_SCANNER_CSS = """
:host {
  display: block;
  width: 100%;
  font-family: 'Plus Jakarta Sans', 'Segoe UI', sans-serif;
  color: #EFE8EA;
}
*, *::before, *::after { box-sizing: border-box; }

.kv-scan-wrap {
  background: #050506;
  border: 1px solid rgba(255, 82, 102, 0.42);
  clip-path: polygon(0 0, calc(100% - 10px) 0, 100% 10px, 100% 100%, 10px 100%, 0 calc(100% - 10px));
  padding: 10px;
}

.kv-stage {
  position: relative;
  width: 100%;
  aspect-ratio: 4 / 3;
  max-height: 295px;
  background: radial-gradient(circle at 50% 45%, #121520 0%, #050506 82%);
  overflow: hidden;
  border: 1px solid rgba(70, 238, 227, 0.25);
}

.kv-stage video,
.kv-stage img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.kv-stage video {
  transform: scaleX(-1);
}

.kv-stage img {
  display: none;
}

.kv-stage.is-locked video {
  display: none;
}
.kv-stage.is-locked img {
  display: block;
}

.kv-hud {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.kv-corner {
  position: absolute;
  width: 16px;
  height: 16px;
  border-color: #46EEE3;
  border-style: solid;
  opacity: 0.85;
  transition: border-color 0.2s ease;
}
.kv-corner.tl { top: 10px; left: 10px; border-width: 2px 0 0 2px; }
.kv-corner.tr { top: 10px; right: 10px; border-width: 2px 2px 0 0; }
.kv-corner.bl { bottom: 10px; left: 10px; border-width: 0 0 2px 2px; }
.kv-corner.br { bottom: 10px; right: 10px; border-width: 0 2px 2px 0; }

.kv-stage.is-locked .kv-corner {
  border-color: #00FF9D;
}

.kv-reticle {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 44%;
  height: 66%;
  transform: translate(-50%, -50%);
  overflow: hidden;
}

.kv-face-ring {
  position: absolute;
  inset: 0;
  border: 1.5px dashed rgba(70, 238, 227, 0.65);
  border-radius: 48% 48% 45% 45% / 44% 44% 56% 56%;
  box-shadow: inset 0 0 18px rgba(70, 238, 227, 0.10);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.kv-stage.is-locking .kv-face-ring {
  border-style: solid;
  border-color: #FCEE0A;
  box-shadow: inset 0 0 22px rgba(252, 238, 10, 0.18), 0 0 14px rgba(252, 238, 10, 0.25);
}

.kv-stage.is-locked .kv-face-ring {
  border-style: solid;
  border-color: #00FF9D;
  box-shadow: inset 0 0 22px rgba(0, 255, 157, 0.22);
}

.kv-laser {
  display: none;
  position: absolute;
  left: 4%;
  right: 4%;
  height: 2px;
  background: linear-gradient(90deg, transparent, #46EEE3, #FCEE0A, #46EEE3, transparent);
  box-shadow: 0 0 10px rgba(70, 238, 227, 0.85);
  animation: kv-sweep 1.8s ease-in-out infinite;
}

.kv-stage.is-scanning .kv-laser,
.kv-stage.is-locking .kv-laser {
  display: block;
}

@keyframes kv-sweep {
  0% { top: 8%; opacity: 0.35; }
  50% { top: 88%; opacity: 1; }
  100% { top: 8%; opacity: 0.35; }
}

.kv-top-bar {
  position: absolute;
  top: 10px;
  left: 32px;
  right: 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.kv-badge,
.kv-telemetry {
  font-family: 'IBM Plex Mono', 'Consolas', monospace;
  font-size: 10px;
  letter-spacing: 0.08em;
  padding: 2px 7px;
  background: rgba(5, 5, 6, 0.78);
  border: 1px solid rgba(70, 238, 227, 0.45);
  color: #46EEE3;
}

.kv-stage.is-locking .kv-badge {
  border-color: rgba(252, 238, 10, 0.85);
  color: #FCEE0A;
}

.kv-stage.is-locked .kv-badge {
  border-color: rgba(0, 255, 157, 0.85);
  color: #00FF9D;
}

.kv-overlay {
  position: absolute;
  inset: 0;
  background: rgba(5, 5, 6, 0.90);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 18px;
  gap: 10px;
}
.kv-overlay[hidden] {
  display: none;
}
.kv-err-title {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: #FF5266;
}
.kv-err-msg {
  font-size: 12px;
  line-height: 1.45;
  color: #D2C7CB;
  max-width: 320px;
}

.kv-meter-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 8px;
}
.kv-meter-track {
  flex: 1;
  height: 6px;
  background: #171215;
  border: 1px solid rgba(255, 82, 102, 0.30);
  overflow: hidden;
}
.kv-meter-fill {
  width: 0%;
  height: 100%;
  background: linear-gradient(90deg, #46EEE3, #FCEE0A);
  transition: width 0.12s linear, background 0.2s ease;
}
.kv-meter-fill.done {
  background: #00FF9D;
}
.kv-meter-pct {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 11px;
  min-width: 36px;
  text-align: right;
  color: #46EEE3;
}

.kv-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-top: 8px;
  min-height: 30px;
}
.kv-hint {
  font-size: 12px;
  color: #B8AFB3;
  line-height: 1.35;
}
.kv-actions {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.kv-btn {
  font-family: 'IBM Plex Mono', 'Segoe UI', monospace;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  padding: 6px 11px;
  border: 1px solid;
  background: #0D0A0C;
  cursor: pointer;
  clip-path: polygon(0 0, calc(100% - 6px) 0, 100% 6px, 100% 100%, 6px 100%, 0 calc(100% - 6px));
  transition: background 0.15s ease, color 0.15s ease;
}
.kv-btn[hidden] {
  display: none;
}
.kv-btn-primary {
  border-color: #FCEE0A;
  background: #FCEE0A;
  color: #050506;
}
.kv-btn-primary:hover {
  background: #46EEE3;
  border-color: #46EEE3;
}
.kv-btn-cyan {
  border-color: rgba(70, 238, 227, 0.7);
  color: #46EEE3;
}
.kv-btn-cyan:hover {
  background: rgba(70, 238, 227, 0.16);
}
"""

_SCANNER_JS = """
export default function(component) {
  const { parentElement, setStateValue } = component;
  if (typeof parentElement.__kvCleanup === 'function') {
    try { parentElement.__kvCleanup(); } catch (_) {}
  }
  const qs = (id) => parentElement.getElementById(id);

  const stage = qs('stage');
  const video = qs('video');
  const snapshot = qs('snapshot');
  const badge = qs('badge');
  const telemetry = qs('telemetry');
  const progressFill = qs('progressFill');
  const progressText = qs('progressText');
  const hint = qs('hint');
  const errorBox = qs('errorBox');
  const errorMsg = qs('errorMsg');
  const btnCapture = qs('btnCapture');
  const btnRescan = qs('btnRescan');
  const btnRetry = qs('btnRetry');

  const roiCanvas = document.createElement('canvas');
  roiCanvas.width = 48;
  roiCanvas.height = 48;
  const roiCtx = roiCanvas.getContext('2d', { willReadFrequently: true });

  const capCanvas = document.createElement('canvas');
  const capCtx = capCanvas.getContext('2d');

  let alive = true;
  let stream = null;
  let starting = false;
  let locked = Boolean(parentElement.__kvLocked && snapshot.getAttribute('src'));
  let scanTimer = null;
  let visTimer = null;
  let prevFrame = null;
  let lockScore = 0;
  let startedAt = 0;
  let seq = Number(parentElement.__kvSeq || 0);

  const isVisible = () => {
    const host = parentElement.host || stage;
    if (!host || !host.isConnected || document.hidden) return false;
    const rect = host.getBoundingClientRect();
    return rect.width > 20 && rect.height > 20;
  };

  const setMode = (cls, badgeTxt, hintTxt) => {
    stage.classList.remove('is-idle', 'is-scanning', 'is-locking', 'is-locked');
    stage.classList.add(cls);
    badge.textContent = badgeTxt;
    hint.textContent = hintTxt;
  };

  const setProgress = (pct, done = false) => {
    const clamped = Math.max(0, Math.min(100, Math.round(pct)));
    progressFill.style.width = `${clamped}%`;
    progressFill.classList.toggle('done', done);
    progressText.textContent = `${clamped}%`;
  };

  const stopLoop = () => {
    if (scanTimer !== null) {
      clearInterval(scanTimer);
      scanTimer = null;
    }
  };

  const stopStream = () => {
    stopLoop();
    if (stream) {
      stream.getTracks().forEach((track) => {
        try { track.stop(); } catch (_) {}
      });
      stream = null;
    }
    video.srcObject = null;
  };

  const lockFrame = () => {
    if (!alive || locked || !video.videoWidth || !video.videoHeight) return;
    const maxW = 640;
    const scale = Math.min(1, maxW / video.videoWidth);
    const w = Math.max(160, Math.round(video.videoWidth * scale));
    const h = Math.max(120, Math.round(video.videoHeight * scale));
    capCanvas.width = w;
    capCanvas.height = h;
    capCtx.save();
    capCtx.translate(w, 0);
    capCtx.scale(-1, 1);
    capCtx.drawImage(video, 0, 0, w, h);
    capCtx.restore();

    const dataUrl = capCanvas.toDataURL('image/jpeg', 0.92);
    locked = true;
    parentElement.__kvLocked = true;
    stopStream();

    snapshot.src = dataUrl;
    setMode('is-locked', 'TERKUNCI // SIAP', 'Citra wajah berhasil dikunci otomatis.');
    telemetry.textContent = 'LOCKED // 100%';
    setProgress(100, true);
    btnCapture.hidden = true;
    btnRescan.hidden = false;

    seq += 1;
    parentElement.__kvSeq = seq;
    setStateValue('capture', {
      dataUrl,
      captureId: `${Date.now()}-${seq}`,
    });
  };

  const analyzeStep = () => {
    if (!alive || locked || !stream || video.readyState < 2 || !video.videoWidth) return;
    if (!isVisible()) {
      stopStream();
      setMode('is-idle', 'JEDA TAB', 'Berpindah kembali ke tab untuk memindai.');
      return;
    }

    const vw = video.videoWidth;
    const vh = video.videoHeight;
    const sx = Math.round(vw * 0.25);
    const sy = Math.round(vh * 0.16);
    const sw = Math.max(32, Math.round(vw * 0.50));
    const sh = Math.max(32, Math.round(vh * 0.68));
    roiCtx.drawImage(video, sx, sy, sw, sh, 0, 0, 48, 48);

    const data = roiCtx.getImageData(0, 0, 48, 48).data;
    const n = 48 * 48;
    const lumaArr = new Float32Array(n);
    let sum = 0;
    for (let i = 0; i < n; i++) {
      const o = i * 4;
      const y = 0.299 * data[o] + 0.587 * data[o + 1] + 0.114 * data[o + 2];
      lumaArr[i] = y;
      sum += y;
    }
    const mean = sum / n;
    let varSum = 0;
    let motionSum = 0;
    for (let i = 0; i < n; i++) {
      const d = lumaArr[i] - mean;
      varSum += d * d;
      if (prevFrame) motionSum += Math.abs(lumaArr[i] - prevFrame[i]);
    }
    const std = Math.sqrt(varSum / n);
    const motion = prevFrame ? motionSum / n : 99;
    prevFrame = lumaArr;

    const elapsed = performance.now() - startedAt;
    const lightingOk = mean >= 26 && std >= 11;
    const steady = lightingOk && motion < 12.5;

    if (elapsed < 600) {
      lockScore = Math.max(0, lockScore);
      setMode('is-scanning', 'KALIBRASI...', 'Arahkan wajah ke dalam bingkai bidik.');
    } else if (!lightingOk) {
      lockScore = Math.max(0, lockScore - 16);
      setMode('is-scanning', 'CAHAYA KURANG', 'Pastikan wajah cukup terang & lensa tidak tertutup.');
    } else if (steady) {
      lockScore = Math.min(100, lockScore + 14);
      setMode('is-locking', 'PINDAI WAJAH...', 'Tahan posisi sebentar, mengunci otomatis...');
    } else {
      lockScore = Math.max(0, lockScore - 10);
      setMode('is-scanning', 'TAHAN POSISI', 'Posisikan wajah tenang di dalam bingkai oval.');
    }

    const stabilityPct = Math.max(0, Math.min(100, Math.round(100 - motion * 4)));
    telemetry.textContent = `LUX ${Math.round(mean)} // STABIL ${stabilityPct}%`;
    setProgress(lockScore, false);

    if (lockScore >= 100) {
      lockFrame();
    }
  };

  const startScanner = async () => {
    if (!alive || locked || starting || stream || !isVisible()) return;
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      errorBox.hidden = false;
      errorMsg.textContent = 'Browser/webview ini tidak mendukung akses kamera langsung. Gunakan tab Unggah foto.';
      setMode('is-idle', 'NONAKTIF', 'Gunakan opsi Unggah foto untuk melanjutkan.');
      return;
    }

    starting = true;
    errorBox.hidden = true;
    btnCapture.hidden = true;
    btnRescan.hidden = true;
    prevFrame = null;
    lockScore = 0;
    setProgress(0, false);
    setMode('is-idle', 'MENGHUBUNGKAN...', 'Meminta akses kamera perangkat...');

    try {
      const s = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
        audio: false,
      });
      if (!alive || locked || !isVisible()) {
        s.getTracks().forEach((t) => { try { t.stop(); } catch (_) {} });
        starting = false;
        return;
      }
      stream = s;
      video.srcObject = s;
      await video.play().catch(() => {});
      startedAt = performance.now();
      btnCapture.hidden = false;
      setMode('is-scanning', 'PINDAI AKTIF', 'Arahkan wajah ke tengah bingkai hingga terkunci.');
      scanTimer = setInterval(analyzeStep, 130);
    } catch (err) {
      errorBox.hidden = false;
      const msg = (err && err.message) ? err.message : 'Izin kamera ditolak atau tidak ada webcam.';
      errorMsg.textContent = `${msg}. Izinkan kamera atau beralih ke tab Unggah foto.`;
      setMode('is-idle', 'KAMERA TERBLOKIR', 'Kamera gagal diakses.');
    } finally {
      starting = false;
    }
  };

  const rescan = () => {
    locked = false;
    parentElement.__kvLocked = false;
    lockScore = 0;
    prevFrame = null;
    snapshot.removeAttribute('src');
    setProgress(0, false);
    setStateValue('capture', null);
    startScanner();
  };

  btnCapture.onclick = lockFrame;
  btnRescan.onclick = rescan;
  btnRetry.onclick = startScanner;

  const hostEl = parentElement.host || stage;
  const obs = new IntersectionObserver((entries) => {
    const visibleNow = entries.some((e) => e.isIntersecting) && isVisible();
    if (visibleNow && !locked && !stream) {
      startScanner();
    } else if (!visibleNow && stream) {
      stopStream();
      if (!locked) setMode('is-idle', 'JEDA TAB', 'Kamera dijeda saat tab tidak aktif.');
    }
  }, { threshold: 0.05 });
  obs.observe(hostEl);

  const onVisChange = () => {
    if (document.hidden) {
      if (stream) stopStream();
    } else if (!locked && !stream && isVisible()) {
      startScanner();
    }
  };
  document.addEventListener('visibilitychange', onVisChange);

  visTimer = setInterval(() => {
    if (!alive || locked) return;
    if (isVisible() && !stream && !starting && errorBox.hidden) {
      startScanner();
    } else if (!isVisible() && stream) {
      stopStream();
    }
  }, 500);

  if (locked) {
    setMode('is-locked', 'TERKUNCI // SIAP', 'Citra wajah berhasil dikunci otomatis.');
    telemetry.textContent = 'LOCKED // 100%';
    setProgress(100, true);
    btnCapture.hidden = true;
    btnRescan.hidden = false;
  } else if (isVisible()) {
    startScanner();
  } else {
    setMode('is-idle', 'STANDBY', 'Membuka kamera otomatis saat tab ini aktif.');
  }

  const cleanup = () => {
    alive = false;
    stopStream();
    obs.disconnect();
    document.removeEventListener('visibilitychange', onVisChange);
    if (visTimer !== null) clearInterval(visTimer);
  };
  parentElement.__kvCleanup = cleanup;
  return cleanup;
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
    """Decode a JPEG/PNG base64 data URL returned by the live scanner."""
    if not isinstance(data_url, str) or not data_url.startswith("data:image/"):
        return None
    header, sep, b64_payload = data_url.partition(",")
    if not sep or ";base64" not in header.lower():
        return None
    try:
        raw = base64.b64decode(b64_payload, validate=True)
    except (binascii.Error, ValueError):
        return None
    if not raw or len(raw) > _MAX_CAPTURE_BYTES:
        return None
    return raw


def render_live_face_scanner(key: str) -> tuple[Optional[bytes], Optional[str]]:
    """Mount the live HUD face scanner and return ``(image_bytes, capture_id)``."""
    cache_key = f"{key}_live_cache"
    result = _FACE_SCANNER(
        key=f"{key}_live",
        default={"capture": None},
        on_capture_change=lambda: None,
        width="stretch",
    )
    payload = getattr(result, "capture", None)
    if isinstance(payload, dict):
        capture_id = str(payload.get("captureId") or "")
        cached = st.session_state.get(cache_key)
        if cached and cached[0] == capture_id:
            return cached[1], capture_id
        img_bytes = _decode_data_url(payload.get("dataUrl"))
        if img_bytes:
            st.session_state[cache_key] = (capture_id, img_bytes)
            return img_bytes, capture_id
    else:
        st.session_state.pop(cache_key, None)
    return None, None


def clear_live_cache(key: str) -> None:
    """Clear any cached snapshot bytes when switching capture mode."""
    st.session_state.pop(f"{key}_live_cache", None)
