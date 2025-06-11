import queue
import threading


class TasksQueue:
    def __init__(self):
        self.tasks = queue.Queue()
        self.worker = threading.Thread(target=self._worker, daemon=True)
        self.worker.start()

    def add_task(self, func, *args, **kwargs):
        self.tasks.put((func, args, kwargs))

    def _worker(self):
        while True:
            func, args, kwargs = self.tasks.get()
            try:
                func(*args, **kwargs)
            except Exception as e:
                print(f"Task failed: {e}")
            self.tasks.task_done()
