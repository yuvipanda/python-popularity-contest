# python-popularity-contest

In interactive computing installations, figuring out which python
modules are in use is extremely helpful in managing environments
for users.

On import, this module will setup an `atexit` hook, which will
send the list of imported modules to a statsd server for aggregation.

Named after the [debian popularity contest](https://popcon.debian.org/)