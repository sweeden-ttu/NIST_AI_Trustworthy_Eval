#!/usr/bin/env python3
"""Generate output/results and output/diagrams per test_cases/rd_agent workflow YAMLs."""

from __future__ import annotations

import json
import os
import struct
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from toy_aes128_trace import (  # noqa: E402
    M_NEW,
    TraceOpts,
    collect_hamming_curve,
    hamming_bits,
    hamming_bytes,
)

OUT_RESULTS = ROOT / "output" / "results"
OUT_DIAG = ROOT / "output" / "diagrams"
ASSETS = ROOT / "assets"


def _ensure_dirs() -> None:
    OUT_RESULTS.mkdir(parents=True, exist_ok=True)
    OUT_DIAG.mkdir(parents=True, exist_ok=True)
    (OUT_RESULTS / "q2").mkdir(parents=True, exist_ok=True)
    (OUT_DIAG / "q3-wireshark").mkdir(parents=True, exist_ok=True)


def _plot_curve(
    labels: list[str],
    bits: list[int],
    title: str,
    outfile: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(range(len(bits)), bits, marker=".", lw=1)
    ax.set_xlabel("step index")
    ax.set_ylabel("Hamming distance (bits)")
    ax.set_title(title)
    step = max(1, len(labels) // 20)
    ax.set_xticks(range(0, len(labels), step))
    ax.set_xticklabels([labels[i] for i in range(0, len(labels), step)], rotation=60, ha="right", fontsize=7)
    fig.tight_layout()
    fig.savefig(outfile, format="pdf")
    plt.close(fig)


def run_q1() -> None:
    P0 = bytes(16)
    P1 = bytearray(16)
    P1[0] = 0x01  # one-bit flip from all-zero plaintext
    P1 = bytes(P1)
    K0 = bytes(16)
    K1 = bytearray(16)
    K1[0] = 0x01
    K1 = bytes(K1)

    scenarios = {
        "part_a_standard": (P0, P1, K0, K0, TraceOpts()),
        "part_b_no_shiftrows": (P0, P1, K0, K0, TraceOpts(disable_shift_rows=True)),
        "part_c_custom_mix": (P0, P1, K0, K0, TraceOpts(mix_matrix=M_NEW)),
    }

    summary: dict = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "note": "Toy AES-128 tracer for coursework; not production crypto.",
        "mix_matrix_M_new": M_NEW,
        "plaintext_pair": {"P_hex": P0.hex(), "P_prime_hex": P1.hex()},
        "hamming_scenarios": {},
        "part_d_key_flip": {},
    }

    plot_map = {
        "part_a_standard": OUT_DIAG / "q1-hamming-rounds.pdf",
        "part_b_no_shiftrows": OUT_DIAG / "q1-ablation-shiftrows.pdf",
        "part_c_custom_mix": OUT_DIAG / "q1-ablation-mixcolumns.pdf",
    }

    for name, (p0, p1, k0, k1, opts) in scenarios.items():
        labels, bits = collect_hamming_curve(p0, p1, k0, k1, opts)
        summary["hamming_scenarios"][name] = {
            "steps": labels,
            "bit_distances": bits,
            "max_bits": max(bits) if bits else 0,
            "final_ciphertext_bit_hamming": bits[-1] if bits else 0,
        }
        title = name.replace("_", " ")
        _plot_curve(labels, bits, f"Q1 {title} (P vs P', key fixed)", plot_map[name])

    # Part D: key flip, plaintext P0 fixed — compare K0 vs K1 for each ablation
    ablations = {
        "d_standard": TraceOpts(),
        "d_no_shiftrows": TraceOpts(disable_shift_rows=True),
        "d_custom_mix": TraceOpts(mix_matrix=M_NEW),
    }
    for aname, opts in ablations.items():
        labels, bits = collect_hamming_curve(P0, P0, K0, K1, opts)
        summary["part_d_key_flip"][aname] = {
            "steps": labels,
            "bit_distances": bits,
            "final_ciphertext_bit_hamming": bits[-1] if bits else 0,
        }

    ct_a = summary["hamming_scenarios"]["part_a_standard"]["final_ciphertext_bit_hamming"]
    openssl_ver = subprocess.run(
        ["openssl", "version", "-a"],
        capture_output=True,
        text=True,
        check=False,
    ).stdout
    summary["environment"] = {"openssl_version_a": openssl_ver.splitlines()[:5]}

    (OUT_RESULTS / "q1-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("Q1 wrote q1-summary.json and q1-*.pdf")


def write_minimal_bmp(path: Path, width: int, height: int) -> None:
    """24-bit BMP, gradient fill; row stride multiple of 4."""
    row_stride = ((width * 3 + 3) // 4) * 4
    pixel_size = row_stride * height
    file_size = 54 + pixel_size
    header = bytearray(54)
    # BITMAPFILEHEADER (14) + BITMAPINFOHEADER (40)
    struct.pack_into("<2sIHHI", header, 0, b"BM", file_size, 0, 0, 54)
    struct.pack_into(
        "<IiiHHIIiiII",
        header,
        14,
        40,
        width,
        height,
        1,
        24,
        0,
        pixel_size,
        0,
        0,
        0,
        0,
    )
    pixels = bytearray(pixel_size)
    for y in range(height):
        row_off = y * row_stride
        for x in range(width):
            i = row_off + x * 3
            pixels[i] = (x * 7 + y * 3) % 256
            pixels[i + 1] = (x * 11 + y * 5) % 256
            pixels[i + 2] = (x * 13 + y * 17) % 256
    path.write_bytes(bytes(header) + pixels)


def run_q2() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    bmp = ASSETS / "Secret.bmp"
    if not bmp.exists():
        write_minimal_bmp(bmp, 120, 90)

    key = os.urandom(16)
    iv = os.urandom(16)
    q2dir = OUT_RESULTS / "q2"
    raw_ecb = q2dir / "secret.ecb.bin"
    raw_cbc = q2dir / "secret.cbc.bin"
    hex_key = key.hex()
    hex_iv = iv.hex()

    subprocess.run(
        [
            "openssl",
            "enc",
            "-aes-128-ecb",
            "-nosalt",
            "-K",
            hex_key,
            "-in",
            str(bmp),
            "-out",
            str(raw_ecb),
        ],
        check=True,
    )
    subprocess.run(
        [
            "openssl",
            "enc",
            "-aes-128-cbc",
            "-nosalt",
            "-K",
            hex_key,
            "-iv",
            hex_iv,
            "-in",
            str(bmp),
            "-out",
            str(raw_cbc),
        ],
        check=True,
    )

    plain = bmp.read_bytes()
    hdr = plain[:54]
    ecb_full = raw_ecb.read_bytes()
    cbc_full = raw_cbc.read_bytes()
    ecb_body = ecb_full[54:]
    cbc_body = cbc_full[54:]

    def ciphertext_preview_pdf(cipher_body: bytes, title: str, out_pdf: Path) -> None:
        arr = np.frombuffer(cipher_body, dtype=np.uint8)
        side = int(np.ceil(np.sqrt(len(arr))))
        pad = side * side - len(arr)
        if pad > 0:
            arr = np.pad(arr, (0, pad), mode="constant")
        grid = arr.reshape(side, side)
        fig, ax = plt.subplots(figsize=(5, 5))
        ax.imshow(grid, cmap="gray", vmin=0, vmax=255)
        ax.set_title(title)
        ax.axis("off")
        fig.tight_layout()
        fig.savefig(out_pdf, format="pdf")
        plt.close(fig)

    ciphertext_preview_pdf(ecb_body, "ECB ciphertext bytes (pixel body)", OUT_DIAG / "q2-ecb-noise.pdf")
    ciphertext_preview_pdf(cbc_body, "CBC ciphertext bytes (pixel body)", OUT_DIAG / "q2-cbc-noise.pdf")

    fixed_ecb = q2dir / "secret.ecb.header-fixed.bmp"
    fixed_cbc = q2dir / "secret.cbc.header-fixed.bmp"
    fixed_ecb.write_bytes(hdr + ecb_body)
    fixed_cbc.write_bytes(hdr + cbc_body)

    def try_preview_bmp(p: Path, title: str, out_pdf: Path) -> None:
        from PIL import Image
        from PIL import UnidentifiedImageError

        try:
            im = Image.open(p)
            fig, ax = plt.subplots(figsize=(5, 5))
            ax.imshow(im)
            ax.set_title(title)
            ax.axis("off")
            fig.tight_layout()
            fig.savefig(out_pdf, format="pdf")
            plt.close(fig)
        except (UnidentifiedImageError, OSError):
            body = p.read_bytes()[54:]
            ciphertext_preview_pdf(body, f"{title} (raw body)", out_pdf)

    try_preview_bmp(fixed_ecb, "ECB + plaintext BMP header (visual)", OUT_DIAG / "q2-header-fixed-ecb.pdf")
    try_preview_bmp(fixed_cbc, "CBC + plaintext BMP header (visual)", OUT_DIAG / "q2-header-fixed-cbc.pdf")

    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "openssl_commands": [
            "openssl enc -aes-128-ecb -nosalt -K <hex> -in Secret.bmp -out secret.ecb.bin",
            "openssl enc -aes-128-cbc -nosalt -K <hex> -iv <hex> -in Secret.bmp -out secret.cbc.bin",
        ],
        "key_hex": hex_key,
        "iv_hex": hex_iv,
        "note": "Key/IV shown for reproducibility on this workstation; do not commit if policy forbids.",
        "artifacts": {
            "ecb_ciphertext": str(raw_ecb.relative_to(ROOT)),
            "cbc_ciphertext": str(raw_cbc.relative_to(ROOT)),
            "header_fixed_ecb": str(fixed_ecb.relative_to(ROOT)),
            "header_fixed_cbc": str(fixed_cbc.relative_to(ROOT)),
        },
    }
    (q2dir / "openssl_run.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print("Q2 wrote output/results/q2/* and q2-*.pdf")


def run_q3() -> None:
    hosts = [
        "google.com",
        "github.com",
        "cloudflare.com",
        "apple.com",
        "microsoft.com",
        "mozilla.org",
        "wikipedia.org",
        "eff.org",
        "amazon.com",
    ]
    rows: list[dict] = []
    for host in hosts:
        cmd = [
            "openssl",
            "s_client",
            "-connect",
            f"{host}:443",
            "-servername",
            host,
        ]
        proc = subprocess.run(
            cmd,
            input="",
            capture_output=True,
            text=True,
            timeout=15,
        )
        txt = proc.stdout + proc.stderr
        cipher = None
        protocol = None
        for line in txt.splitlines():
            low = line.lower()
            if "cipher" in low and ("new" in low or "session" in low or ":" in line):
                if ":" in line:
                    cipher = line.split(":", 1)[-1].strip()
            if "protocol" in low and ":" in line:
                protocol = line.split(":", 1)[-1].strip()
        rows.append(
            {
                "host": host,
                "protocol": protocol,
                "negotiated_cipher": cipher,
                "openssl_exit": proc.returncode,
            }
        )

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "method": "openssl s_client (live TLS); supplement with Wireshark ClientHello captures for coursework",
        "hosts": rows,
    }
    (OUT_RESULTS / "q3-cipher-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    # Table figure (client offers not available from openssl; title clarifies negotiation snapshot)
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.axis("off")
    cells = [["Host", "Protocol", "Negotiated cipher"]]
    for r in rows:
        cells.append(
            [
                r["host"],
                r["protocol"] or "—",
                (r["negotiated_cipher"] or "—")[:60],
            ]
        )
    table = ax.table(cellText=cells, loc="center", cellLoc="left")
    table.scale(1, 1.4)
    ax.set_title("TLS negotiation snapshot (openssl s_client) — replace with Wireshark ClientHello tables for coursework")
    fig.tight_layout()
    fig.savefig(OUT_DIAG / "q3-client-hello-table.pdf", format="pdf")
    plt.close(fig)

    # Simple bar: count ciphers
    from collections import Counter

    ciphers = [r["negotiated_cipher"] or "unknown" for r in rows]
    ctr = Counter(ciphers)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(range(len(ctr)), list(ctr.values()))
    ax.set_xticks(range(len(ctr)))
    ax.set_xticklabels(list(ctr.keys()), rotation=35, ha="right", fontsize=7)
    ax.set_ylabel("Count (hosts)")
    ax.set_title("Server-selected cipher frequency in sample")
    fig.tight_layout()
    fig.savefig(OUT_DIAG / "q3-server-hello-summary.pdf", format="pdf")
    plt.close(fig)

    note = OUT_DIAG / "q3-wireshark" / "README.txt"
    note.write_text(
        "Place Wireshark screenshots and PCAP exports for the 2-browser × 9-site assignment here.\n"
        "Figures q3-*.pdf in parent folder are openssl-derived summaries for the LaTeX draft.\n",
        encoding="utf-8",
    )
    print("Q3 wrote q3-cipher-summary.json and q3-*.pdf")


def verify_aes_against_pycryptodome() -> None:
    from Crypto.Cipher import AES

    key = bytes(range(16))
    pt = bytes(16)
    ref = AES.new(key, AES.MODE_ECB).encrypt(pt)
    from toy_aes128_trace import encrypt_trace

    got = encrypt_trace(pt, key, TraceOpts(), log=None)
    assert got == ref, "Toy AES must match PyCryptodome ECB for standard opts"


def main() -> None:
    _ensure_dirs()
    verify_aes_against_pycryptodome()
    run_q1()
    run_q2()
    run_q3()
    print("Done. Outputs under output/results and output/diagrams")


if __name__ == "__main__":
    main()
