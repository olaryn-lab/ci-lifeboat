# CI Lifeboat release checklist

This project is open-source **software that configures dispatch**; it is not a
hosted GitHub runner service and does not provision a machine. The maintainer
must explicitly approve release after security review.

## Source review

- [ ] Read README, SECURITY and CONTRIBUTING; ensure no private org names,
      machine paths, hostnames, private account details, fingerprints or tokens.
- [ ] Scan **all tracked files and entire Git history** for credentials,
      proprietary recipes and internal infrastructure. Use dedicated tooling
      (e.g. gitleaks or equivalent) where available.
- [ ] Confirm Apache-2.0 rights for every included source/dependency and
      include third-party notices when needed.
- [ ] Confirm the public repository uses GitHub-hosted CI for contributor PRs;
      any self-hosted access is separately scoped to an approved protected-branch
      fallback workflow.
- [ ] Review the fallback example for protected branch, exact commit, evidence
      validation before checkout, pinned Actions, restricted permissions,
      no implicit deploy and no secret access.
- [ ] Review GitHub runner-group scope/restrictions outside this repository.
- [ ] Configure GitHub Private Vulnerability Reporting and protected main.
- [ ] Document and verify the release tag/version and changelog.

## Validation commands

```sh
python3 -m unittest discover -s tests -v
python3 -m compileall -q ci_lifeboat
python3 -m pip wheel --no-deps -w /tmp/ci-lifeboat-dist .
git diff --check
git status --porcelain=v1
```

Inspect the wheel contents and a fresh installation if possible. Keep any
real `config.toml` outside the repository. Review failures and warnings;
do not bypass gates to meet a date.

## Proof still required before announcing production readiness

- [ ] Manually test dry-run against a private approved test repository.
- [ ] Confirm an ordinary failing hosted test never dispatches fallback.
- [ ] Observe a genuine hosted quota/billing refusal or a carefully controlled
      isolated test that proves the **independent workflow** guard.
- [ ] Exercise runner-offline and GitHub API failure behavior.
- [ ] Confirm fallback results do not satisfy protected release checks by
      accident.
- [ ] Confirm a private installation's running containers and timer remain
      unchanged.

No publishing to PyPI, creating public releases, or changing repository
visibility should happen until these checks are signed off.
