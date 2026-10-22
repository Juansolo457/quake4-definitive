"""Disassemble one function of a decrypted Xbox 360 image (xexdump output) with
constants resolved: lis/addi pairs that point at strings, lfs/lfd loads of float
constants, and bl targets (named from the import symbols when known).

Function bounds come from .pdata; leaf functions without an entry are cut at the
first blr.

    python -P tools/ppc_func.py game/xex/default 0x821CE804 [more addresses...]
"""

import bisect
import struct
import sys

import capstone

BASE = 0x82000000


class Image:
    def __init__(self, prefix):
        self.data = open(prefix + ".bin", "rb").read()
        self.sections = {}
        for line in open(prefix + ".sections.txt"):
            name, base, size = line.split()[:3]
            self.sections[name] = (int(base, 16), int(size, 16))
        self.symbols = {}
        for line in open(prefix + ".symbols.txt"):
            address, _, name = line.split(maxsplit=2)
            self.symbols[int(address, 16)] = name.strip()
        pb, ps = self.sections[".pdata"]
        funcs = []
        for k in range(ps // 8):
            begin, info = struct.unpack_from(">II", self.data, pb - BASE + k * 8)
            if begin:
                funcs.append((begin, ((info >> 8) & 0x3FFFFF) * 4))
        funcs.sort()
        self.funcs = funcs
        self.starts = [f[0] for f in funcs]

    def u32(self, address):
        return struct.unpack_from(">I", self.data, address - BASE)[0]

    def string(self, address):
        off = address - BASE
        if not 0 <= off < len(self.data):
            return None
        end = self.data.find(b"\0", off, off + 200)
        raw = self.data[off:end] if end > off else b""
        if len(raw) >= 2 and all(0x20 <= b < 0x7F for b in raw):
            return raw.decode()
        return None

    def function_at(self, address):
        i = bisect.bisect_right(self.starts, address) - 1
        if i >= 0 and address < self.funcs[i][0] + self.funcs[i][1]:
            return self.funcs[i]
        return None


def disassemble(image, address):
    func = image.function_at(address)
    if func:
        start, size = func
    else:
        start, size = address, 0x400
    md = capstone.Cs(capstone.CS_ARCH_PPC, capstone.CS_MODE_32 | capstone.CS_MODE_BIG_ENDIAN)
    val = {}  # GPR -> known constant (from lis, then addi)
    print(f"===== function 0x{start:08X} size 0x{size:X}" + ("" if func else " (no .pdata entry; stops at blr)"))
    for offset in range(0, size, 4):
        pc = start + offset
        word = image.u32(pc)
        ins = next(md.disasm(struct.pack(">I", word), pc), None)
        text = f"{ins.mnemonic:8s} {ins.op_str}" if ins else f".long 0x{word:08X}"
        note = ""
        op, rd, ra = word >> 26, (word >> 21) & 31, (word >> 16) & 31
        simm = word & 0xFFFF
        simm = simm - 0x10000 if simm & 0x8000 else simm
        base = val.get(ra) if ra else None
        if op == 15 and ra == 0:
            val[rd] = (word & 0xFFFF) << 16
        elif op == 14 and base is not None:
            target = (base + simm) & 0xFFFFFFFF
            val[rd] = target
            s = image.string(target)
            note = f'"{s}"' if s else f"&0x{target:08X}"
        elif op in (48, 50) and base is not None and 0 <= ((base + simm) & 0xFFFFFFFF) - BASE < len(image.data) - 8:   # lfs / lfd
            target = (base + simm) & 0xFFFFFFFF
            if op == 48:
                note = f"= {struct.unpack_from('>f', image.data, target - BASE)[0]:g}f  @0x{target:08X}"
            else:
                note = f"= {struct.unpack_from('>d', image.data, target - BASE)[0]:g}  @0x{target:08X}"
        elif op in (32, 34, 40, 42, 36, 38, 44, 52, 54) and base is not None:   # integer/FP access at a constant address
            note = f"[0x{(base + simm) & 0xFFFFFFFF:08X}]"
        if op in (7, 8, 12, 13, 32, 33, 34, 35, 40, 41, 42, 43, 46) or (op == 14 and base is None and ra):
            val.pop(rd, None)                             # rD overwritten by a non-constant
        elif op == 14 and ra == 0:
            val[rd] = simm & 0xFFFFFFFF
        elif op in (20, 21, 23, 24, 25, 26, 27, 28, 29, 30, 31):
            val.pop(ra if op != 31 else rd, None)
            if op == 31:
                val.pop(ra, None)
        if op == 18:
            li = word & 0x03FFFFFC
            li = li - 0x04000000 if li & 0x02000000 else li
            target = (pc + li) & 0xFFFFFFFF
            note = image.symbols.get(target, "")
        print(f"{pc:08X}  {text:40s} {note}")
        if not func and word == 0x4E800020:
            break


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    image = Image(sys.argv[1])
    for arg in sys.argv[2:]:
        disassemble(image, int(arg, 16))


if __name__ == "__main__":
    main()
