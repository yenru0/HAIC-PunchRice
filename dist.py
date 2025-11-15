#! /usr/bin/env python
import zipfile
import glob
import datetime
import os.path
import sys


def _process_file(
    file_path: str, module_to_skip: str | None
) -> tuple[list[str], list[str]] | tuple[None, None]:
    imports = []
    code_body = []

    if not os.path.exists(file_path):
        return None, None

    print(f"Processing: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped_line = line.strip()
            if stripped_line.startswith("import ") or stripped_line.startswith("from "):
                if module_to_skip is None:
                    imports.append(line.strip())
                elif module_to_skip not in stripped_line:
                    imports.append(line.rstrip())
            else:
                code_body.append(line.rstrip())

    return imports, code_body


def make_main(
    model_name: str,
) -> None:
    base_model_path = "./models/DotsBoxModel.py"
    model_path = f"./models/{model_name}.py"

    base_imports, base_codes = _process_file(base_model_path, None)
    if base_imports is None or base_codes is None:
        raise Exception("Error processing base model file.")

    sp_imports, sp_codes = _process_file(model_path, "DotsBoxModel")

    if sp_imports is None or sp_codes is None:
        raise Exception("Error processing target model file.")

    combined_imports = set(base_imports)
    combined_imports.update(sp_imports)

    with open("./main.py", "w", encoding="utf-8") as f:
        for imp in sorted(combined_imports):
            f.write(imp + "\n")
        f.write("\n\n")

        for code in base_codes:
            f.write(code + "\n")
        f.write("\n\n")
        for code in sp_codes:
            f.write(code + "\n")

        f.write(
            f"""
mdl = {model_name}()

model = mdl.model

def init():
    global mdl
    mdl.init()

def run(board_lines, xsize, ysize):
    global mdl
    return mdl.run(board_lines, xsize, ysize)
                """
        )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python dist.py <ModelName>")
        sys.exit(1)
    make_main(sys.argv[1])
    if not os.path.isdir("dist"):
        os.mkdir("dist")

    zf = zipfile.ZipFile(
        f"dist/PunchRice-{datetime.datetime.now().strftime(r"%Y%m%d-%H%M%S")}.zip", "w"
    )

    zf.write("./main.py", compress_type=zipfile.ZIP_DEFLATED)
    for f in glob.glob("./data/*"):
        zf.write(f, compress_type=zipfile.ZIP_DEFLATED)
    print("SUCCESSFULLY")
    os.remove("./main.py")
    print("Cleaning up...")
