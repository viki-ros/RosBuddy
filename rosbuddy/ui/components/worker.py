# Worker thread management for ROSBuddy UI
from PyQt6.QtCore import QThread, pyqtSignal, QObject
import traceback
import logging
from typing import Callable

logger = logging.getLogger(__name__)

class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(tuple)
    progress = pyqtSignal(str)
    process_started = pyqtSignal(object)

class Worker(QThread):
    def __init__(self, target_fn: Callable, *args, **kwargs):
        super().__init__()
        self.target_fn = target_fn
        self.args = args
        self.target_fn_kwargs = kwargs.copy()
        self.signals = WorkerSignals()

        # Setup realtime_output_callback to emit progress
        original_realtime_callback = self.target_fn_kwargs.pop('realtime_output_callback', self.signals.progress.emit)
        self.target_fn_kwargs['realtime_output_callback'] = original_realtime_callback
        if 'process_started_callback' not in self.target_fn_kwargs:
            self.target_fn_kwargs['process_started_callback'] = self.signals.process_started.emit

    def run(self):
        result_tuple = None
        try:
            logger.debug(f"Worker.run() calling target_fn with args: {self.args}, kwargs: {list(self.target_fn_kwargs.keys())}")
            result_tuple = self.target_fn(*self.args, **self.target_fn_kwargs)
            if not isinstance(result_tuple, tuple) or not (len(result_tuple) == 3 or len(result_tuple) == 4):
                logger.warning(f"target_fn did not return the expected tuple format. Got: {type(result_tuple)}. Content: {result_tuple}")
                self.signals.result.emit((False, str(result_tuple), "Unexpected return format from task", None))
            else:
                logger.debug(f"target_fn (e.g., ToolInvoker) finished. Result success: {result_tuple[0]}")
                self.signals.result.emit(result_tuple)
        except Exception as e:
            logger.error(f"Worker.run() caught ERROR during target_fn execution: {e}", exc_info=True)
            self.signals.error.emit((type(e), e, traceback.format_exc()))
        finally:
            logger.debug("Worker.run() completed. Emitting finished signal.")
            self.signals.finished.emit()
