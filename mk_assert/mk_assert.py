from typing import Callable, Any, Optional

import logging

import print_helper


# Global test state -------------------------------------------------------------------#
g_tests: list["TestFn"] = []
g_active_test: Optional["ActiveTestContext"] = None
g_setup_fn: Optional[Callable[[], None]] = None
g_teardown_fn: Optional[Callable[[], None]] = None


class TestFn:
    def __init__(
        self, func: Callable[..., None], args: tuple[Any, ...], kwargs: dict[str, Any]
    ):
        self.func: Callable[..., None] = func
        self.args: tuple[Any, ...] = args
        self.kwargs: dict[str, Any] = kwargs

    def run(self) -> None:
        return self.func(*self.args, **self.kwargs)


class ActiveTestContext:
    def __init__(self, test_fn: TestFn):
        self._test_fn = test_fn
        self.passed: int = 0
        self.failed: int = 0

    def __enter__(self):
        global g_active_test
        g_active_test = self
        return self

    def __exit__(self, exc_type, exc_value, _traceback):
        global g_active_test
        g_active_test = None

        if exc_type is not None:
            self.failure()
            logging.critical(
                f"Test '{self._test_fn.func.__name__}' raised an exception: {exc_value}"
            )

        return False

    def success(self):
        self.passed += 1

    def failure(self):
        self.failed += 1


def set_setup_fn(setup_fn: Callable[[], None]) -> None:
    global g_setup_fn
    g_setup_fn = setup_fn


def set_teardown_fn(teardown_fn: Callable[[], None]) -> None:
    global g_teardown_fn
    g_teardown_fn = teardown_fn


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
        if g_setup_fn is not None:
            logging.debug(
                f"Running setup function before test: {test_fn.func.__name__}"
            )
            g_setup_fn()

        logging.debug(f"Running test: {test_fn.func.__name__}")

        print_helper.print_test_start(test_fn.func.__name__)
        test_fn.run()
        print_helper.print_test_summary(
            test_fn.func.__name__,
            active_test.passed,
            active_test.failed,
        )

        if g_teardown_fn is not None:
            logging.debug(
                f"Running teardown function after test: {test_fn.func.__name__}"
            )
            g_teardown_fn()


def run_tests():
    global g_tests

    logging.debug(f"Running {len(g_tests)} tests...")
    for test_fn in g_tests:
        run_single_test(test_fn)
        print()


def clear_tests():
    global g_tests
    logging.debug("Clearing all registered tests.")
    g_tests.clear()


def assert_true(cond: bool, msg: str = "", negate: bool = False):
    global g_active_test
    if g_active_test is None:
        raise RuntimeError("No active test context for assertion.")

    if cond != negate:
        g_active_test.success()
    else:
        g_active_test.failure()

    print_helper.print_assert(msg, cond != negate)


def assert_eqf(a: float, b: float, tol: float, msg: str = "", negate: bool = False):
    assert_true(abs(a - b) <= tol, msg, negate)
