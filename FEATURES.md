
## Booking travel estimate Gateway

Managers can calculate an estimated driving distance and duration from the
configured business base address to a Booking location. The Desktop calls a
manager-only FastAPI endpoint; the backend resolves both addresses and calls
OpenRouteService through the application-owned `RouteGateway` abstraction. The
API key remains server-side, results are not persisted, and the UI explicitly
notes that the estimate does not include live traffic.

