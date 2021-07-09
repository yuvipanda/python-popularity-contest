# python-popularity-contest

In interactive computing installations, figuring out which python
modules are in use is extremely helpful in managing environments
for users.

On import, this module will setup an `atexit` hook, which will
send the list of imported modules to a statsd server for aggregation.

Named after the [debian popularity contest](https://popcon.debian.org/)

## What data is collected?

We want to collect just enough data to help with the following tasks:

1. Remove unused packages that have never been imported. These can
   probably be removed without a lot of breakage for individual
   users

2. Provide aggregate statistics about the 'popularity' of a package
   to add a data point for understanding how important a particular package is
   to a group of users. This can help with funding requests, better
   training recommendations, etc.

To collect the smallest amount of data possible, we aggregate this at
source. Only overall global counts are stored, without any individual
record of each source. This is much better than storing per-user or
per-process records.

The data we have will be a time series for each package, representing
the cumulative count of processes where this package was imported. This
functions as a [prometheus counter](https://prometheus.io/docs/concepts/metric_types/#counter),
which is how eventually queries are written.

## Collection infrastructure

The package emits metrics over the [statsd](https://github.com/statsd/statsd)
protocol, so you need a statsd server running to collect and aggregate
this information. Since statsd only stores global aggregate counts, we
never collect data beyond what we need.

The recommended collection pipeline is:

1. [prometheus_statsd](https://github.com/prometheus/statsd_exporter) as
   the statsd server metrics are sent to.

   A [mapping rule](https://github.com/prometheus/statsd_exporter#glob-matching)
   to convert the statsd metrics into usable prometheus metrics, with
   helpful labels for package names. Instaed of many metrics named like
   `python_popcon_imported_package_<package-name>`, we can get a better
   `python_popcon_imported_package{package="<package-name>}`. A mapping
   rule that works with the default statsd metric name structure would
   look like:

   ```yaml
      mappings:
      - match: "python_popcon.imported_package.*"
        name: "python_popcon_imported_package"
        labels:
          package: "$1"
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
        - match: "python_popcon.imported_package.*"
        name: "python_popcon_imported_package"
        labels:
            package: "$1"
```

## Privacy

Collecting limited, pre-aggregated data helps preserve privacy as much as
possible, and might be sufficient in cases where other data with more
private information (like usernames tied to activity times, etc).

However, side channel attacks are still possible if the entire
set of timeseries data is available. Individual users might have specific
patterns of packages they use, and this might be discernable with enough
analysis. If some packages are uniquely used only by particular users,
this analysis becomes easier. Further aggregation of the data, redaction
of information about packages that don't have a lot of use, etc are methods
that can be used to further anonymize this dataset, based on your needs.

