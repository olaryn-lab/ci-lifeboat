# AGENTS.md — CI Lifeboat installation instructions for coding agents

These instructions apply to agents helping install or modify CI Lifeboat. **Read [docs/INSTALL.md](docs/INSTALL.md), [SECURITY.md](SECURITY.md) and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) first.**

## Goal

Install a **small evidence-verified dispatcher** while leaving GitHub-hosted CI as default. Use the **official GitHub Actions self-hosted runner** for job execution. The controller does not connect to the runner directly and does not register runner software.

## Operating rules

1. **Start read-only.** Inspect the target GitHub organization's runners, repo visibility, protected branches, workflow restrictions, CI recipes and runner credentials before proposing any changes. Never assume the target GitHub account has safe controls by default.
2. **Obtain the user's approval before any side effect:** registering/reconfiguring a runner, changing runner groups/settings, creating/changing GitHub workflows, creating or enabling systemd services, dispatching jobs, introducing credentials, or altering branch protection. If an approval is already explicit, stay within its exact scope.
3. **Fail closed.** Do not weaken or bypass checks, suppress failures, fabricate quota evidence or widen runner access to make a test pass.
4. **Keep secrets out of source and logs.** Never print, copy into chat, or commit registration tokens, PATs, SSH keys or personal configs. Use the GitHub CLI/official auth mechanism and minimal scopes.
5. **Public-source PR CI must stay GitHub-hosted.** Do not run untrusted PRs, forks, or arbitrary community branches on persistent or personal self-hosted machines. Do not grant public repos access to the private runner pool.
6. **Prefer an isolated ephemeral runner.** No host Docker socket, personal home mounts, production credentials or privileged deployment commands.
7. **Do not change protected release gates.** The fallback recipe is additional source-level QA, not a substitute for build provenance, integrations, security scans or production qualification.
8. **Keep existing CI operational.** When migrating, avoid disrupting currently registered runners or systemd timers until the user approves the cutover and rollback.
9. **Validate after every change.** Run offline tests, a dry-run evaluation, config/permission checks, and report exactly what is verified versus still unverified. Avoid live dispatch merely to “see if it works.”

## Suggested sequence

1. Read the project docs and confirm the approved private repositories and desired QA scope.
2. Produce a short installation plan showing credentials, runner-group and protected-branch boundaries; get approval.
3. Install Python CLI in a clean environment and create a private config in `~/.config/ci-lifeboat/config.toml` from the sample.
4. Configure the official runner and restricted runner group **only if approved**.
5. Add the reviewed dedicated fallback workflow and `make ci-fallback` target to each approved repo **only if approved**.
6. Run `python3 -m unittest discover -s tests -v` and `ci-lifeboat` **without `--dispatch`**.
7. Once approved, enable the timer and verify status; do not manufacture real account billing failures.
8. Report the exact files, runner settings, GitHub links, validation results, remaining blockers, and rollback commands.

## Review checklist

- [ ] Exact trusted repository and protected branch
- [ ] Dedicated workflow restricted by runner group
- [ ] Scoped permissions and no secret-bearing environment
- [ ] Local runner isolation and outbound network verified
- [ ] Same-SHA quota evidence validated twice (controller and workflow)
- [ ] Ordinary failures and public fork PRs cannot dispatch fallback
- [ ] Existing CI/release checks are unchanged
- [ ] No secrets/private infrastructure leaked in commits
- [ ] Timer/runner registration changes approved and reversible
