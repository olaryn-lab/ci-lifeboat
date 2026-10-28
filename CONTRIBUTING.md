# Contributing

Open an issue describing the proposed change before broadening the security
model. Preserve the default fail-closed behavior and independent verification
before checkout. Do not submit production secrets, real private repository
allowlists, internal host paths, or privileged credentials.

Run `python3 -m unittest discover -s tests -v` before proposing changes.
Public pull requests must use GitHub-hosted CI only; never self-hosted runners.
