# AeglysAI qualification technical evidence: sarthakviche

## Fork, branch and commits

- Fork: <https://github.com/sarthakviche/AeglysAI>
- Branch: <https://github.com/sarthakviche/AeglysAI/tree/qualification/sarthakviche>
- Baseline commit tested (unchanged upstream `main`): `48047e46aee115181dc0fd67a45105a0b7a45a45`
- Improvement commit: `57c23b905c43d0340af0876d83e93846dfba0e8a`

## Environment

Windows 11 Home Single Language (build 26300), x86_64. .NET SDK 8.0.427 (runtime 8.0.33),
Python 3.12.5, Git 2.50.1 with the Git for Windows default `core.autocrlf=true`,
Gitleaks 8.30.1 (checksum verified). The Docker CLI is installed, but the daemon was not running.

## Setup

1. Fork the repository and clone the fork.
2. Install a .NET 8 SDK. `global.json` requests 8.0.204 with `latestFeature` roll-forward; 8.0.427 was used.
3. Run the commands in the validation table from the clone root.

## Architecture

Dependencies point inward and architecture tests check this.

- **Domain** holds authorization concepts and invariants: roles, attribute rules, and `RiskContext`,
  which rejects out-of-range indicators and treats an absent signal as unknown, never zero.
- **Application** holds the decision engines and the ports they need, such as
  `IRbacPolicyProvider`, `IRiskContextProvider` and `IAuthorizationAuditSink`. It has no web or storage code.
- **Infrastructure** implements the ports with immutable in-memory providers.
- **Api** is the composition root. It validates JWTs, loads and validates server-side configuration at
  startup, maps endpoints, and handles audit, tracing and metrics.

Request flow: the JWT is validated, the identity comes from the token rather than the request body, and
the endpoint accepts only `resource` and `action`, rejecting unknown JSON fields. The selected engine
decides, one pseudonymized audit event is written, and the response explains the decision.

## A/B/C baseline understanding

- **Model A (RBAC):** allows only if an assigned role grants the permission. The default policy has no grants.
- **Model B (RBAC + ABAC):** also requires every applicable attribute rule to pass, using server-owned
  attributes. Missing attributes deny.
- **Model C (B + deterministic risk):** runs only after B allows, and computes a weighted score from five
  server-owned signals. Below 0.25 gives ALLOW, below 0.50 STEP_UP, below 0.75 LIMIT, otherwise DENY.
  Any missing signal denies. STEP_UP and LIMIT are recommendations and are not enforced. This is a
  heuristic, not AI or ML.

## Observation

On an unmodified clone with `core.autocrlf=true`, .NET build and tests pass, but hash-verified Python
workflows fail:

- `scripts/community/tests`: 23 errors in 89 tests, 22 of them `ValueError: snapshot integrity`.
- `python -m research.acbsd.verify research/acbsd/examples/smoke-v1`: `ValueError: integrity mismatch`.

The repository has no `.gitattributes`. In that clone, 292 files stored with LF were checked out as CRLF,
which changes the bytes that SHA-256 verification reads. To test this cause, I cloned the same commit with
`core.autocrlf=false`: the integrity errors disappeared and `verify` passed.

## Improvement

Add a `.gitattributes` with `* text=auto eol=lf`, plus `AeglysAI.sln -text` to keep that file's committed
CRLF bytes. Add `scripts/community/tests/test_line_endings.py` as a regression test.

**Engineering value:** contributors on Windows get reliable integrity checks, and a failed check is less
likely to be dismissed as a line-ending false alarm. `git add --renormalize .` changed no existing blob, so
hashes and history are unaffected.

## Validation results

| Check | Baseline, `autocrlf=true` | Control, `autocrlf=false` | With fix, `autocrlf=true` |
|---|---|---|---|
| `dotnet restore AeglysAI.sln` | exit 0 | not run | exit 0 |
| `dotnet build AeglysAI.sln --configuration Release --no-restore` | 0 warnings, 0 errors | not run | 0 errors |
| `dotnet test AeglysAI.sln --configuration Release --no-build --no-restore` | 168 of 168 pass | not run | 168 of 168 pass |
| `python -m unittest discover -s scripts/community/tests` | 89 run, 23 errors | 89 run, 1 error | 91 run, 1 error |
| `python scripts/community/check_docs.py` | pass | not run | pass |
| `python -m unittest discover -s research/acbsd/tests` | 19 of 19 pass | not run | 19 of 19 pass |
| `python -m research.acbsd.verify research/acbsd/examples/smoke-v1` | **fails** | pass | pass |

The regression test fails on the baseline commit without `.gitattributes` and passes with it. Validation
used a fresh clone of the pushed fix.

Run check on the baseline build: `GET /health` returned 200 with `{"status":"healthy"}`. Anonymous
`GET /identity` and anonymous `POST /authorization/evaluate/model-c` returned 401.

## Limitations

- **Remaining community test error:** `test_traversal_and_symlink_escape_rejected` fails with
  `WinError 1314` because this account cannot create symlinks. It also occurs in the control clone and is
  not caused by line endings. The community suite therefore still exits 1 on this machine.
- **Security gates:** `scan.py tracked` and `scan.py history` both exit 1, listing paths for owner review.
  All listed paths come from the existing upstream tree or history, and the README already reports
  repository audit findings as not cleared. The staged scan of this submission's files passed.
- **Security gate unit tests:** 21 errors in 27 tests on Windows, where the tests call `python3` and `sh`
  and create symlinks. The repository's scanner installer supports only macOS arm64 and Linux x64.
- **Not run:** the Docker workflow (`./dev up`, `./dev demo`), because the daemon was not running. Linux was
  not tested. `./dev help` did still run under CRLF in Git Bash, so I make no claim that CRLF breaks `./dev`.
- **Authenticated calls:** the run check used anonymous requests only. Authenticated A/B/C decisions are
  covered by the integration tests.
- **Scope:** the fix was tested only on the Windows setup above, and no upstream pull request was opened.

## Evidence location

[Sanitized build, run and test logs](evidence/sarthakviche/). Private paths and machine identifiers are
replaced with placeholders. `security-gates.txt` is condensed and says so at the top.

## AI assistance disclosure

Tool: Claude Code (Claude Opus 5.5). Scope: running the commands, diagnosing the failure, drafting the fix,
the regression test and this document. All results above come from real command runs recorded in the logs.
The participant is responsible for reviewing this work and being able to explain it.
