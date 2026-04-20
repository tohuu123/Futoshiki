from __future__ import annotations

import multiprocessing as mp
import queue as queue_module
import sys
import traceback
from pathlib import Path
from typing import Optional

try:
    from PyQt6.QtCore import QThread, Qt, pyqtSignal, QSize, QRectF
    from PyQt6.QtGui import QAction, QColor, QFont, QPainter, QPen
    from PyQt6.QtWidgets import (
        QApplication,
        QFileDialog,
        QFormLayout,
        QGraphicsDropShadowEffect,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QComboBox,
        QSizePolicy,
        QSplitter,
        QToolButton,
        QVBoxLayout,
        QWidget,
    )
except ImportError as exc:  # pragma: no cover - runtime dependency
    raise SystemExit(
        "PyQt6 is not installed. Install it with `pip install PyQt6` "
        "(or use a PyQt6 version compatible with your Python interpreter)."
    ) from exc

from Helper import print_output
from Solver import Method, Solver
from parser import FutoshikiInput, parse_futoshiki


SOURCE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SOURCE_DIR.parent
INPUTS_DIR = SOURCE_DIR / "Inputs"
OUTPUTS_DIR = SOURCE_DIR / "Outputs"


def apply_shadow(widget: QWidget, blur: float = 22.0, alpha: int = 55, offset_y: float = 6.0) -> None:
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(0.0, offset_y)
    effect.setColor(QColor(0, 145, 196, alpha))
    widget.setGraphicsEffect(effect)


def clone_futo(futo: FutoshikiInput) -> FutoshikiInput:
    return FutoshikiInput(
        futo.N,
        [row[:] for row in futo.grid],
        [row[:] for row in futo.h_constraints],
        [row[:] for row in futo.v_constraints],
    )


def solve_method_from_key(key: str) -> Method:
    mapping = {
        "bruteforce": Method.BRUTE_FORCE,
        "backtracking": Method.BACKTRACKING,
        "backward_chaining": Method.BACKWARD_CHAINING,
        "forward_chaining": Method.FORWARD_CHAINING,
        "astar": Method.ASTAR,
    }
    return mapping[key]


def default_output_path_for(input_path: Path) -> Path:
    stem = input_path.stem
    if stem.startswith("input-"):
        suffix = stem.split("input-", 1)[1]
        return OUTPUTS_DIR / f"output-{suffix}.txt"
    return OUTPUTS_DIR / f"{stem}_output.txt"


def apply_forward_inference_to_grid(base_futo: FutoshikiInput, inferred_facts: Optional[set[str]]) -> FutoshikiInput:
    if not inferred_facts:
        return clone_futo(base_futo)

    result = clone_futo(base_futo)
    pinned: dict[tuple[int, int], int] = {}

    for fact in inferred_facts:
        if not fact.startswith("Val_"):
            continue
        parts = fact.split("_")
        if len(parts) != 4:
            continue
        try:
            i, j, v = int(parts[1]), int(parts[2]), int(parts[3])
        except ValueError:
            continue
        pinned[(i - 1, j - 1)] = v

    for (r, c), v in pinned.items():
        if 0 <= r < result.N and 0 <= c < result.N:
            result.grid[r][c] = v

    return result


def _solver_process_entry(futo: FutoshikiInput, method_key: str, heuristic_key: str, result_queue) -> None:
    try:
        solver = Solver(clone_futo(futo))
        method = solve_method_from_key(method_key)
        heuristic = heuristic_key if method == Method.ASTAR else "hrc"
        result = solver.solve(method, heuristic_name=heuristic)
        result_queue.put(("result", result))
    except Exception:
        result_queue.put(("error", traceback.format_exc()))


class SolverWorker(QThread):
    finished_result = pyqtSignal(object)
    failed = pyqtSignal(str)
    cancelled = pyqtSignal(str)

    def __init__(self, futo: FutoshikiInput, method_key: str, heuristic_key: str):
        super().__init__()
        self._futo = clone_futo(futo)
        self._method_key = method_key
        self._heuristic_key = heuristic_key

    def request_stop(self) -> None:
        self.requestInterruption()

    @staticmethod
    def _terminate_process(proc) -> None:
        if proc is None or not proc.is_alive():
            return
        proc.terminate()
        proc.join(timeout=1.0)
        if proc.is_alive() and hasattr(proc, "kill"):
            proc.kill()
            proc.join(timeout=1.0)

    def run(self) -> None:
        ctx = mp.get_context("spawn")
        result_queue = ctx.Queue()
        proc = ctx.Process(
            target=_solver_process_entry,
            args=(self._futo, self._method_key, self._heuristic_key, result_queue),
        )
        proc.start()

        try:
            while True:
                if self.isInterruptionRequested():
                    self._terminate_process(proc)
                    self.cancelled.emit("Stopped by user.")
                    return

                try:
                    kind, payload = result_queue.get(timeout=0.1)
                except queue_module.Empty:
                    if proc.is_alive():
                        continue
                    proc.join(timeout=0.2)
                    try:
                        kind, payload = result_queue.get_nowait()
                    except queue_module.Empty:
                        self.failed.emit("Solver process ended unexpectedly without returning a result.")
                        return

                if kind == "result":
                    self.finished_result.emit(payload)
                else:
                    self.failed.emit(payload)
                return
        finally:
            self._terminate_process(proc)
            result_queue.close()
            result_queue.join_thread()


class FutoshikiBoardWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._futo: Optional[FutoshikiInput] = None
        self._givens: set[tuple[int, int]] = set()
        self.setMinimumSize(520, 520)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def sizeHint(self) -> QSize:
        return QSize(700, 700)

    def set_board(self, futo: Optional[FutoshikiInput], givens: Optional[set[tuple[int, int]]] = None) -> None:
        self._futo = clone_futo(futo) if futo is not None else None
        self._givens = set(givens or set())
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        bg = QColor("#e9fbff")
        stroke = QColor("#0e7490")
        tile_bg = QColor("#ffffff")
        value_color = QColor("#083344")
        constraint_color = QColor("#000000")
        shadow = QColor("#7dd3fc")

        painter.fillRect(self.rect(), bg)

        if self._futo is None:
            painter.setPen(QPen(stroke, 1.5))
            painter.setFont(QFont("Segoe UI", 14, QFont.Weight.DemiBold))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Load an input file to preview the puzzle")
            return

        n = self._futo.N
        margin = 28
        if n <= 4:
            gap = 36
        elif n == 5:
            gap = 30
        elif n == 6:
            gap = 24
        else:
            gap = 18

        available_w = self.width() - 2 * margin - (n - 1) * gap
        available_h = self.height() - 2 * margin - (n - 1) * gap
        cell = max(24, min(available_w // n, available_h // n))

        board_w = n * cell + (n - 1) * gap
        board_h = n * cell + (n - 1) * gap
        start_x = (self.width() - board_w) / 2
        start_y = (self.height() - board_h) / 2

        outer_shadow = QRectF(start_x - 16, start_y - 10, board_w + 32, board_h + 32)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(shadow)
        painter.drawRoundedRect(outer_shadow, 24, 24)

        painter.setPen(QPen(stroke, 2.0))
        painter.setBrush(QColor(255, 255, 255, 150))
        outer = QRectF(start_x - 18, start_y - 18, board_w + 36, board_h + 36)
        painter.drawRoundedRect(outer, 22, 22)

        number_font = QFont("Segoe UI", max(12, int(cell * 0.28)))
        number_font.setBold(True)
        given_font = QFont(number_font)
        given_font.setWeight(QFont.Weight.Black)

        if n <= 5:
            constraint_size = max(20, min(int(cell * 0.30), int(gap * 0.92)))
        else:
            constraint_size = max(13, min(int(cell * 0.22), int(gap * 0.90)))
        constraint_font = QFont("Segoe UI", constraint_size)
        constraint_font.setBold(True)

        for r in range(n):
            for c in range(n):
                x = start_x + c * (cell + gap)
                y = start_y + r * (cell + gap)
                rect = QRectF(x, y, cell, cell)

                shadow_rect = QRectF(x, y + 5, cell, cell)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(56, 189, 248, 32))
                painter.drawRoundedRect(shadow_rect, 14, 14)

                painter.setPen(QPen(stroke, 2.0))
                painter.setBrush(tile_bg)
                painter.drawRoundedRect(rect, 14, 14)

                value = self._futo.grid[r][c]
                if value:
                    painter.setPen(value_color)
                    painter.setFont(given_font if (r, c) in self._givens else number_font)
                    painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(value))

                if c < n - 1:
                    rel = self._futo.h_constraints[r][c]
                    if rel != 0:
                        painter.setPen(QPen(constraint_color, 2.0))
                        painter.setFont(constraint_font)
                        symbol = "<" if rel == 1 else ">"
                        cx = x + cell + gap / 2
                        crect = QRectF(cx - gap * 0.55, y, gap * 1.10, cell)
                        painter.drawText(crect, Qt.AlignmentFlag.AlignCenter, symbol)

                if r < n - 1:
                    rel = self._futo.v_constraints[r][c]
                    if rel != 0:
                        painter.setPen(QPen(constraint_color, 2.0))
                        painter.setFont(constraint_font)
                        symbol = "^" if rel == 1 else "v"
                        cy = y + cell + gap / 2
                        crect = QRectF(x, cy - gap * 0.55, cell, gap * 1.10)
                        painter.drawText(crect, Qt.AlignmentFlag.AlignCenter, symbol)


class ArrowComboBox(QComboBox):
    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        color = QColor("#0e7490") if self.isEnabled() else QColor("#94a3b8")
        painter.setPen(color)
        arrow_font = QFont("Segoe UI Symbol", 12, QFont.Weight.Bold)
        painter.setFont(arrow_font)
        arrow_rect = self.rect().adjusted(self.width() - 26, 0, -8, 0)
        painter.drawText(arrow_rect, int(Qt.AlignmentFlag.AlignCenter), "▾")
        painter.end()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Futoshiki Solver — PyQt6")
        self.resize(1360, 860)

        self.original_futo: Optional[FutoshikiInput] = None
        self.current_futo: Optional[FutoshikiInput] = None
        self.current_input_path: Optional[Path] = None
        self.last_result = None
        self.worker: Optional[SolverWorker] = None
        self.log_messages: list[str] = []

        self.method_specs = [
            ("Brute Force", "bruteforce"),
            ("Backtracking", "backtracking"),
            ("Backward Chaining", "backward_chaining"),
            ("Forward Chaining", "forward_chaining"),
            ("A* Search", "astar"),
        ]

        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background: #eefcff;
                color: #0f172a;
                font-family: 'Segoe UI';
                font-size: 14px;
            }
            QMenuBar {
                background: #dff7ff;
                color: #0f172a;
                border-bottom: 1px solid #bae6fd;
            }
            QMenuBar::item:selected, QMenu::item:selected {
                background: #bae6fd;
                border-radius: 8px;
            }
            QGroupBox {
                border: 2px solid #0ea5c6;
                border-radius: 20px;
                margin-top: 14px;
                padding: 14px;
                font-weight: 700;
                color: #0e7490;
                background: rgba(255, 255, 255, 0.84);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 6px 0 6px;
            }
            QLabel {
                background: transparent;
            }
            QPushButton, QToolButton, QLineEdit {
                background: #ffffff;
                border: 2px solid #38bdf8;
                border-radius: 14px;
                padding: 9px 12px;
                selection-background-color: #38bdf8;
            }
            QComboBox {
                background: #ffffff;
                border: 2px solid #38bdf8;
                border-radius: 14px;
                padding: 9px 34px 9px 12px;
                selection-background-color: #38bdf8;
            }
            QPushButton:hover, QToolButton:hover, QComboBox:hover, QLineEdit:hover {
                background: #f0fbff;
                border-color: #06b6d4;
            }
            QPushButton:pressed, QToolButton:pressed {
                background: #dff7ff;
            }
            QPushButton:disabled {
                color: #94a3b8;
                border-color: #cbd5e1;
                background: #f8fafc;
            }
            QComboBox:disabled, QLineEdit:disabled, QToolButton:disabled {
                color: #94a3b8;
                border-color: #cbd5e1;
                background: #f8fafc;
            }
            QPushButton[accent="true"] {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #22d3ee, stop:1 #0ea5e9);
                color: white;
                border: none;
                font-weight: 700;
            }
            QPushButton[accent="true"]:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #67e8f9, stop:1 #38bdf8);
            }
            QPushButton[danger="true"] {
                background: #ecfeff;
                color: #0f766e;
                border: 2px solid #2dd4bf;
                font-weight: 700;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
                subcontrol-origin: padding;
                subcontrol-position: top right;
            }
            QComboBox::down-arrow {
                image: none;
                width: 0px;
                height: 0px;
            }
            QSplitter::handle {
                background: transparent;
                width: 10px;
            }
            QLabel[role="metric"] {
                font-weight: 700;
                color: #0e7490;
            }
            QLabel[role="value"] {
                color: #0f172a;
            }
            QStatusBar {
                background: #dff7ff;
                color: #0f172a;
            }
            """
        )

        self._build_ui()
        self._build_menu()
        self.refresh_inputs()
        if self.input_combo.count() > 0:
            self.load_selected_input()

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("File")
        open_action = QAction("Open input…", self)
        open_action.triggered.connect(self.browse_input)
        file_menu.addAction(open_action)

        save_action = QAction("Save output…", self)
        save_action.triggered.connect(self.save_output)
        file_menu.addAction(save_action)

        refresh_action = QAction("Refresh inputs", self)
        refresh_action.triggered.connect(self.refresh_inputs)
        file_menu.addAction(refresh_action)

    def _build_ui(self) -> None:
        title = QLabel("Futoshiki Solver")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            "font-size: 34px; font-weight: 800; color: #0b5f76; padding: 10px; border: 2px solid #0ea5c6; border-radius: 24px; background: rgba(255, 255, 255, 0.92);"
        )

        self.board = FutoshikiBoardWidget()

        left_group = QGroupBox("Puzzle")
        left_layout = QVBoxLayout(left_group)
        self.board_title = QLabel("No puzzle loaded")
        self.board_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #0e7490;")
        left_layout.addWidget(self.board_title)
        left_layout.addWidget(self.board, 1)

        controls_group = QGroupBox("Controls")
        controls_layout = QVBoxLayout(controls_group)

        input_row = QHBoxLayout()
        self.input_combo = ArrowComboBox()
        self.input_combo.setMinimumWidth(320)
        self.load_btn = QPushButton("Load")
        self.load_btn.clicked.connect(self.load_selected_input)
        self.browse_btn = QToolButton()
        self.browse_btn.setText("Browse…")
        self.browse_btn.clicked.connect(self.browse_input)
        self.refresh_btn = QToolButton()
        self.refresh_btn.setText("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_inputs)
        input_row.addWidget(self.input_combo, 1)
        input_row.addWidget(self.load_btn)
        input_row.addWidget(self.browse_btn)
        input_row.addWidget(self.refresh_btn)

        method_row = QHBoxLayout()
        self.method_combo = ArrowComboBox()
        for label, key in self.method_specs:
            self.method_combo.addItem(label, key)
        self.method_combo.currentIndexChanged.connect(self._sync_heuristic_state)
        self.heuristic_combo = ArrowComboBox()
        self.heuristic_combo.addItem("hrc", "hrc")
        self.heuristic_combo.addItem("h0", "h0")
        self.heuristic_combo.setCurrentIndex(0)
        method_row.addWidget(self.method_combo, 1)
        method_row.addWidget(self.heuristic_combo)

        output_row = QHBoxLayout()
        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("Output file path")
        self.save_btn = QPushButton("Save Output")
        self.save_btn.clicked.connect(self.save_output)
        output_row.addWidget(self.output_edit, 1)
        output_row.addWidget(self.save_btn)

        action_row = QHBoxLayout()
        self.solve_btn = QPushButton("Solve")
        self.solve_btn.setProperty("accent", "true")
        self.solve_btn.clicked.connect(self.start_solve)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setProperty("danger", "true")
        self.stop_btn.clicked.connect(self.stop_solve)
        self.stop_btn.setEnabled(False)
        self.restore_btn = QPushButton("Restore Original")
        self.restore_btn.clicked.connect(self.restore_original_board)
        action_row.addWidget(self.solve_btn)
        action_row.addWidget(self.stop_btn)
        action_row.addWidget(self.restore_btn)

        controls_layout.addWidget(QLabel("Input file"))
        controls_layout.addLayout(input_row)
        controls_layout.addWidget(QLabel("Method + heuristic"))
        controls_layout.addLayout(method_row)
        controls_layout.addWidget(QLabel("Output file"))
        controls_layout.addLayout(output_row)
        controls_layout.addSpacing(6)
        controls_layout.addLayout(action_row)
        controls_layout.addStretch(1)

        apply_shadow(controls_group, blur=24, alpha=45, offset_y=8)

        metrics_group = QGroupBox("Run summary")
        metrics_layout = QFormLayout(metrics_group)
        self.metric_labels = {}
        for key in ["status", "time", "memory", "expansions", "generated", "backtracks", "inferences", "notes"]:
            left = QLabel(key.capitalize())
            left.setProperty("role", "metric")
            value = QLabel("—")
            value.setWordWrap(True)
            value.setProperty("role", "value")
            metrics_layout.addRow(left, value)
            self.metric_labels[key] = value

        apply_shadow(left_group, blur=26, alpha=38, offset_y=8)
        apply_shadow(metrics_group, blur=24, alpha=42, offset_y=8)
        apply_shadow(title, blur=28, alpha=48, offset_y=8)
        apply_shadow(self.solve_btn, blur=18, alpha=55, offset_y=5)
        apply_shadow(self.save_btn, blur=16, alpha=35, offset_y=4)
        apply_shadow(self.restore_btn, blur=16, alpha=30, offset_y=4)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(16)
        right_layout.addWidget(controls_group, 3)
        right_layout.addWidget(metrics_group, 2)

        splitter = QSplitter()
        splitter.addWidget(left_group)
        splitter.addWidget(right_panel)
        splitter.setSizes([800, 560])
        splitter.setChildrenCollapsible(False)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(title)
        layout.addWidget(splitter, 1)
        self.setCentralWidget(central)

        self._sync_heuristic_state()

    def _sync_heuristic_state(self) -> None:
        is_astar = self.current_method_key() == "astar"
        self.heuristic_combo.setEnabled(is_astar)

    def append_log(self, message: str) -> None:
        self.log_messages.append(message)
        if len(self.log_messages) > 500:
            self.log_messages = self.log_messages[-500:]
        self.statusBar().showMessage(message, 5000)

    def current_method_key(self) -> str:
        return self.method_combo.currentData()

    def current_heuristic_key(self) -> str:
        return self.heuristic_combo.currentData()

    def current_givens(self) -> set[tuple[int, int]]:
        if self.original_futo is None:
            return set()
        givens = set()
        for r in range(self.original_futo.N):
            for c in range(self.original_futo.N):
                if self.original_futo.grid[r][c] != 0:
                    givens.add((r, c))
        return givens

    def refresh_inputs(self) -> None:
        self.input_combo.clear()
        if INPUTS_DIR.exists():
            for path in sorted(INPUTS_DIR.glob("*.txt")):
                self.input_combo.addItem(path.name, str(path))
        self.append_log(f"[refresh] Inputs directory scanned: {INPUTS_DIR}")

    def load_selected_input(self) -> None:
        path_text = self.input_combo.currentData()
        if not path_text:
            return
        self.load_input_file(Path(path_text))

    def browse_input(self) -> None:
        start_dir = str(INPUTS_DIR if INPUTS_DIR.exists() else SOURCE_DIR)
        chosen, _ = QFileDialog.getOpenFileName(self, "Choose input file", start_dir, "Text files (*.txt);;All files (*)")
        if not chosen:
            return
        path = Path(chosen)
        index = self.input_combo.findData(str(path))
        if index == -1:
            self.input_combo.addItem(path.name, str(path))
            self.input_combo.setCurrentIndex(self.input_combo.count() - 1)
        else:
            self.input_combo.setCurrentIndex(index)
        self.load_input_file(path)

    def load_input_file(self, path: Path) -> None:
        try:
            futo = parse_futoshiki(str(path))
        except Exception as exc:
            QMessageBox.critical(self, "Invalid input", f"Could not parse input file:\n{path}\n\n{exc}")
            self.append_log(f"[error] Failed to parse {path}: {exc}")
            return

        self.current_input_path = path
        self.original_futo = clone_futo(futo)
        self.current_futo = clone_futo(futo)
        self.last_result = None
        self.board.set_board(self.current_futo, self.current_givens())
        self.board_title.setText(f"{path.name}  •  {futo.N}x{futo.N}")
        self.output_edit.setText(str(default_output_path_for(path)))
        self._reset_metrics()
        self.append_log(f"[load] Loaded {path}")

    def restore_original_board(self) -> None:
        if self.original_futo is None:
            return
        self.current_futo = clone_futo(self.original_futo)
        self.board.set_board(self.current_futo, self.current_givens())
        self.append_log("[restore] Restored original puzzle state")

    def _reset_metrics(self) -> None:
        for label in self.metric_labels.values():
            label.setText("—")

    def _set_busy(self, busy: bool) -> None:
        self.solve_btn.setEnabled(not busy)
        self.stop_btn.setEnabled(busy)
        self.method_combo.setEnabled(not busy)
        self.heuristic_combo.setEnabled(not busy and self.current_method_key() == "astar")
        self.input_combo.setEnabled(not busy)
        self.load_btn.setEnabled(not busy)
        self.browse_btn.setEnabled(not busy)
        self.refresh_btn.setEnabled(not busy)

    def start_solve(self) -> None:
        if self.original_futo is None:
            QMessageBox.information(self, "No input", "Load an input file first.")
            return
        if self.worker is not None and self.worker.isRunning():
            QMessageBox.information(self, "Solver running", "A solve job is already running.")
            return

        method_key = self.current_method_key()
        heuristic_key = self.current_heuristic_key()
        method_label = self.method_combo.currentText()
        heuristic_label = heuristic_key if method_key == "astar" else "n/a"

        self.append_log(f"[run] Starting {method_label} (heuristic={heuristic_label})")
        self._set_busy(True)
        self.worker = SolverWorker(self.original_futo, method_key, heuristic_key)
        self.worker.finished_result.connect(self.on_solve_finished)
        self.worker.failed.connect(self.on_solve_failed)
        self.worker.cancelled.connect(self.on_solve_cancelled)
        self.worker.finished.connect(self._on_worker_finished)
        self.worker.start()

    def stop_solve(self) -> None:
        if self.worker is None or not self.worker.isRunning():
            return
        self.metric_labels["status"].setText("STOPPING…")
        self.metric_labels["notes"].setText("Stop requested by user.")
        self.stop_btn.setEnabled(False)
        self.append_log("[stop] Stop requested")
        self.worker.request_stop()

    def _on_worker_finished(self) -> None:
        self._set_busy(False)
        if self.worker is not None:
            self.worker.deleteLater()
            self.worker = None

    def on_solve_cancelled(self, message: str) -> None:
        self.metric_labels["status"].setText("STOPPED")
        self.metric_labels["notes"].setText(message)
        self.append_log(f"[stopped] {message}")

    def on_solve_finished(self, result) -> None:
        self.last_result = result
        display_futo = result.futo
        if result.method == Method.FORWARD_CHAINING:
            display_futo = apply_forward_inference_to_grid(self.original_futo, result.inferred)
        self.current_futo = clone_futo(display_futo)
        self.board.set_board(self.current_futo, self.current_givens())

        self.metric_labels["status"].setText("SUCCESS" if result.success else "FAILED")
        self.metric_labels["time"].setText(f"{result.elapsed:.4f} s")
        self.metric_labels["memory"].setText(f"{result.peak_memory_kb:.2f} KB")
        self.metric_labels["expansions"].setText(str(result.expansions))
        self.metric_labels["generated"].setText(str(result.generated))
        self.metric_labels["backtracks"].setText(str(result.backtracks))
        self.metric_labels["inferences"].setText(str(result.inferences))
        self.metric_labels["notes"].setText(result.notes or "—")

        method_name = result.method.name
        status = "success" if result.success else "failed"
        self.append_log(
            f"[done] {method_name} {status} | time={result.elapsed:.4f}s | "
            f"mem={result.peak_memory_kb:.2f}KB | exp={result.expansions} | inf={result.inferences}"
        )

    def on_solve_failed(self, message: str) -> None:
        self.metric_labels["status"].setText("ERROR")
        self.metric_labels["notes"].setText("Solver crashed before completion.")
        self.append_log("[error] Solve failed unexpectedly")
        self.append_log(message)
        QMessageBox.critical(self, "Solver error", message)

    def save_output(self) -> None:
        if self.current_futo is None:
            QMessageBox.information(self, "Nothing to save", "Load and solve a puzzle first.")
            return

        suggested = self.output_edit.text().strip() or str(default_output_path_for(self.current_input_path or (OUTPUTS_DIR / "output.txt")))
        chosen, _ = QFileDialog.getSaveFileName(self, "Save output", suggested, "Text files (*.txt);;All files (*)")
        if not chosen:
            return

        output_path = Path(chosen)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        temp_dir = output_path.parent
        print_output(self.current_futo, output_path.name, output_dir=str(temp_dir), echo_console=False)
        self.output_edit.setText(str(output_path))
        self.append_log(f"[save] Output saved to {output_path}")
        QMessageBox.information(self, "Saved", f"Output written to:\n{output_path}")


def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
