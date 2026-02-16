# Security & Compliance Policy

## Overview
This document outlines the security practices and compliance posture for the Veriqko platform. We are committed to maintaining high standards of data protection and security, aligning with ISO 27001, GDPR, and SOC 2 Type 2 frameworks.

## 🔒 Security Practices

### 1. Data Protection (GDPR)
- **Encryption at Rest**: All database volumes and sensitive backups are encrypted using AES-256.
- **Encryption in Transit**: TLS 1.3 is enforced for all external communications via Nginx.
- **Data Minimization**: We only collect the minimum amount of personal data required for the service to function.
- **Access Control**: Role-Based Access Control (RBAC) is implemented throughout the platform.

### 2. Infrastructure Security (ISO 27001)
- **Deployment**: Secure deployment scripts (Proxmox/Ubuntu) automate environment hardening.
- **SSH Access**: Key-based authentication is required; password-based root SSH is disabled by default.
- **Updates**: Modular update scripts ensure timely patching of system and application dependencies.
- **Logging**: Comprehensive auditing of API access and system events.

### 3. Operational Security (SOC 2)
- **Availability**: Systemd services with auto-restart ensure high service availability.
- **Integrity**: Database migrations are version-controlled and tested.
- **Confidentiality**: JWT-based authentication with high-entropy secrets protects user sessions.

## 🛡️ Reporting a Vulnerability
If you discover a security vulnerability, please do NOT create a public issue. Instead, report it to the security team:
- **Email**: security@veriqko.com
- **PGP Key**: [Add Link/Fingerprint]

Please include a detailed description of the vulnerability and steps to reproduce.

## ⚖️ Compliance Status
- **ISO 27001**: Guided by best practices in infrastructure management.
- **GDPR**: Data subject rights and privacy-by-design principles implemented.
- **SOC 2 Type 2**: Controls in place for Security, Availability, and Confidentiality.

---
*Last Updated: 2026-02-16*
