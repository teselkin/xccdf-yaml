=======================
Notes
=======================

There are a couple of examples.
I assume we will use pkg parser, but all stated below
also applies to the file and pattern_match parsers.

In the benchmark file you set the next rule:

.. code-block: yaml
  rules:
  - check_sssd_version_1161_or_greater_is_installed:
    type: pkg
    name: sssd
    version: 1.16.1
    match: ge

In the resulting oval xml such rule will be converted into one state, one
object and one test.

It's also possible to use a list of packages names instead of a single
package name.

.. code-block: yaml
  rules:
  - check_rsh_packages_are_uninstalled:
    type: pkg
    name:
    - rsh-client
    - rsh-redone-client
    removed: true

=======================
Known limitations
======================

You must keep in mind what there is a "*feature*".
If you use a list of names and in the same time use version - version and
matching will be applied to the each list's element. Thus, the next rule will
be converted into 6 states, 6 objest and 6 tests.
Version and matching will be applied to **each package**.

.. code-block: yaml
  rules:
  - check_ssh_packages_version_77p13_are_installed:
    type: pkg
    name:
    - openssh-client
    - openssh-server
    version: 7.7.p1-3
    match: ge

The same applies to the file (filename) and to the pattern_match (filename)
parsers.

