"""
Report list of imported modules to statsd on process exit

In interactive computing installations, figuring out which python
modules are in use is extremely helpful in managing environments
for users.

On import, this module will setup an `atexit` hook, which will
send the list of distributions (libraries) from which packages
have been imported. stdlib and local modules are ignord.
"""
import sys
import atexit
import os
from statsd import StatsClient
from importlib_metadata import distributions

# Make a copy of packages that have already been loaded
# until this point. These will not be reported to statsd,
# since these are 'infrastructure' packages that are needed
# by everyone, regardless of the specifics of the code being
# written.
ORIGINALLY_LOADED_MODULES = []

def setup_reporter(current_modules=None):
    """
    Initialize the reporter

    Saves the list of currently loaded modules in a global
    variable, so we can ignore the modules that were imported
    before this method was called.
    """
    if current_modules is None:
        current_modules = sys.modules
    global ORIGINALLY_LOADED_MODULES
    ORIGINALLY_LOADED_MODULES = list(current_modules.keys())

    atexit.register(report_popularity)

def get_all_packages():
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


def get_used_libraries(current_modules, initial_modules):
    """
    Return list of libraries with modules that were imported.

    Finds the modules present in current_modules but not in
    initial_modules, and gets the libraries that provide these
    modules.
    """

    all_packages = get_all_packages()

    libraries = set()

    for module_name in current_modules:
        if module_name in initial_modules:
            # Ignore modules that were already loaded when we were imported
            continue

        # Only look for packages from distributions explicitly
        # installed in the environment. No stdlib, no local installs.
        if module_name in all_packages:
            for p in all_packages[module_name]:
                libraries.add(p.name)

    return libraries

def report_popularity(current_modules=None):
    """
    Report imported packages to statsd

    This runs just before a process exits, so must be as fast as
    possible.
    """
    if current_modules is None:
        current_modules = sys.modules
    statsd = StatsClient(
        host=os.environ.get('PYTHON_POPCONTEST_STATSD_HOST', 'localhost'),
        port=int(os.environ.get('PYTHON_POPCONTEST_STATSD_PORT', 8125)),
        prefix=os.environ.get('PYTHON_POPCONTEST_STATSD_PREFIX', 'python_popcon')
    )

    libraries = get_used_libraries(current_modules, ORIGINALLY_LOADED_MODULES)

    # Use a statsd pipeline to reduce total network usage
    with statsd.pipeline() as stats_pipe:
        for p in libraries:
            stats_pipe.incr(f'library_used.{p}', 1)
        stats_pipe.send()

    statsd.incr('reports', 1)
