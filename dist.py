#! /usr/bin/env python
import zipfile
import glob
import datetime

if __name__ == "__main__":
    zf = zipfile.ZipFile(
        f"dist/PunchRice-{datetime.datetime.now().strftime(r"%Y%m%d-%H%M%S")}.zip", "w"
    )

    zf.write("./main.py", compress_type=zipfile.ZIP_DEFLATED)
    for f in glob.glob("./data/*"):
        zf.write(f, compress_type=zipfile.ZIP_DEFLATED)
    print("SUCCESSFULLY")
