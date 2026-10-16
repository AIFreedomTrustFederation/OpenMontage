# Federation Role: OpenMontage

## Layer

`applied-business`

## Role

federated repository participating in the AIFT operating system

## Operating Principle

This repository is part of the AI Freedom Trust Federation operating system. It remains sovereign in its own repo while participating in the shared federation control plane.

## Control Plane

Top-level workspace:

```bash
/data/data/com.termux/files/home/AIFT
```

Primary command:

```bash
/data/data/com.termux/files/home/AIFT/aift-os.sh
```

## Standard Commands

Status:

```bash
git status --short
```

Pull:

```bash
git pull --ff-only
```

Verify (requires Python test dependencies and Make, from the repository root):

```bash
make test-contracts
```

This command runs the contract-test suite and returns a nonzero exit code on test failures. It does not validate end-to-end rendering, paid provider availability, or optional HyperFrames runtime readiness. Run `make hyperframes-doctor` separately when applicable.

## Federation Metadata

This repo declares its federation role in:

```bash
aift.repo.json
```

The workspace-level federation manifest is generated at:

```bash
/data/data/com.termux/files/home/AIFT/manifests/workspace.json
```
