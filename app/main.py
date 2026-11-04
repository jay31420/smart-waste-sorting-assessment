"""Application entry point."""

import argparse
import os
import sys
from pathlib import Path


# Some Conda-created Windows virtual environments do not expose PyQt's platform
# plugin directory correctly. Docker/Linux is unaffected.
if os.name == "nt" and "QT_QPA_PLATFORM_PLUGIN_PATH" not in os.environ:
    plugin_dir = Path(sys.prefix) / "Lib" / "site-packages" / "PyQt5" / "Qt5" / "plugins" / "platforms"
    if plugin_dir.exists():
        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(plugin_dir)


def parse_args():
    parser = argparse.ArgumentParser(description="智能垃圾分拣招新考核程序")
    parser.add_argument("--sim-host", default=os.environ.get("SIM_HOST", "127.0.0.1"))
    parser.add_argument("--sim-port", default=int(os.environ.get("SIM_PORT", "9000")), type=int)
    parser.add_argument("--transport", choices=("tcp", "serial"), default=os.environ.get("TRANSPORT", "tcp"))
    parser.add_argument("--serial-port", default=os.environ.get("SERIAL_PORT", "/dev/ttyUSB0"))
    parser.add_argument("--baudrate", default=int(os.environ.get("BAUDRATE", "9600")), type=int)
    parser.add_argument(
        "--source",
        choices=("video", "camera"),
        default=os.environ.get("SOURCE", "video"),
    )
    parser.add_argument(
        "--source-value",
        default=os.environ.get("SOURCE_VALUE", "assets/assessment_demo.mp4"),
    )
    parser.add_argument("--weights", default=os.environ.get("YOLO_WEIGHTS", "Predict/best.pt"))
    parser.add_argument("--confidence", default=float(os.environ.get("YOLO_CONFIDENCE", "0.50")), type=float)
    parser.add_argument("--auto-start", action="store_true")
    return parser.parse_args()


def main() -> None:
    from PyQt5 import QtCore, QtWidgets

    from .ui import MainWindow
    from .worker import SortingWorker

    args = parse_args()
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    app = QtWidgets.QApplication(sys.argv)
    worker = SortingWorker(
        sim_host=args.sim_host,
        sim_port=args.sim_port,
        source_kind=args.source,
        source_value=args.source_value,
        weights=args.weights,
        confidence=args.confidence,
        transport_kind=args.transport,
        serial_port=args.serial_port,
        baudrate=args.baudrate,
    )
    window = MainWindow(worker, auto_start=args.auto_start)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
