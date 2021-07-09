"""
Report list of imported modules to statsd on process exit

In interactive computing installations, figuring out which python
modules are in use is extremely helpful in managing environments
for users.

On import, this module will setup an `atexit` hook, which will
send the list of imported modules to a statsd server for aggregation.

"""
import sys
import atexit
import os
from stdlib_list import stdlib_list
from statsd import StatsClient

# Make a copy of packages that have already been loaded
# until this point. These will not be reported to statsd,
# since these are 'infrastructure' packages that are needed
# by everyone, regardless of the specifics of the code being
# written.
ORIGINALLY_LOADED_PACKAGES = list(sys.modules.keys())

def report_popularity():
    """
    Report imported packages to statsd

    This runs just before a process exits, so must be very fast.
    """
    statsd = StatsClient(
        host=os.environ.get('PYTHON_POPCONTEST_STATSD_HOST', 'localhost'),
        port=int(os.environ.get('PYTHON_POPCONTEST_STATSD_PORT', 8125)),
        prefix=os.environ.get('PYTHON_POPCONTEST_STATSD_PREFIX', 'python_popcon.imported_package')
    )

    packages = set()
    for name in sys.modules:
        if name in ORIGINALLY_LOADED_PACKAGES:
            # Ignore packages that were already loaded when we were imported
            continue
        if name in stdlib_list():
            # Ignore packages in stdlib
            continue
        if name[0] == '_':
            # Ignore packages starting with `_`
            continue
        packages.add(name.split('.')[0])

    # Use a statsd pipeline to reduce total network usage
    with statsd.pipeline() as stats_pipe:
        for p in packages:
            stats_pipe.incr(p, 1)
        stats_pipe.send()


atexit.register(report_popularity)

