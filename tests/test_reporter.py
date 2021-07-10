from unittest.mock import MagicMock
from pathlib import Path

def make_distribution(name, files):
    m = MagicMock()
    m.name = name
    m.files = [Path(f) for f in files]
    return m


DISTRIBUTION_FIXTURE = [
    make_distribution(
        "escapism",
        [
            # A package with a single file module
            "__pycache__/escapism.cpython-39.pyc",
            "escapism-1.0.1.dist-info/INSTALLER",
            "escapism-1.0.1.dist-info/LICENSE",
            "escapism-1.0.1.dist-info/METADATA",
            "escapism-1.0.1.dist-info/RECORD",
            "escapism-1.0.1.dist-info/REQUESTED",
            "escapism-1.0.1.dist-info/WHEEL",
            "escapism-1.0.1.dist-info/top_level.txt",
            "escapism.py",
        ],
    ),
    make_distribution(
        # A package with multiple modules / packages
        "statsd",
        [
            "statsd-3.3.0.dist-info/INSTALLER",
            "statsd-3.3.0.dist-info/METADATA",
            "statsd-3.3.0.dist-info/RECORD",
            "statsd-3.3.0.dist-info/REQUESTED",
            "statsd-3.3.0.dist-info/WHEEL",
            "statsd-3.3.0.dist-info/top_level.txt",
            "statsd/__init__.py",
            "statsd/__pycache__/__init__.cpython-39.pyc",
            "statsd/__pycache__/tests.cpython-39.pyc",
            "statsd/client/__init__.py",
            "statsd/client/__pycache__/__init__.cpython-39.pyc",
            "statsd/client/__pycache__/base.cpython-39.pyc",
            "statsd/client/__pycache__/stream.cpython-39.pyc",
            "statsd/client/__pycache__/timer.cpython-39.pyc",
            "statsd/client/__pycache__/udp.cpython-39.pyc",
            "statsd/client/base.py",
            "statsd/client/stream.py",
            "statsd/client/timer.py",
            "statsd/client/udp.py",
            "statsd/defaults/__init__.py",
            "statsd/defaults/__pycache__/__init__.cpython-39.pyc",
            "statsd/defaults/__pycache__/django.cpython-39.pyc",
            "statsd/defaults/__pycache__/env.cpython-39.pyc",
            "statsd/defaults/django.py",
            "statsd/defaults/env.py",
            "statsd/tests.py",
        ],
    ),
]


def test_all_packages(mocker):
    """
    Test resources
    """
    expected_packages = set(['escapism', 'statsd', 'statsd.client', 'statsd.defaults'])
    mocker.patch(
        "importlib_metadata.distributions", return_value=DISTRIBUTION_FIXTURE
    )
    from popularity_contest.reporter import get_all_packages
    assert set(get_all_packages()) == expected_packages


def test_setup(mocker):
    existing_modules = {
        'test_module': None
    }

    register_mock = mocker.patch('atexit.register')

    from popularity_contest import reporter

    assert reporter.ORIGINALLY_LOADED_MODULES == []
    reporter.setup_reporter(existing_modules)
    assert reporter.ORIGINALLY_LOADED_MODULES == ['test_module']
    register_mock.assert_called_once()


def test_used_libraries(mocker):
    mocker.patch(
        "importlib_metadata.distributions", return_value=DISTRIBUTION_FIXTURE
    )

    from popularity_contest.reporter import get_used_libraries
    assert get_used_libraries(
        # Modules loaded after we called the register function
        current_modules={'statsd.defaults': None, 'escapism': None},
        # Modules loaded before we called our register function
        initial_modules={'escapism': None}
    ) == set(['statsd'])
