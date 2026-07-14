# Release Policy

This package publishes a lean wheel and a broad source distribution.

The wheel contains the importable `quantum_backend_bench` package, bundled JSON
presets, package metadata, entry points, and the license. It is the artifact most
users install.

The source distribution intentionally includes research and reproducibility
assets needed to audit and reproduce the workflow around the core package: tests,
examples, tutorial notebooks, schema files, documentation source, generated
documentation assets, reference results, citation metadata, and the development
container definition. These assets support review of SDK comparison and
translation behavior, but they are not the lean install surface. This makes the
sdist larger than the wheel by design.

Release checks should fail when either artifact drifts unexpectedly:

- the wheel should stay focused on installable package files
- the sdist should keep the reproducibility assets listed above
- archive growth should be reviewed rather than accepted silently

The CI release-artifact checker enforces representative content expectations and
a coarse size budget for the sdist.
