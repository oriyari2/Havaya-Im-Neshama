# PIV 26 — OpenRouteService Travel Gateway

## Purpose

This task adds a domain-specific external provider for operational event
planning. A Manager can calculate an estimated car-driving distance and duration
from the configured business base address to the selected Booking location.

## Course requirements advanced

- Gateway pattern for external services.
- Calling a service related to the product domain and receiving processed data.
- FastAPI as the only backend boundary used by the Desktop client.
- MVP separation between Desktop View, Presenter and service adapter.
- Server-side authorization.

## Architecture

```text
Manager Booking Details
  -> BookingsView emits travel_estimate_requested
    -> BookingsPresenter schedules background operation
      -> BookingService calls FastAPI
        -> GET /bookings/{booking_id}/travel-estimate
          -> booking visibility/query boundary
          -> BookingTravelService
            -> RouteGateway protocol
              -> OpenRouteServiceGateway
                -> Geocoding API
                -> Directions API (driving-car)
```

Only the infrastructure adapter imports `httpx` for OpenRouteService calls. The
application service depends on `RouteGateway`, not on the provider. The Desktop
never receives the provider API key and never calls OpenRouteService directly.

## Returned application data

- resolved origin and destination labels;
- distance in kilometres;
- estimated duration in minutes;
- provider identifier;
- explicit `uses_live_traffic=false` indicator.

The duration is a routing estimate and is not presented as real-time traffic
information.

## Configuration

Add the following values to the local, ignored `backend/.env`:

```env
OPENROUTESERVICE_API_KEY=replace_with_real_key
BUSINESS_BASE_ADDRESS="לנדרס 16, רמת גן, ישראל"
OPENROUTESERVICE_BASE_URL=https://api.openrouteservice.org
OPENROUTESERVICE_TIMEOUT_SECONDS=15
OPENROUTESERVICE_COUNTRY_CODE=ISR
```

`backend/.env.example` and `backend/.env.route.example` contain safe templates.
The real `.env` remains excluded from Git.

## Files added

- `backend/app/application/gateways/route_gateway.py`
- `backend/app/application/services/booking_travel_service.py`
- `backend/app/infrastructure/gateways/openrouteservice_gateway.py`
- `backend/app/routers/travel.py`
- `backend/app/schemas/travel.py`
- `backend/tests/test_route_gateway.py`
- `desktop_client/tests/test_travel_gateway_ui.py`
- `backend/.env.route.example`

## Files updated

- backend composition/environment/provider files;
- Booking Desktop service, Presenter, View and registration;
- `.env.example`;
- architecture, feature, roadmap and traceability documentation.

## Authorization and failure behaviour

- `manager` and `instructor` may call the travel-estimate endpoint for bookings they are allowed to view.
- Manager calculations start from `BUSINESS_BASE_ADDRESS`; instructor calculations start from the city saved in the instructor profile.
- Missing booking location returns `422`.
- Missing/invalid provider configuration returns `503`.
- Provider timeout/unavailability returns `502`.
- The provider key is never returned in an error or response.

## Validation

Run:

```powershell
python -m compileall backend desktop_client rag
python -m unittest backend.tests.test_route_gateway -v
python -m unittest desktop_client.tests.test_travel_gateway_ui -v
python -m unittest discover -s backend/tests -p "test_*.py" -v
```

The provider adapter tests use an `httpx.MockTransport`; they do not consume the
real API quota. A final manual check should use a real booking with a complete
venue/street and city.

## Manual acceptance flow

1. Start the backend with the local OpenRouteService values in `backend/.env`.
2. Sign in as Manager, open a Booking and calculate from the configured business address.
3. Sign in as Instructor whose profile contains a city.
4. Open an assigned event or a visible open event.
5. Click `חשב מרחק מהעיר שלי`.
6. Confirm that the screen displays distance, duration and resolved addresses.
7. Confirm that Customers do not see the calculation panel.

## External provider references

- Geocoder endpoint: https://giscience.github.io/openrouteservice/api-reference/endpoints/geocoder/
- API playground/Directions: https://openrouteservice.org/dev/
- Standard free plan: https://openrouteservice.org/plans/
