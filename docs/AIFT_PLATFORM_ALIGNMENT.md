# OpenMontage — Optional AIFT Universal OS Developer/Application Integration

> **AIFT planning supplement only; not a change to upstream project authority, licensing, current architecture or shipped AIFT functionality.** The proposed platform and visual infographics are under review in [AIFT-OS PR #92](https://github.com/AIFreedomTrustFederation/AIFT-OS/pull/92).

## Current source role

Open-source AI-orchestrated video production platform. The authoring pipeline is defined by AGENT_GUIDE.md and PROJECT_CONTEXT.md; AIFT does not take over its project decision/approval model.

## Possible optional integration

Optional future AIFT desktop media/creative application via a reviewed manifest and scoped file/media permissions. The application must still run its native pipeline with preflight, stages, provider selection, approvals and recording, not bypass the agent guide.

~~~mermaid
flowchart LR
  UPSTREAM["OpenMontage: existing upstream role"] --> ADAPTER["Opt-in, separately reviewed build/app adapter"]
  ADAPTER -. "only after real tests" .-> AIFT["AIFT development or creative workspace"]
  LIC["License, provenance and author approvals"] --> ADAPTER
  CI["Exact source and target verification"] --> ADAPTER
~~~

## Verifiable acceptance

1. Read existing project README, contribution/agent guide and source license before any implementation.
2. Document any future versioned manifest and environment-specific limitations.
3. Prove Actual pipeline preflight, capability discovery, provider/license checks, source-linked output, explicit paid-generation and publishing approval, and target-specific tested app launch.
4. Keep test/build/publishing and authorization evidence with exact source/artifact SHAs.
5. If not actually installed or executed, label this integration UNVERIFIED and avoid advertising bundled software or a supported hardware OS.

## Non-negotiable boundary

No paid generation, cloud publishing, asset generation, pipeline switch or external provider call is authorized by a documentation note. Preserve upstream licenses and authoritative guide. No production deployment, firmware flashing, boot entry changes, hidden telemetry, phone/robot action, security-policy revision or credential handling is part of this document.

See [AIFT-OS draft architecture](https://github.com/AIFreedomTrustFederation/AIFT-OS/pull/92).
