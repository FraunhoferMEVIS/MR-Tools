# ===== File: gpu_bloch.py =====
"""GPU‑/CPU‑unterstützte Bloch‑Simulation mit optionalem 3‑D‑Fluss.

    + GPU‑Kernel (CUDA) für statische Spins
    + CPU/Numba‑Fallback, der pro Zeitschritt die Spins um einen Flow‑Vektor verschiebt
    + Die High‑Level‑Funktion `bloch_simulation` wählt automatisch den richtigen Pfad.

    Alle Eingabegrößen sind **SI‑Einheiten** (T, s, m) – intern wird ggf. skaliert.
"""

import math
import numpy as np
from numba import cuda, njit, prange

# Gyromagnetisches Verhältnis für ¹H in rad / T / s
GAMMA = 2 * math.pi * 42.57747892e6  # rad T⁻¹ s⁻¹
gamma = 2 * math.pi * 42.57747892e6  # rad T⁻¹ s⁻¹

# -----------------------------------------------------------------------------
# CUDA‑Kernel (keine Flow‑Unterstützung)  -------------------------------------
# -----------------------------------------------------------------------------
@cuda.jit
def _bloch_kernel(mx, my, mz,
                  b1r, b1i, g, dt,
                  T1, T2, df, pos,
                  mx0, my0, mz0,
                  mode):
    """Ein einfacher in‑place Bloch‑Kernel.

    Parameter
    ---------
    mx,my,mz : (N, Nt_out) float32
        Ausgabepuffer.
    b1r,b1i  : (Nt) float32
        Real‑ bzw. Imaginärteil von B1(t) in Tesla.
    g        : (3, Nt) float32
        Gradienten in T m⁻¹.
    dt       : (Nt) float32
        Zeitschritt zum *nächsten* Puls (s).
    mode     : int
        Bit 0 → initiale M v. mx0/my0/mz0 übernehmen,
        Bit 1 → Zeitverlauf in mx/my/mz speichern (sonst nur Endwert @0).
    """

    i = cuda.grid(1)
    if i >= mx.shape[0]:
        return

    # --- Anfangs‑Magnetisierung ---------------------------------------------
    Mx = mx0[i] if (mode & 1) else 0.0
    My = my0[i] if (mode & 1) else 0.0
    Mz = mz0[i] if (mode & 1) else 1.0

    # feste Position (GPU‑Kernel kennt keinen Flow) ---------------------------
    x0, y0, z0 = pos[i, 0], pos[i, 1], pos[i, 2]
    dfi  = df[i]  if df.shape[0] > 1 else df[0]
    T1i  = T1[i]  if T1.shape[0] > 1 else T1[0]
    T2i  = T2[i]  if T2.shape[0] > 1 else T2[0]

    for step in range(b1r.shape[0]):
        # B‑Feld an der Spin‑Position ----------------------------------------
        Bx = b1r[step]
        By = b1i[step]
        Gx, Gy, Gz = g[0, step], g[1, step], g[2, step]
        Bz = Gx*x0 + Gy*y0 + Gz*z0 + dfi / GAMMA

        # ---------------------------
        #   Z‑Rotation (precession)  
        # ---------------------------
        phi_z = GAMMA * Bz * dt[step]
        c, s  = math.cos(phi_z), math.sin(phi_z)
        Mx, My = Mx*c - My*s, Mx*s + My*c

        # ---------------------------
        #   RF‑Rotation in der XY‑Ebene
        # ---------------------------
        Bxy = math.sqrt(Bx*Bx + By*By)
        if Bxy > 0.0:
            phi_xy = GAMMA * Bxy * dt[step]
            ux, uy = Bx/Bxy, By/Bxy
            cxy, sxy = math.cos(phi_xy), math.sin(phi_xy)
            dot = Mx*ux + My*uy
            Mx = cxy*Mx + sxy*(uy*Mz) + (1.0-cxy)*dot*ux
            My = cxy*My - sxy*(ux*Mz) + (1.0-cxy)*dot*uy
            Mz = cxy*Mz + sxy*(ux*My - uy*Mx)

        # Relaxation ----------------------------------------------------------
        E1 = math.exp(-dt[step]/T1i)
        E2 = math.exp(-dt[step]/T2i)
        Mx *= E2; My *= E2
        Mz = 1.0 - (1.0 - Mz)*E1

        # evtl. Speichern -----------------------------------------------------
        if (mode & 2):
            mx[i, step] = Mx
            my[i, step] = My
            mz[i, step] = Mz

    # Nur Endzustand speichern? ----------------------------------------------
    if (mode & 2) == 0:
        mx[i, 0] = Mx
        my[i, 0] = My
        mz[i, 0] = Mz

# -----------------------------------------------------------------------------
# CPU‑/Numba‑Pfad MIT Flow ----------------------------------------------------
# -----------------------------------------------------------------------------
@njit(parallel=True)
def _bloch_cpu(mx_out, my_out, mz_out,
               b1r, b1i, g, dt,
               T1, T2, df, pos,
               flow, t_abs,
               mx0, my0, mz0,
               mode, sampling_idx):

    N = mx_out.shape[0]
    M = b1r.shape[0]
    for i in prange(N):
        Mx = mx0[i] if (mode & 1) else 0.0
        My = my0[i] if (mode & 1) else 0.0
        Mz = mz0[i] if (mode & 1) else 1.0

        # x0, y0, z0 = pos[i, 0], pos[i, 1], pos[i, 2]
        # vx, vy, vz = flow[i, 0], flow[i, 1], flow[i, 2]
        # print(i,vx,vy,vz)
        dfi = df[i] if df.shape[0] > 1 else df[0]
        T1i = T1[i] if T1.shape[0] > 1 else T1[0]
        T2i = T2[i] if T2.shape[0] > 1 else T2[0]
        store_i = 0
        for step in range(M):
            # t_rel = t_abs[step]
            Bx = b1r[step] 
            By = b1i[step] 
            Gx = g[0, step] 
            Gy = g[1, step] 
            Gz = g[2, step]
            # xi = x0 + vx*t_rel
            # yi = y0 + vy*t_rel
            # zi = z0 + vz*t_rel
            xi, yi, zi = pos[step, i, 0], pos[step, i, 1], pos[step, i, 2]
            Bz = Gx * xi + Gy * yi + Gz * zi + dfi / gamma

            angle_z = gamma * Bz * dt[step]
            cos_z = np.cos(angle_z)
            sin_z = np.sin(angle_z)
            Mx, My = Mx * cos_z - My * sin_z, Mx * sin_z + My * cos_z

            angle_xy = gamma * np.sqrt(Bx * Bx + By * By) * dt[step]
            if angle_xy > 0.0:
                ux = Bx / np.sqrt(Bx * Bx + By * By)
                uy = By / np.sqrt(Bx * Bx + By * By)
                cos_xy = np.cos(angle_xy)
                sin_xy = np.sin(angle_xy)
                dot = Mx * ux + My * uy
                Mx = cos_xy * Mx + sin_xy * (uy * Mz) + (1 - cos_xy) * dot * ux
                My = cos_xy * My - sin_xy * (ux * Mz) + (1 - cos_xy) * dot * uy
                Mz = cos_xy * Mz + sin_xy * (ux * My - uy * Mx)

            E1 = np.exp(-dt[step] / T1i)
            E2 = np.exp(-dt[step] / T2i)
            Mx *= E2
            My *= E2
            Mz = 1.0 - (1.0 - Mz) * E1

            if (mode & 2) and (step==sampling_idx[store_i]):
                mx_out[i, store_i] = Mx
                my_out[i, store_i] = My
                mz_out[i, store_i] = Mz
                store_i += 1

        # pos[i, 0], pos[i, 1], pos[i, 2] = xi,yi,zi

        if (mode & 2) == 0:
            mx_out[i, 0] = Mx
            my_out[i, 0] = My
            mz_out[i, 0] = Mz
    return 

def _bloch_cpu_flow(mx_out, my_out, mz_out,
               b1r, b1i, g, dt,
               T1, T2, df, pos,
               flow, t_abs,
               mx0, my0, mz0,
               mode, sampling_idx):

    """Bloch‑Simulation auf der CPU mit Flow‑Feld."""
    N  = mx_out.shape[0]
    Nt = b1r.shape[0]

    for i in prange(N):
        # Start‑Magnetisierung
        Mx = mx0[i] if (mode & 1) else 0.0
        My = my0[i] if (mode & 1) else 0.0
        Mz = mz0[i] if (mode & 1) else 1.0

        # Ausgangs‑Pos & Flow
        x0, y0, z0 = pos[i, 0], pos[i, 1], pos[i, 2]
        vx, vy, vz = flow[i, 0], flow[i, 1], flow[i, 2]
        dfi = df[i] if df.shape[0] > 1 else df[0]
        T1i = T1[i] if T1.shape[0] > 1 else T1[0]
        T2i = T2[i] if T2.shape[0] > 1 else T2[0]

        store = 0  # Index im Ausgabepuffer

        for step in range(Nt):
            # Aktuelle Pos = Start + v * t_abs[step]
            t_rel = t_abs[step]
            x = x0 + vx*t_rel
            y = y0 + vy*t_rel
            z = z0 + vz*t_rel

            # B‑Feld (RF + Grad + Off‑Res)
            Bx = b1r[step]
            By = b1i[step]
            Gx, Gy, Gz = g[0, step], g[1, step], g[2, step]
            Bz = Gx*x + Gy*y + Gz*z + dfi / GAMMA

            # Precession (Z‑Rot.)
            phi_z = GAMMA * Bz * dt[step]
            c, s = math.cos(phi_z), math.sin(phi_z)
            Mx, My = Mx*c - My*s, Mx*s + My*c

            # RF‑Rot. (XY)
            Bxy = math.sqrt(Bx*Bx + By*By)
            if Bxy > 0.0:
                phi_xy = GAMMA * Bxy * dt[step]
                ux, uy = Bx/Bxy, By/Bxy
                cxy, sxy = math.cos(phi_xy), math.sin(phi_xy)
                dot = Mx*ux + My*uy
                Mx = cxy*Mx + sxy*(uy*Mz) + (1.0-cxy)*dot*ux
                My = cxy*My - sxy*(ux*Mz) + (1.0-cxy)*dot*uy
                Mz = cxy*Mz + sxy*(ux*My - uy*Mx)

            # Relaxation
            E1 = math.exp(-dt[step]/T1i)
            E2 = math.exp(-dt[step]/T2i)
            Mx *= E2; My *= E2
            Mz = 1.0 - (1.0 - Mz)*E1

            # Speichern nur an Sampling‑Indizes
            if (mode & 2) and (step == sampling_idx[store]):
                mx_out[i, store] = Mx
                my_out[i, store] = My
                mz_out[i, store] = Mz
                store += 1

        # Endzustand
        if (mode & 2) == 0:
            mx_out[i, 0] = Mx; my_out[i, 0] = My; mz_out[i, 0] = Mz

# -----------------------------------------------------------------------------
# Öffentliche Wrapper‑Funktion  -----------------------------------------------
# -----------------------------------------------------------------------------
def bloch_simulation(b1, g, dt,
                     T1, T2, df, pos3d,
                     mode, mx0, my0, mz0,
                     sampling_idx=None,
                     flow=None, t_abs=None,
                     use_gpu=True):
    """High‑Level‑Interface für Bloch‑Simulation.

    Alle Arrays werden intern als float32 angelegt; dt, b1, g sind Vektoren
    bzw. Matrizen für **jeden** Zeitschritt.  `sampling_idx` enthält die
    Zeitschritte, an denen Magnetisierung gespeichert wird.
    """
    if sampling_idx is None:
        sampling_idx = np.arange(len(dt), dtype=np.int32)
    sampling_idx = np.asarray(sampling_idx, dtype=np.int32)

    N  = pos3d.shape[1]               # Spin‑Anzahl
    Nt = dt.shape[0]                  # Zeitschritte
    Nout = sampling_idx.shape[0] if (mode & 2) else 1

    # dtype‑Konvertierungen / Skalierung
    b1r = np.real(b1).astype(np.float32)
    b1i = np.imag(b1).astype(np.float32)
    g   = g.astype(np.float32)
    dt  = dt.astype(np.float32)
    if pos3d.ndim == 3:                                    # already (Nt,N,3)
        if pos3d.shape[0] != Nt:
            raise ValueError("pos3d first axis must match Nt")
        pos = pos3d.astype(np.float32)
    else:                                                  # static grid (+flow)
        pos0 = pos3d.T.astype(np.float32)                  # (N,3)
        if flow is not None:                               # flow [m/s] → mm/s
            flow_mmps = flow.astype(np.float32) * 1e3
            # absolute Zeitpunkte (Beginn jedes Δt-Schrittes)
            t_abs = np.concatenate(([0.0], np.cumsum(dt[:-1])))
            pos   = pos0[None, :, :] + flow_mmps[None, :, :] * t_abs[:, None, None]
        else:                                              # reine Wiederholung
            pos   = np.broadcast_to(pos0, (Nt, *pos0.shape)).copy()

    # 1‑D oder Voxel‑spezifische Parameter angleichen
    T1 = np.atleast_1d(T1).astype(np.float32)
    T2 = np.atleast_1d(T2).astype(np.float32)
    df = np.atleast_1d(df).astype(np.float32)

    # Ausgabe‑Puffer
    mx = np.zeros((N, Nout), dtype=np.float32)
    my = np.zeros((N, Nout), dtype=np.float32)
    mz = np.zeros((N, Nout), dtype=np.float32)

    # GPU erst nutzen, wenn Flow **nicht** gesetzt ---------------------------
    if flow is not None:
        use_gpu = False
    if use_gpu and not cuda.is_available():
        use_gpu = False

    # ---------------- Pfad wählen -----------------------------------------
    if use_gpu:
        # Transfer to device
        mx0_d, my0_d, mz0_d = (cuda.to_device(arr.astype(np.float32)) for arr in (mx0, my0, mz0))
        mx_d = cuda.to_device(mx); my_d = cuda.to_device(my); mz_d = cuda.to_device(mz)
        b1r_d = cuda.to_device(b1r); b1i_d = cuda.to_device(b1i)
        g_d   = cuda.to_device(g);    dt_d  = cuda.to_device(dt)
        T1_d  = cuda.to_device(T1);   T2_d  = cuda.to_device(T2); df_d = cuda.to_device(df)
        pos_d = cuda.to_device(pos)

        threads = 128
        blocks  = (N + threads - 1) // threads
        _bloch_kernel[blocks, threads](mx_d, my_d, mz_d,
                                       b1r_d, b1i_d, g_d, dt_d,
                                       T1_d, T2_d, df_d, pos_d,
                                       mx0_d, my0_d, mz0_d,
                                       int(mode))
        cuda.synchronize()
        mx, my, mz = mx_d.copy_to_host(), my_d.copy_to_host(), mz_d.copy_to_host()

    else:
        # CPU / Flow‑Pfad
        flow = np.zeros_like(pos) if flow is None else flow.astype(np.float32)
        if t_abs is None:
            t_abs = np.cumsum(dt) - dt  # t[0]=0
        t_abs = t_abs.astype(np.float32)

        _bloch_cpu(mx, my, mz,
                    b1r, b1i, g, dt,
                    T1, T2, df, pos,
                    flow, t_abs,
                    mx0.astype(np.float32),
                    my0.astype(np.float32),
                    mz0.astype(np.float32),
                    int(mode), sampling_idx.astype(np.int32))

    return mx, my, mz, pos[sampling_idx]
