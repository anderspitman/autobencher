[![Build Status](https://travis-ci.org/anderspitman/autobencher.svg?branch=master)](https://travis-ci.org/anderspitman/autobencher)
[![Coverage Status](https://coveralls.io/repos/anderspitman/autobencher/badge.svg?branch=master&service=github)](https://coveralls.io/github/anderspitman/autobencher?branch=master)

autobencher is a tool for automatically running
[asv](https://github.com/spacetelescope/asv)
benchmarks for Python projects hosted on GitHub. It runs as a server process
and listens for
[GitHub Webhooks](https://developer.github.com/webhooks/)
requests for pull requests  and updates to master and runs benchmarks. It uses
the
[GitHub status API](https://developer.github.com/v3/repos/statuses/)
to report the results of the benchmark runs, similar to how TravisCI and
coveralls report. Currently result plots for benchmark runs are hosted
statically on Amazon S3, which allows the plots to be viewed.
