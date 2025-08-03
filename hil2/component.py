from typing import Callable, Optional


class DO:
    """Digital Output"""

    def __init__(self, set_fn: Callable[[bool], None], hiZ_fn: Callable[[], None]):
        self._set_fn: Callable[[bool], None] = set_fn
        self._hiZ_fn: Callable[[], None] = hiZ_fn

    def set(self, value: bool) -> None:
        self._set_fn(value)

    def hiZ(self) -> None:
        self._hiZ_fn()

    def shutdown(self) -> None:
        self._hiZ_fn()
    

class DI:
    """Digital Input"""

    def __init__(self, get_fn: Callable[[], bool]):
        self._get_fn: Callable[[], bool] = get_fn

    def get(self) -> bool:
        return self._get_fn()
    
    def shutdown(self) -> None:
        pass


class AO:
    """Analog Output"""

    def __init__(self, set_fn: Callable[[float], None], hiZ_fn: Callable[[], None]):
        self._set_fn: Callable[[float], None] = set_fn
        self._hiZ_fn: Callable[[], None] = hiZ_fn

    def set(self, value: float) -> None:
        self._set_fn(value)

    def hiZ(self) -> None:
        self._hiZ_fn()

    def shutdown(self) -> None:
        self._hiZ_fn()


class AI:
    """Analog Input"""

    def __init__(self, get_fn: Callable[[], float]):
        self._get_fn: Callable[[], float] = get_fn

    def get(self) -> float:
        return self._get_fn()
    
    def shutdown(self) -> None:
        pass


class CAN:
    """CAN Bus Interface"""

    def __init__(
        self,
        send_fn: Callable[[str | int, dict], None],
        get_fn: Callable[[str | int], Optional[dict]],
        clear_fn: Callable[[str | int], None]
    ):
        self._send_fn: Callable[[str | int, dict], None] = send_fn
        self._get_fn: Callable[[str | int], Optional[dict]] = get_fn
        self._clear_fn: Callable[[str | int], None] = clear_fn

    def clear(self, signal: str | int = None) -> None:
        self._clear_fn(signal)

    def send(self, signal: str | int, data: dict) -> None:
        self._send_fn(signal, data)
    
    def get(self, signal: str | int) -> Optional[dict]:
        return self._get_fn(signal)
    
    def shutdown(self) -> None:
        pass
    

