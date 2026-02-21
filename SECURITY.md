# Veriqko Security & Compliance Architecture

This document outlines the security, privacy, and compliance controls implemented in the Veriqko platform to meet ISO 27001, GDPR, and SOC 2 Type II requirements.

## Data Privacy & GDPR

### Data Minimization & PII Extrication
Veriqko processes hardware diagnostic data. We explicitly integrate with Picea Services to systematically wipe and verify the destruction of any Personally Identifiable Information (PII) residing on user devices during the refurbishment flow. 
- **Erase Confirmation:** The system enforces a strict state-machine guard that prevents devices from progressing beyond the `RESET` phase without an explicit API payload or manual bypass verifying data erasure.
- **Erase Certificates:** Picea Data Erasure Certificates are retrieved, structurally mapped, and injected definitively into the generated PDF Verification Reports, providing an immutable audit trail of data destruction.

### Right to be Forgotten (GDPR Article 17)
Users and technicians can invoke their Right to be Forgotten via the `DELETE /users/me/forget` API endpoint. This endpoint fully anonymizes user PII (names, emails) with scrambled local replacements and marks the record as inactive while preserving relational integrity for historical SOC 2 audit logs.

## Audit Trails & SOC 2 Context

### State Transition Logging
All job progressions (e.g. `INTAKE` -> `RESET` -> `QC`) are rigidly tracked in the `JobHistory` table. This satisfies SOC 2 requirements for change management and access control tracking:
- **Timestamping:** Every state transition is recorded using strict timezone-aware (`timezone.utc`) timestamps.
- **Attribution:** Transitions must be tied to a valid `user_id`.
- **System Traceability:** The `JobStateMachine` handles validations, guarding against unauthorized transitions in the refurbishment process.

### Logical Access Controls
- Robust JWT-based authentication via OAuth2 tokens.
- Immediate revocation scenarios handled via short-lived access tokens and refresh mechanisms.

## ISO 27001 Resilience & Consistency

### Zero-Downtime Deployment
The infrastructure pipeline utilizes a Blue/Green deployment strategy (`update.sh`) ensuring continuous availability (Availability control, ISO 27001).
- Dependency compilation and virtual environment setups transpire in an isolated folder.
- Only upon complete readiness are the live folders atomically swapped.

### Infrastructure Integrity
Server deployment configurations utilize deterministic SSH authentication loops, robust system dependency lockdowns (`apt-get` wait loops), and restricted root context isolation. All deployments default to establishing internal communication via constrained configurations and explicit UFW lockdown logic.
