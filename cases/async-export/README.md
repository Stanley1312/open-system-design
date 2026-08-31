# Async Export — System Design Case

This case evolves a large-file export flow from a blocking HTTP request into a
durable asynchronous system. Each version introduces one major architectural
step while keeping the request flow runnable and observable.

## Learning path

1. Start with [`v1/`](v1/) to compare a synchronous export with an in-memory
   asynchronous job and client polling.
2. Continue with [`v2/`](v2/) to persist jobs in PostgreSQL and let multiple
   workers claim work safely.
3. Continue with [`v3/`](v3/) for the next reliability step.
4. Read the [case-wide architecture note](docs/async_large_file_export_api_design_en.md)
   for the complete production-oriented model.

## Repository layout

```text
async-export/
├── README.md       # Case overview and version map
├── docs/           # Notes that apply to the whole case
├── v1/             # HTTP interaction and polling
├── v2/             # PostgreSQL queue and worker pool
└── v3/             # Next reliability step
```

Each version owns its challenge, runnable code, and version-specific design
notes. Case-wide docs describe the destination architecture rather than the
implementation of one version.
