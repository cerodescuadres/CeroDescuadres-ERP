---
name: Replit Streamlit preview routing
description: External port mapping for Streamlit workflows when local health checks pass but the web preview returns 502.
---

For Streamlit apps in a standalone Replit workflow, `waitForPort` and binding to `0.0.0.0` may not be enough for Preview routing. Declare a `.replit` `[[ports]]` mapping from the app's local port (commonly 5000) to external port 80 so the app is served at the workspace root. Use Replit's validated `.replit` replacement flow rather than editing the file directly.

**Why:** A Streamlit server returned HTTP 200 locally while the Replit preview proxy returned `502 repl unreachable` until an external port mapping was added.

**How to apply:** For this failure pattern, check the external root URL after adding the mapping. If the mapping disappears after workflow configuration, reapply it afterward and confirm it remains in `.replit`.
