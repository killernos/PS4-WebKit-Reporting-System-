# Security and Privacy

This project collects diagnostic data. Implementers are responsible for protecting testers and their data.

## Do not require

- Real names
- PSN usernames
- Email addresses
- Passwords or tokens
- Console serial numbers
- MAC addresses
- Precise location

Use random session/report IDs.

## Server guidance

Production deployments should use HTTPS, explicit CORS origins, body-size limits, rate limiting, schema validation, safe storage permissions, log rotation, and a documented retention policy.

Never trust client-supplied filenames or paths. Do not execute submitted report contents.

## Reporting security issues

Use the repository's private security-reporting feature if enabled. Avoid posting secrets, private tester data, or exploitable infrastructure details in public issues.
