# Integration policy

Before adopting an external repository or model:

- Confirm the canonical upstream repository and current maintenance state.
- Read the exact license and note model-weight / dataset terms separately.
- Check Python, CUDA, operating-system and hardware requirements.
- Identify install size, runtime memory, network downloads and external services.
- Prefer adapters and optional extras over copying large upstream codebases.
- Run unit tests and a small end-to-end smoke test on a feature branch.
- Record source URL, pinned version/commit, license, changes and test evidence.
- Revert the integration if it breaks baseline tests, violates license terms or exceeds the supported device budget.

No third-party repository is approved for integration merely because it appears in a candidate list.
