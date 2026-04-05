"""Educational AES-128 encrypt-only tracer (not side-channel safe)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

# Standard AES S-box
SBOX = bytes(
    int(x, 16)
    for x in """63 7c 77 7b f2 6b 6f c5 30 01 67 2b fe d7 ab 76
    ca 82 c9 7d fa 59 47 f0 ad d4 a2 af 9c a4 72 c0
    b7 fd 93 26 36 3f f7 cc 34 a5 e5 f1 71 d8 31 15
    04 c7 23 c3 18 96 05 9a 07 12 80 e2 eb 27 b2 75
    09 83 2c 1a 1b 6e 5a a0 52 3b d6 b3 29 e3 2f 84
    53 d1 00 ed 20 fc b1 5b 6a cb be 39 4a 4c 58 cf
    d0 ef aa fb 43 4d 33 85 45 f9 02 7f 50 3c 9f a8
    51 a3 40 8f 92 9d 38 f5 bc b6 da 21 10 ff f3 d2
    cd 0c 13 ec 5f 97 44 17 c4 a7 7e 3d 64 5d 19 73
    60 81 4f dc 22 2a 90 88 46 ee b8 14 de 5e 0b db
    e0 32 3a 0a 49 06 24 5c c2 d3 ac 62 91 95 e4 79
    e7 c8 37 6d 8d d5 4e a9 6c 56 f4 ea 65 7a ae 08
    ba 78 25 2e 1c a6 b4 c6 e8 dd 74 1f 4b bd 8b 8a
    70 3e b5 66 48 03 f6 0e 61 35 57 b9 86 c1 1d 9e
    e1 f8 98 11 69 d9 8e 94 9b 1e 87 e9 ce 55 28 df
    8c a1 89 0d bf e6 42 68 41 99 2d 0f b0 54 bb 16""".split()
)


def xtime(a: int) -> int:
    return (((a << 1) ^ 0x1B) & 0xFF) if (a & 0x80) else ((a << 1) & 0xFF)


def mix_single_column(col: list[int], matrix: list[list[int]] | None = None) -> list[int]:
    """Mix one 4-byte column. Default = AES MixColumns matrix."""
    if matrix is None:
        matrix = [[2, 3, 1, 1], [1, 2, 3, 1], [1, 1, 2, 3], [3, 1, 1, 2]]
    out = [0, 0, 0, 0]
    for i in range(4):
        v = 0
        for j in range(4):
            c = matrix[i][j]
            t = col[j]
            if c == 1:
                v ^= t
            elif c == 2:
                v ^= xtime(t)
            elif c == 3:
                v ^= xtime(t) ^ t
            else:
                acc = 0
                bb = t
                for k in range(8):
                    if c & 1:
                        acc ^= bb
                    bb = xtime(bb)
                    c >>= 1
                v ^= acc & 0xFF
        out[i] = v & 0xFF
    return out


def key_expansion(key: bytes) -> list[bytes]:
    assert len(key) == 16
    nk, nb, nr = 4, 4, 10
    w: list[int] = list(key)
    rcon = [0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1B, 0x36]

    def rot_word(x: list[int]) -> list[int]:
        return x[1:] + x[:1]

    def sub_word(x: list[int]) -> list[int]:
        return [SBOX[b] for b in x]

    for i in range(nk, nb * (nr + 1)):
        t = w[(i - 1) * 4 : i * 4]
        if i % nk == 0:
            t = sub_word(rot_word(t))
            t[0] ^= rcon[i // nk - 1]
        elif nk > 6 and i % nk == 4:
            t = sub_word(t)
        for j in range(4):
            w.append(w[(i - nk) * 4 + j] ^ t[j])
    rk: list[bytes] = []
    for r in range(nr + 1):
        rk.append(bytes(w[r * 16 : r * 16 + 16]))
    return rk


@dataclass
class TraceOpts:
    disable_shift_rows: bool = False
    mix_matrix: list[list[int]] | None = None  # 4x4 coeffs for MixColumns


def _state_from_bytes(block: bytes) -> list[list[int]]:
    # column-major 4x4
    s = [[0] * 4 for _ in range(4)]
    for c in range(4):
        for r in range(4):
            s[c][r] = block[c * 4 + r]
    return s


def _bytes_from_state(s: list[list[int]]) -> bytes:
    out = bytearray(16)
    for c in range(4):
        for r in range(4):
            out[c * 4 + r] = s[c][r]
    return bytes(out)


def _sub_bytes(s: list[list[int]]) -> None:
    for c in range(4):
        for r in range(4):
            s[c][r] = SBOX[s[c][r]]


def _shift_rows(s: list[list[int]]) -> None:
    # s[col][row] column-major; ShiftRows rotates row r by r positions left across columns
    for r in range(1, 4):
        col_vals = [s[c][r] for c in range(4)]
        for c in range(4):
            s[c][r] = col_vals[(c + r) % 4]


def _mix_columns(s: list[list[int]], matrix: list[list[int]] | None) -> None:
    for c in range(4):
        col = [s[c][r] for r in range(4)]
        nc = mix_single_column(col, matrix)
        for r in range(4):
            s[c][r] = nc[r]


def _add_round_key(s: list[list[int]], rk: bytes) -> None:
    for c in range(4):
        for r in range(4):
            s[c][r] ^= rk[c * 4 + r]


def encrypt_trace(
    plaintext: bytes,
    key: bytes,
    opts: TraceOpts | None = None,
    log: Callable[[str, int, bytes], None] | None = None,
) -> bytes:
    """Encrypt 16-byte block; optional log(label, round, state_bytes)."""
    if opts is None:
        opts = TraceOpts()
    rk = key_expansion(key)
    s = _state_from_bytes(plaintext)

    def emit(label: str, rnd: int) -> None:
        if log:
            log(label, rnd, _bytes_from_state(s))

    _add_round_key(s, rk[0])
    emit("r0_add_round_key", 0)

    for rnd in range(1, 10):
        _sub_bytes(s)
        emit(f"r{rnd}_sub_bytes", rnd)
        if opts.disable_shift_rows:
            pass
        else:
            _shift_rows(s)
        emit(f"r{rnd}_shift_rows", rnd)
        _mix_columns(s, opts.mix_matrix)
        emit(f"r{rnd}_mix_columns", rnd)
        _add_round_key(s, rk[rnd])
        emit(f"r{rnd}_add_round_key", rnd)

    _sub_bytes(s)
    emit("r10_sub_bytes", 10)
    if not opts.disable_shift_rows:
        _shift_rows(s)
    emit("r10_shift_rows", 10)
    _add_round_key(s, rk[10])
    emit("r10_add_round_key", 10)

    return _bytes_from_state(s)


def hamming_bits(a: bytes, b: bytes) -> int:
    x = int.from_bytes(a, "big") ^ int.from_bytes(b, "big")
    return x.bit_count()


def hamming_bytes(a: bytes, b: bytes) -> int:
    return sum(1 for i in range(16) if a[i] != b[i])


def collect_hamming_curve(
    p0: bytes,
    p1: bytes,
    k0: bytes,
    k1: bytes,
    opts: TraceOpts | None = None,
) -> tuple[list[str], list[int]]:
    """Return (step_labels, bit_distances) comparing traces p0,k0 vs p1,k1."""
    seq_a: list[bytes] = []
    seq_b: list[bytes] = []

    def make_logger(bucket: list[bytes]):
        def _log(_lbl: str, _rnd: int, st: bytes) -> None:
            bucket.append(st)

        return _log

    encrypt_trace(p0, k0, opts, log=make_logger(seq_a))
    encrypt_trace(p1, k1, opts, log=make_logger(seq_b))
    labels: list[str] = []
    bits: list[int] = []
    for i, (sa, sb) in enumerate(zip(seq_a, seq_b, strict=True)):
        labels.append(f"s{i}")
        bits.append(hamming_bits(sa, sb))
    return labels, bits


# M_new: invertible circulant-style alternative (assignment matrix not in sidecar; documented in JSON)
M_NEW = [[3, 2, 1, 1], [1, 3, 2, 1], [1, 1, 3, 2], [2, 1, 1, 3]]
