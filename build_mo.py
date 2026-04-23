"""
Build .mo files from existing .po files without requiring GNU gettext.
Usage: python build_mo.py
"""
import struct
import re
import os


def parse_po(path):
    """Parse a .po file and return dict of msgid -> msgstr."""
    translations = {}
    current_msgid = None
    current_msgstr = None
    in_msgid = False
    in_msgstr = False

    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n').rstrip('\r')
            
            # Skip comment lines
            if line.startswith('#'):
                continue
            
            if line.startswith('msgid '):
                if current_msgid is not None and current_msgstr is not None:
                    translations[current_msgid] = current_msgstr
                raw = line[6:].strip()
                if raw.startswith('"') and raw.endswith('"'):
                    current_msgid = raw[1:-1]
                else:
                    current_msgid = raw
                current_msgstr = None
                in_msgid = True
                in_msgstr = False
                
            elif line.startswith('msgstr '):
                raw = line[7:].strip()
                if raw.startswith('"') and raw.endswith('"'):
                    current_msgstr = raw[1:-1]
                else:
                    current_msgstr = raw
                in_msgid = False
                in_msgstr = True
                
            elif line.startswith('"') and line.endswith('"'):
                # Continuation line
                content = line[1:-1]
                if in_msgid and current_msgid is not None:
                    current_msgid += content
                elif in_msgstr and current_msgstr is not None:
                    current_msgstr += content
                    
            elif line.strip() == '':
                # Empty line = end of an entry
                if current_msgid is not None and current_msgstr is not None:
                    translations[current_msgid] = current_msgstr
                current_msgid = None
                current_msgstr = None
                in_msgid = False
                in_msgstr = False

    # Don't forget the last entry
    if current_msgid is not None and current_msgstr is not None:
        translations[current_msgid] = current_msgstr

    return translations


def make_mo_content(translations):
    """Create .mo binary content from a dict of original->translation."""
    # Remove empty key if present (we'll add our own header)
    clean = {k: v for k, v in translations.items() if k != ''}
    
    sorted_items = sorted(clean.items())
    keys = [k for k, v in sorted_items]
    values = [v for k, v in sorted_items]

    # Insert MIME header at the empty key
    keys.insert(0, "")
    values.insert(0, "Project-Id-Version: 1.0\nContent-Type: text/plain; charset=UTF-8\nContent-Transfer-Encoding: 8bit\n")

    n = len(keys)
    header_size = 28
    key_table_offset = header_size
    val_table_offset = header_size + 8 * n
    strings_offset = header_size + 16 * n

    kdata = b""
    k_offsets = []
    for k in keys:
        enc = k.encode("utf-8")
        k_offsets.append((len(enc), strings_offset + len(kdata)))
        kdata += enc + b"\0"

    vdata = b""
    v_offsets = []
    v_start = strings_offset + len(kdata)
    for v in values:
        enc = v.encode("utf-8")
        v_offsets.append((len(enc), v_start + len(vdata)))
        vdata += enc + b"\0"

    result = struct.pack(
        "<IIIIIII",
        0x950412de, 0, n,
        key_table_offset,
        val_table_offset,
        0, 0
    )

    for length, pos in k_offsets:
        result += struct.pack("<II", length, pos)

    for length, pos in v_offsets:
        result += struct.pack("<II", length, pos)

    result += kdata
    result += vdata
    return result


def build_mo_from_po(po_path, mo_path):
    print(f"  Reading: {po_path}")
    translations = parse_po(po_path)
    # Filter out empty msgstr entries
    valid = {k: v for k, v in translations.items() if v.strip()}
    content = make_mo_content(valid)
    with open(mo_path, 'wb') as f:
        f.write(content)
    print(f"  Written: {mo_path}  ({len(valid)} strings)")


# Build both language .mo files
build_mo_from_po(
    "locale/ar/LC_MESSAGES/django.po",
    "locale/ar/LC_MESSAGES/django.mo"
)

build_mo_from_po(
    "locale/en/LC_MESSAGES/django.po",
    "locale/en/LC_MESSAGES/django.mo"
)

print("\nDone! .mo files built from .po files.")
