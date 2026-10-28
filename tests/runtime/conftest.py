import pytest

from aether.control.settings import Settings
from aether.runtime import Runtime

KEY = b"r" * 32


class FakeClock:
    def __init__(self, t: float = 1000.0):
        self.t = t

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def runtime(tmp_path, clock):
    rt = Runtime(Settings(), tmp_path, KEY, clock=clock, session_id="s-test")
    yield rt
    rt.close()
