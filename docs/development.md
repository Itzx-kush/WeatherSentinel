# Development

## Windows workflow

```powershell
cd D:\WeatherSentinel
.\scripts\setup.ps1
.\scripts\test.ps1
.\scripts\replay-example.ps1 -Speed 0
```

Part 1 is a Python library and CLI, not an HTTP service. Consequently there is no backend server startup or frontend build command. Add those only when real API and product capabilities are implemented.

## Principles

- Preserve raw observations and provenance.
- Add tests with every behavior.
- Use past-only feature baselines.
- Treat quality flags as evidence, not labels.
- Never report benchmark metrics without traceable ground truth.
- Keep future-part modules empty rather than inventing placeholder success behavior.
