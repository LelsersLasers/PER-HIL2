from typing import Callable, Any, Optional

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
        return self.func(*self.args, **self.kwargs)


class ActiveTestContext:
    def __init__(self, test_fn: TestFn):
        self.test_fn = test_fn
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
            return False
    
    def success(self):
        self.passed += 1
    
    def failure(self):
        self.failed += 1

    def summary(self) -> str:
        total = self.passed + self.failed
        return f"Test '{self.test_fn.func.__name__}': {self.passed}/{total} passed, {self.failed} failed."


def add_test(func, *args, run_now: bool = False, **kwargs):
    global g_tests
    
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

    for test_fn in g_tests:
        run_single_test(test_fn)

def clear_tests():
    global g_tests
    g_tests.clear()


def assert_eq(cond: bool, msg: str = "", negate: bool = False):
    global g_active_test
    if g_active_test is None:
        raise RuntimeError("No active test context for assertion.")
    
    if cond != negate:
        g_active_test.success()
    else:
        g_active_test.failure()

def assert_eqf(a: float, b: float, tol: float, msg: str = "", negate: bool = False):
    assert_eq(abs(a - b) <= tol, msg, negate)
