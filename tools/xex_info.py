"""Print the XEX2 header of an Xbox 360 executable: format, execution info, PE name,
XDK static libraries and import libraries.  Reads the header only; the image is untouched.

    python -I tools/xex_info.py <default.xex>
"""

import hashlib
import struct
import sys
from pathlib import Path

HEADER_NAMES = {
    0x000002FF: "resource info",
    0x000003FF: "file format info",
    0x00000405: "base reference",
    0x000080FF: "bounding path",
    0x00010001: "original base address",
    0x00010100: "entry point",
    0x00010201: "image base address",
    0x000103FF: "import libraries",
    0x00018002: "checksum/timestamp",
    0x000183FF: "original PE name",
    0x000200FF: "static libraries",
    0x00020104: "TLS info",
    0x00020200: "default stack size",
    0x00020301: "default filesystem cache size",
    0x00020401: "default heap size",
    0x00028002: "page heap size and flags",
    0x00030000: "system flags",
    0x00040006: "execution info",
    0x00040201: "title workspace size",
    0x00040310: "game ratings",
    0x00040404: "LAN key",
    0x000405FF: "Xbox 360 logo",
    0x000406FF: "multidisc media IDs",
    0x000407FF: "alternate title IDs",
    0x00040801: "additional title memory",
    0x00E10402: "exports by name",
}

ENCRYPTION = {0: "none", 1: "normal (AES)"}
COMPRESSION = {0: "none", 1: "basic (zero-fill blocks)", 2: "normal (LZX)", 3: "delta"}


def u16(data, off):
    return struct.unpack_from(">H", data, off)[0]


def u32(data, off):
    return struct.unpack_from(">I", data, off)[0]


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    path = Path(sys.argv[1])
    data = path.read_bytes()
    if data[:4] != b"XEX2":
        sys.exit(f"not an XEX2 file (magic {data[:4]!r})")

    print(f"file: {path.name}  size: {len(data):,}  sha1: {hashlib.sha1(data).hexdigest()}")
    module_flags, pe_offset, _, security_offset, count = struct.unpack_from(">5I", data, 4)
    print(f"module flags: 0x{module_flags:08X}  PE data offset: 0x{pe_offset:X}  security info: 0x{security_offset:X}")

    headers = {}
    for i in range(count):
        key, value = struct.unpack_from(">II", data, 0x18 + i * 8)
        headers[key] = value
        print(f"  header 0x{key:08X}  {HEADER_NAMES.get(key, '?'):30s} value 0x{value:08X}")

    if 0x000003FF in headers:
        off = headers[0x000003FF]
        print(f"encryption: {ENCRYPTION.get(u16(data, off + 4), '?')}  compression: {COMPRESSION.get(u16(data, off + 6), '?')}")

    if 0x00040006 in headers:
        off = headers[0x00040006]
        media_id, version, base_version, title_id = struct.unpack_from(">4I", data, off)
        platform, table, disc, discs = struct.unpack_from(">4B", data, off + 16)
        def ver(v):
            return f"{v >> 28}.{(v >> 24) & 0xF}.{(v >> 8) & 0xFFFF}.{v & 0xFF}"
        print(f"title id: {title_id:08X}  media id: {media_id:08X}  version: {ver(version)}  base: {ver(base_version)}  disc {disc}/{discs}")

    load_address = u32(data, security_offset + 0x110)
    image_size = u32(data, security_offset + 0x4)
    print(f"load address: 0x{load_address:08X}  image size: 0x{image_size:X}")
    if 0x00010100 in headers:
        print(f"entry point: 0x{headers[0x00010100]:08X}")

    if 0x000183FF in headers:
        off = headers[0x000183FF]
        size = u32(data, off)
        print(f"original PE name: {data[off + 4:off + size].split(b'\\0')[0].decode('ascii', 'replace')}")

    if 0x000200FF in headers:
        off = headers[0x000200FF]
        size = u32(data, off)
        print("static libraries (XDK):")
        for entry in range(off + 4, off + size, 16):
            name = data[entry:entry + 8].split(b"\0")[0].decode("ascii", "replace")
            major, minor, build, qfe = struct.unpack_from(">4H", data, entry + 8)
            print(f"  {name:8s} {major}.{minor}.{build}.{qfe & 0xFF}")

    if 0x000103FF in headers:
        off = headers[0x000103FF]
        string_size, lib_count = u32(data, off + 4), u32(data, off + 8)
        names = data[off + 12:off + 12 + string_size].split(b"\0")
        print(f"import libraries ({lib_count}): " + ", ".join(n.decode("ascii", "replace") for n in names if n))


if __name__ == "__main__":
    main()
