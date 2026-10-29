#!/usr/bin/env python3
"""Package a look pack directory into a zip archive.

    main.py <pack_folder> <output.zip>

The pack is validated first (pack.json must list looks that exist and pass
the preset schema), and archive paths are rooted at the pack folder
(e.g. starter_pack/pack.json, starter_pack/looks/...) rather than carrying the
full source path. Dotfiles (.DS_Store, editor temp files) are skipped.
"""
import os
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
VALIDATOR = os.path.join(HERE, "..", "preset_validator", "validate.py")


def main(argv):
    if len(argv) != 2:
        print("Usage: preset_packager <pack_folder> <output.zip>", file=sys.stderr)
        return 1
    input_folder, output_file = argv
    pack_json = os.path.join(input_folder, "pack.json")
    if not os.path.isfile(pack_json):
        print(f"preset_packager: {pack_json} not found", file=sys.stderr)
        return 1

    # Refuse to ship a pack that references missing or invalid looks.
    if subprocess.call([sys.executable, VALIDATOR, input_folder]) != 0:
        print("preset_packager: pack failed validation; not packaging", file=sys.stderr)
        return 1

    out_abs = os.path.abspath(output_file)
    parent = os.path.dirname(os.path.abspath(input_folder).rstrip(os.sep))
    with zipfile.ZipFile(output_file, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(input_folder):
            dirs.sort()
            for name in sorted(files):
                path = os.path.join(root, name)
                if os.path.abspath(path) == out_abs or name.startswith("."):
                    continue
                z.write(path, arcname=os.path.relpath(os.path.abspath(path), parent))

    print("Packaged:", output_file)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
