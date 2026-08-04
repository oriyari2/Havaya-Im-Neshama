# Task 26 — OpenRouteService Travel Gateway

## Goal

Add a second domain-specific external service integration that calculates the
estimated driving distance and duration to a booking location. Managers use
the configured business base address; instructors use the city saved in their profile.

## Scope

- Add an application-owned `RouteGateway` protocol.
- Implement `OpenRouteServiceGateway` in infrastructure.
- Geocode the origin and destination addresses.
- Request a `driving-car` route and translate provider data into application data.
- Add a role-safe manager/instructor booking travel-estimate endpoint.
- Add the travel panel to Manager and Instructor Booking Details.
- Keep the API key on the backend only.
- Add tests and PIV documentation.

## Non-goals

- No route persistence or database migration.
- No live-traffic promise.
- No changes to booking Event Sourcing/CQRS.
- No direct external-service access from the Desktop client.
