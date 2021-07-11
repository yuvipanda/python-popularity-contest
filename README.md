# python-popularity-contest

[![codecov](https://codecov.io/gh/yuvipanda/python-popularity-contest/branch/main/graph/badge.svg?token=QD438CBG0S)](https://codecov.io/gh/yuvipanda/python-popularity-contest)
[![PyPI version](https://badge.fury.io/py/popularity-contest.svg)](https://badge.fury.io/py/popularity-contest)
![GitHub Actions](https://github.com/yuvipanda/python-popularity-contest/actions/workflows/lint-and-test.yaml/badge.svg)

In interactive computing installations, figuring out which python
libraries are in use is extremely helpful in managing environments
for users.

python-popularity-contest collects pre-aggregated, anonymized data
on which installed libraries are being actively used by your users.

Named after the [debian popularity contest](https://popcon.debian.org/)

## What data is collected?

We want to collect just enough data to help with the following tasks:

1. Remove unused library that have never been imported. These can
   probably be removed without a lot of breakage for individual
   users

2. Provide aggregate statistics about the 'popularity' of a library
   to add a data point for understanding how important a particular library is
   to a group of users. This can help with funding requests, better
   training recommendations, etc.

To collect the smallest amount of data possible, we aggregate this at
source. Only overall global counts are stored, without any individual
record of each source. This is much better than storing per-user or
per-process records.

The data we have will be a time series for each library, representing the
cumulative count of processes where any module from this library was imported.
This is designed as a [prometheus
counter](https://prometheus.io/docs/concepts/metric_types/#counter), which is
how eventually queries are written.

## Collection infrastructure

`popularity_contest` emits metrics over the [statsd](https://github.com/statsd/statsd)
protocol, so you need a statsd server running to collect and aggregate
this information. Since statsd only stores global aggregate counts, we
never collect data beyond what we need.

The recommended collection pipeline is:

1. [prometheus_statsd](https://github.com/prometheus/statsd_exporter) as
   the statsd server metrics are sent to.

   A [mapping rule](https://github.com/prometheus/statsd_exporter#glob-matching)
   to convert the statsd metrics into usable prometheus metrics, with
   helpful labels for library names. Instaed of many metrics named like
   `python_popcon_library_used_<library-name>`, we can get a better
   `python_popcon_library_used{library="<library-name>"}`. A mapping
   rule that works with the default statsd metric name structure would
   look like:

   ```yaml
      mappings:
      - match: "python_popcon.library_used.*"
        name: "python_popcon_library_used"
        labels:
          library: "$1"
   ```

   You can add additional labels here if you would like.

3. A [prometheus server](https://prometheus.io/) that scrapes the metrics
   from prometheus_statsd and stores it in a queryable form. A tool like
   [grafana](https://grafana.com/) is used to visualize the results.

### Kubernetes setup

If you are running a kubernetes cluster of some sort, you probably already
have prometheus running for metrics collection. prometheus_statsd has
a [helm chart](https://github.com/prometheus-community/helm-charts/tree/main/charts/prometheus-statsd-exporter)
that can be deployed easily on cluster. Here is a sample helm config:

```yaml
service:
    # Tell prometheus server we want metrics scraped from port 9102
    annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9102"

statsd:
    mappingConfig: |-
        mappings:
        - match: "python_popcon.library_used.*"
        name: "python_popcon_library_used
        labels:
            library: "$1"
```

The prometheus-statsd chart has [a bug](https://github.com/prometheus-community/helm-charts/issues/1153)
where `mappingConfig` does not take effect until you restart the prometheus-statsd
pod.

## Installing

`popularity-contest` is available from PyPI, and can be installed
with `pip`.

```bash
python3 -m pip install popularity-contest
```

It must be installed in the environment we want instrumented.

## Usage

### Activation

After installation, the popularity_contest reporter must be explicitly
set up. You can enable reporting for all IPython sessions (and hence Jupyter
Notebook sessions) with an [IPython startup
script](https://switowski.com/blog/ipython-startup-files).

The startup script just needs one line:

```python
import popularity_contest.reporter
popularity_contest.reporter.setup_reporter()
```

Since the instrumentation is usually set up by an admin and not
the user, the preferred path for the script is inside `sys.prefix` - the
location of your virtual environment. For example, if you have a
conda environment installed in `/opt/conda`, you can put the file in
`/opt/conda/etc/ipython/startup/000-popularity-contest.py`. This
way, it also gets loaded before any user specific IPython startup
scripts.

Only modules imported *after* the reporter is set up with
`popularity_contest.reporter.setup_reporter()` will be counted.  This reduces
noise from baseline libraries (like `IPython` or `six`) that are used invisibly
by everyone.

### Statsd server connection info

`popularity_contest` expects the following environment variables
to be set.

1. `PYTHON_POPCONTEST_STATSD_HOST` - the hostname or IP address of
   the server statsd packets will be sent to.
2. `PYTHON_POPCONTEST_STATSD_PORT` - the port to send statsd packets
   to. With the recommended `prometheus_statsd` setup, this will be
   `9125`.
3. `PYTHON_POPCONTEST_STATSD_PREFIX` - the prefix each statsd metric
   will have, defaults to `python_popcon.library_used`. So
   each metric in statsd will be of the form
   `python_popcon.library_used.<library-name>`.

   You can put additional information in this prefix, and use that
   to extract more labels in prometheus. For example, in a
   [zero-to-jupyterhub on k8s](https://z2jh.jupyter.org) setup,
   you can add information about the current hub namespace like this:

   ```yaml
   hub:
     extraConfig:
       07-popularity-contest: |
         import os
         pod_namespace = os.environ['POD_NAMESPACE']
         c.KubeSpawner.environment.update({
            'PYTHON_POPCONTEST_STATSD_PREFIX': f'python_popcon.namespace.{pod_namespace}.library_used'
         })
   ```

   A mapping rule can be added to `prometheus_statsd` to extract the namespace.

   ```yaml
      mappings:
      - match: "python_popcon.namespace.*.library_used.*"
        name: "python_popcon_library_used"
        labels:
          namespace: "$1"
          library: "$2"
   ```

   The prometheus metrics produced out of this will be of the form
   `python_popcon_library_used{library="<library-name>", namespace="<namespace>}`

## Privacy

Collecting limited, pre-aggregated data helps preserve privacy as much as
possible, and might be sufficient in cases where other data with more
private information (like usernames tied to activity times, etc).

However, side channel attacks are still possible if the entire
set of timeseries data is available. Individual users might have specific
patterns of modules they use, and this might be discernable with enough
analysis. If some libraries are uniquely used only by particular users,
this analysis becomes easier. Further aggregation of the data, redaction
of information about modules that don't have a lot of use, etc are methods
that can be used to further anonymize this dataset, based on your needs.

