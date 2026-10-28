# Contributing

Open an issue describing the proposed change before broadening the security
model. Preserve the default fail-closed behavior and independent verification
before checkout. Do not submit production secrets, real private repository
allowlists, internal host paths, or privileged credentials.

Run `python3 -m unittest discover -s tests -v` before proposing changes.
Contributor PRs use the repository's GitHub-hosted CI. CI Lifeboat's self-hosted fallback is scoped separately to approved, protected-branch QA via a dedicated workflow and restricted runner group.
