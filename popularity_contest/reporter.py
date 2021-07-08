"""
Report list of imported modules to statsd on process exit

In interactive computing installations, figuring out which python
modules are in use is extremely helpful in managing environments
for users.

On import, this module will setup an `atexit` hook, which will
send the list of imported modules to a statsd server for aggregation.

"""
import atexit

def report_popularity():
    """
    Report imported packages to statsd

    This runs just before a process exits, so must be very fast.
    """
    # This function is only run on process exit, so imports here
    # will not slow down application load time
    import sys
    import os
    from stdlib_list import stdlib_list
    from statsd import StatsClient

    statsd = StatsClient(
        host=os.environ.get('PYTHON_POPCONTEST_STATSD_HOST', 'localhost'),
        port=int(os.environ.get('PYTHON_POPCONTEST_STATSD_PORT', 8125)),
        prefix=os.environ.get('PYTHON_POPCONTEST_STATSD_PREFIX', 'python_popcon.imported_package')
    )

    packages = set()
    for name in sys.modules:
        if not (name in stdlib_list() or name[0] == '_'):
            # Ignore packages in stdlib or those beginning with _
            # Only send out the first namespace (everything before first .)
            # This granularity of information is usually way more than good enough
            packages.add(name.split('.')[0])

    # Use a statsd pipeline to reduce total network usage
    with statsd.pipeline() as stats_pipe:
        for p in packages:
            stats_pipe.incr(p, 1)
        stats_pipe.send()


atexit.register(report_popularity)

