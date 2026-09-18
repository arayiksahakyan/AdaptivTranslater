# Future commercial architecture — planning only

No services in this document are implemented or required by the local MVP.

```text
Desktop (local capture + OCR + optional local translation)
   |
   | HTTPS: recognized text, only with explicit user choice
   v
Backend API
   +-- Authentication
   +-- Subscription / license validation
   +-- Rate limiting and abuse protection
   +-- Provider API key protection
   +-- Minimal usage accounting
              |
              v
       Translation / AI providers
```

Possible models: Free/Pro plans, subscriptions, lifetime desktop license, optional
AI credits, cloud translation, contextual translation, and fully local/private
translation. Commercial choices require validation; they are not dependencies of
the prototype. Desktop code calls TranslationProvider, preserving an offline path.

Future concerns: explicit consent for network text transfer, retention/deletion
policies, encrypted transport, server-side secrets, quotas, transparent cost
indicators, timeout/retry budgets, code signing, secure updates, license reviews of
GUI/OCR/model dependencies, and optional telemetry with privacy controls. Do not
ship backend credentials inside a desktop binary. Never upload screenshots by
default. Context/history would require a separate opt-in and retention design.
