# Security policy

## Supported execution scope

CI Lifeboat is designed for trusted QA on an **explicit repository allowlist**, its **protected branch** (the sample uses `main`), and one **dedicated fallback workflow**. The controller verifies GitHub's billing/quota refusal for that branch's current commit, while **GitHub runner groups** independently restrict which repository and workflow can receive self-hosted capacity.

**Allowlisting a repository does not automatically restrict every workflow or ref in that repository.** Both the runner-group policy and the workflow's protected-branch guard are necessary parts of the supported setup. PR heads, fork branches and arbitrary contributor workflows are **outside the fallback scope**; ordinary contributor CI remains GitHub-hosted. For publicly available repositories, the same narrow protected-branch workflow boundary needs explicit review before enabling self-hosted access.

The approved fallback job runs repository code on the operator's machine. Use an isolated runner environment with minimal credentials/permissions, no host Docker socket and no production secrets. A container reduces exposure but is not a complete boundary; ephemeral runner hosts provide additional isolation.

The dispatcher does not create or verify GitHub runner-group policies. Disabling its timer does not cancel already queued GitHub jobs.

Do not report vulnerabilities in public issues with exploit details, host
secrets or access tokens. Before a public GitHub repository exists, report
privately to the project maintainers through a trusted direct channel.
Once published, maintainers should enable GitHub Private Vulnerability
Reporting and document the maintained versions here.

This preview has not been independently security audited.
