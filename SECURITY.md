# Security policy

CI Lifeboat dispatches jobs that execute repository code on self-hosted hosts.
**Do not run untrusted PRs, fork submissions or public contributions on a
persistent machine**, even if the runner is in a container. A runner host
must not contain personal or production credentials, access to the Docker
socket, or broadly privileged cloud credentials. Use disposable isolated
runners and defense in depth.

GitHub runner groups must restrict repository, workflow and trusted branch
separately; the dispatcher itself does not create or verify those policies.
Disabling a timer does not stop already-queued GitHub Actions runs.

Do not report vulnerabilities in public issues with exploit details, host
secrets or access tokens. Before a public GitHub repository exists, report
privately to the project maintainers through a trusted direct channel.
Once published, maintainers should enable GitHub Private Vulnerability
Reporting and document the maintained versions here.

This preview has not been independently security audited.
