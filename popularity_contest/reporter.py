"""
Report list of imported modules to statsd on process exit

In interactive computing installations, figuring out which python
modules are in use is extremely helpful in managing environments
for users.

`setup_reporter` will setup an `atexit` hook, which will
send the list of distributions (libraries) from which packages
have been imported. stdlib and local modules are ignord.
"""
import atexit
import os
import sys

from importlib_metadata import distributions
from statsd import StatsClient


def setup_reporter(current_modules: set=None):
    """
    Initialize the reporter

    Saves the list of currently loaded modules, so they can be
    excluded when reporting
    """
    if current_modules is None:
        # Make a copy of packages that have already been loaded
        # until this point. These will not be reported to statsd,
        # since these are 'infrastructure' packages that are needed
        # by everyone, regardless of the specifics of the code being
        # written.
        current_modules = set(sys.modules.keys())

    atexit.register(report_popularity, current_modules)

def get_all_packages() -> dict:
    """
    List all installed packages with their distributions

    Returns a dictionary, with the package name as the key
    and the list of Distribution objects the package is
    provided by.

    Warning:
        This makes a bunch of filesystem calls so can be expensive if you
        have a lot of packages installed on a slow filesystem (like NFS).
    """
    packages = {}
    for dist in distributions():
        for f in dist.files:
            if f.name == '__init__.py':
                # If an __init__.py file is present, the parent
                # directory should be counted as a package
                package = str(f.parent).replace('/',  '.')
                packages.setdefault(package, []).append(dist)
            elif f.name == str(f):
                # If it is a top level file, it should be
                # considered as a package by itself
                package = str(f).replace('.py', '')
                packages.setdefault(package, []).append(dist)
    return packages


def get_used_libraries(initial_modules: set, current_modules: set) -> set:
    """
    Return list of libraries with modules that were imported.

    Finds the modules present in current_modules but not in
    initial_modules, and gets the libraries that provide these
    modules.
    """

    all_packages = get_all_packages()

    libraries = set()

    # Ignore modules that were already loaded when we were imported
    imported_modules = current_modules - initial_modules

    for module_name in imported_modules:
        # Only look for packages from distributions explicitly
        # installed in the environment. No stdlib, no local installs.
        if module_name in all_packages:
            for p in all_packages[module_name]:
                libraries.add(p.name)

    return libraries

def report_popularity(initial_modules: set, current_modules: set=None):
    """
    Report imported packages to statsd

    This runs just before a process exits, so must be as fast as
    possible.
    """
    if current_modules is None:
        current_modules = set(sys.modules.keys())
    statsd = StatsClient(
        host=os.environ.get('PYTHON_POPCONTEST_STATSD_HOST', 'localhost'),
        port=int(os.environ.get('PYTHON_POPCONTEST_STATSD_PORT', 8125)),
        prefix=os.environ.get('PYTHON_POPCONTEST_STATSD_PREFIX', 'python_popcon')
    )

    libraries = get_used_libraries(initial_modules, current_modules)

    # Use a statsd pipeline to reduce total network usage
    with statsd.pipeline() as stats_pipe:
        for p in libraries:
            stats_pipe.incr(f'library_used.{p}', 1)
        stats_pipe.send()

    statsd.incr('reports', 1)
