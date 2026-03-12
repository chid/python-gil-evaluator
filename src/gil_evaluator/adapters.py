from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from threading import Lock, Thread
from typing import Protocol

from .cases import Case, CaseType


class LibraryAdapter(Protocol):
    name: str

    def import_check(self) -> tuple[bool, str | None]: ...

    def functional_cases(self) -> list[Case]: ...

    def stress_cases(self) -> list[Case]: ...

    def perf_cases(self) -> list[Case]: ...


@dataclass(slots=True)
class BaseAdapter:
    name: str
    import_name: str

    def import_check(self) -> tuple[bool, str | None]:
        try:
            import_module(self.import_name)
        except Exception as exc:  # pragma: no cover - exercised in integration flows
            return False, f"{type(exc).__name__}: {exc}"
        return True, None

    def functional_cases(self) -> list[Case]:
        return []

    def stress_cases(self) -> list[Case]:
        return []

    def perf_cases(self) -> list[Case]:
        return []


class NumpyAdapter(BaseAdapter):
    def __init__(self) -> None:
        super().__init__(name="numpy", import_name="numpy")

    def functional_cases(self) -> list[Case]:
        def vector_sum() -> dict[str, int]:
            import numpy as np

            arr = np.arange(100_000)
            return {"sum": int(arr.sum())}

        return [Case("numpy.vector_sum", CaseType.FUNCTIONAL, vector_sum)]

    def stress_cases(self) -> list[Case]:
        def threaded_dot() -> dict[str, int]:
            import numpy as np

            left = np.ones((100, 100))
            right = np.ones((100, 100))
            outputs: list[int] = []

            def worker() -> None:
                outputs.append(int(np.dot(left, right).sum()))

            threads = [Thread(target=worker) for _ in range(6)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            return {"runs": len(outputs), "checksum": sum(outputs)}

        return [Case("numpy.threaded_dot", CaseType.STRESS, threaded_dot)]

    def perf_cases(self) -> list[Case]:
        def matrix_multiply() -> dict[str, int]:
            import numpy as np

            left = np.arange(10_000).reshape(100, 100)
            right = np.arange(10_000).reshape(100, 100)
            product = left @ right
            return {"checksum": int(product.sum())}

        return [Case("numpy.matrix_multiply", CaseType.PERF, matrix_multiply)]


class PandasAdapter(BaseAdapter):
    def __init__(self) -> None:
        super().__init__(name="pandas", import_name="pandas")

    def functional_cases(self) -> list[Case]:
        def groupby_agg() -> dict[str, int]:
            import pandas as pd

            frame = pd.DataFrame({"k": ["a", "a", "b"], "v": [1, 2, 3]})
            grouped = frame.groupby("k")["v"].sum().to_dict()
            return {"a": int(grouped["a"]), "b": int(grouped["b"])}

        return [Case("pandas.groupby_agg", CaseType.FUNCTIONAL, groupby_agg)]

    def stress_cases(self) -> list[Case]:
        def threaded_read_write() -> dict[str, int]:
            import pandas as pd

            total = 0
            lock = Lock()

            def worker(seed: int) -> None:
                nonlocal total
                frame = pd.DataFrame({"n": [seed, seed + 1, seed + 2]})
                value = int(frame["n"].sum())
                with lock:
                    total += value

            threads = [Thread(target=worker, args=(idx,)) for idx in range(8)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            return {"total": total}

        return [Case("pandas.threaded_read_write", CaseType.STRESS, threaded_read_write)]

    def perf_cases(self) -> list[Case]:
        def dataframe_transform() -> dict[str, int]:
            import pandas as pd

            frame = pd.DataFrame({"v": range(50_000)})
            transformed = frame.assign(square=lambda x: x["v"] * x["v"])
            return {"checksum": int(transformed["square"].sum())}

        return [Case("pandas.dataframe_transform", CaseType.PERF, dataframe_transform)]


class HttpxAdapter(BaseAdapter):
    def __init__(self) -> None:
        super().__init__(name="httpx", import_name="httpx")

    def functional_cases(self) -> list[Case]:
        def request_build() -> dict[str, int]:
            import httpx

            request = httpx.Request("GET", "https://example.com", params={"x": "1"})
            return {"url_len": len(str(request.url))}

        return [Case("httpx.request_build", CaseType.FUNCTIONAL, request_build)]

    def stress_cases(self) -> list[Case]:
        def concurrent_clients() -> dict[str, int]:
            import httpx

            statuses: list[int] = []

            def worker() -> None:
                transport = httpx.MockTransport(lambda _request: httpx.Response(status_code=200))
                with httpx.Client(transport=transport) as client:
                    response = client.get("https://service.local/health")
                    statuses.append(response.status_code)

            threads = [Thread(target=worker) for _ in range(8)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            return {"ok": statuses.count(200)}

        return [Case("httpx.concurrent_clients", CaseType.STRESS, concurrent_clients)]


class SqlalchemyAdapter(BaseAdapter):
    def __init__(self) -> None:
        super().__init__(name="sqlalchemy", import_name="sqlalchemy")

    def functional_cases(self) -> list[Case]:
        def in_memory_query() -> dict[str, int]:
            from sqlalchemy import text
            from sqlalchemy import create_engine

            engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
            with engine.connect() as connection:
                result = connection.execute(text("select 7 + 5")).scalar_one()
            return {"result": int(result)}

        return [Case("sqlalchemy.in_memory_query", CaseType.FUNCTIONAL, in_memory_query)]

    def stress_cases(self) -> list[Case]:
        def threaded_select() -> dict[str, int]:
            from sqlalchemy import text
            from sqlalchemy import create_engine

            values: list[int] = []
            lock = Lock()

            def worker(seed: int) -> None:
                engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
                with engine.connect() as connection:
                    out = connection.execute(text(f"select {seed} + 1")).scalar_one()
                with lock:
                    values.append(int(out))

            threads = [Thread(target=worker, args=(idx,)) for idx in range(10)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            return {"count": len(values), "sum": sum(values)}

        return [Case("sqlalchemy.threaded_select", CaseType.STRESS, threaded_select)]


class ThreadingBaselineAdapter(BaseAdapter):
    def __init__(self) -> None:
        super().__init__(name="threading_baseline", import_name="threading")

    def functional_cases(self) -> list[Case]:
        def lock_roundtrip() -> dict[str, int]:
            lock = Lock()
            count = 0
            for _ in range(1000):
                with lock:
                    count += 1
            return {"count": count}

        return [Case("threading.lock_roundtrip", CaseType.FUNCTIONAL, lock_roundtrip)]

    def stress_cases(self) -> list[Case]:
        def queue_churn() -> dict[str, int]:
            from queue import Queue

            queue: Queue[int] = Queue()
            outputs: list[int] = []

            def producer() -> None:
                for idx in range(500):
                    queue.put(idx)
                queue.put(-1)

            def consumer() -> None:
                while True:
                    item = queue.get()
                    if item == -1:
                        break
                    outputs.append(item)

            t1 = Thread(target=producer)
            t2 = Thread(target=consumer)
            t1.start()
            t2.start()
            t1.join()
            t2.join()
            return {"processed": len(outputs)}

        return [Case("threading.queue_churn", CaseType.STRESS, queue_churn)]

    def perf_cases(self) -> list[Case]:
        def thread_spawn() -> dict[str, int]:
            done = 0
            lock = Lock()

            def worker() -> None:
                nonlocal done
                with lock:
                    done += 1

            threads = [Thread(target=worker) for _ in range(200)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            return {"done": done}

        return [Case("threading.thread_spawn", CaseType.PERF, thread_spawn)]


def default_adapters() -> list[LibraryAdapter]:
    return [
        ThreadingBaselineAdapter(),
        NumpyAdapter(),
        PandasAdapter(),
        HttpxAdapter(),
        SqlalchemyAdapter(),
    ]
