# Task 14 Report

**Status:** DONE

**Files modified:**
- `docker-compose.yml` — Added Traefik service with Let's Encrypt TLS configuration, switched clipper from `ports` to `expose` + Traefik labels
- `README.md` — Added "HTTPS Deployment" section covering Traefik/Let's Encrypt setup and p12-to-PEM conversion guidance

**Concerns:** None. The docker-compose.yml uses placeholder values (`your-email@example.com`, `clipper.example.com`) that users must replace for their own deployment, as documented in the README.
