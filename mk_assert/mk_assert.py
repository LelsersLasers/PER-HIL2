from typing import Callable, Any, Optional

import logging


# Global test state -------------------------------------------------------------------#
g_tests: list["TestFn"] = []
g_active_test: Optional["ActiveTestContext"] = None


class TestFn:
    def __init__(
        self, func: Callable[..., None], args: tuple[Any, ...], kwargs: dict[str, Any]
    ):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self) -> Any:
        logging.info(f"Running test: {self.func.__name__}")
        return self.func(*self.args, **self.kwargs)


class ActiveTestContext:
    def __init__(self, test_fn: TestFn):
        self._test_fn = test_fn
        self._passed: int = 0
        self._failed: int = 0

    def __enter__(self):
        global g_active_test
        g_active_test = self
        return self

    def __exit__(self, exc_type, exc_value, _traceback):
        global g_active_test
        g_active_test = None

        if exc_type is not None:
            self.failure()
            logging.critical(f"Test '{self._test_fn.func.__name__}' raised an exception: {exc_value}")
        
        return False

    def success(self):
        self._passed += 1

    def failure(self):
        self._failed += 1

    def summary(self) -> str:
        total = self._passed + self._failed
        return (
            f"Test '{self._test_fn.func.__name__}':"
            f"{self._passed}/{total} passed, {self._failed} failed."
        )


def add_test(func, *args, run_now: bool = False, **kwargs):
    global g_tests

    logging.debug(f"Adding test: {func.__name__}, run_now={run_now}")
    test_fn = TestFn(func, args, kwargs)
    if run_now:
        run_single_test(test_fn)
    else:
        g_tests.append(test_fn)


def run_single_test(test_fn: TestFn) -> None:
    with ActiveTestContext(test_fn) as active_test:
        test_fn.run()
        print(active_test.summary())


def run_tests():
    global g_tests
    
    logging.debug(f"Running {len(g_tests)} tests...")
    for test_fn in g_tests:
        run_single_test(test_fn)


def clear_tests():
    global g_tests
    logging.debug("Clearing all registered tests.")
    g_tests.clear()


def assert_eq(cond: bool, msg: str = "", negate: bool = False):
    global g_active_test
    if g_active_test is None:
        raise RuntimeError("No active test context for assertion.")

    if cond != negate:
        if msg == "":
            logging.debug("Check passed.")
        else:
            logging.debug(f"Check passed: {msg}")
        g_active_test.success()
    else:
        if msg == "":
            logging.warning("Check failed.")
        else:
            logging.warning(f"Check failed: {msg}")
        g_active_test.failure()


def assert_eqf(a: float, b: float, tol: float, msg: str = "", negate: bool = False):
    assert_eq(abs(a - b) <= tol, msg, negate)
