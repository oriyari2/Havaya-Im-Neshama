-- Instructor self-nomination workflow for booking activities.
-- Additive and idempotent: safe to run on an existing project database.

CREATE TABLE IF NOT EXISTS booking_assignment_requests (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_activity_id uuid NOT NULL REFERENCES booking_activities(id) ON DELETE CASCADE,
    instructor_id uuid NOT NULL REFERENCES instructors(id),
    status text NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED')),
    requested_at timestamptz NOT NULL DEFAULT now(),
    decided_at timestamptz,
    decided_by uuid REFERENCES users(id),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (booking_activity_id, instructor_id)
);

CREATE INDEX IF NOT EXISTS idx_booking_assignment_requests_activity_status
    ON booking_assignment_requests(booking_activity_id, status);
CREATE INDEX IF NOT EXISTS idx_booking_assignment_requests_instructor_status
    ON booking_assignment_requests(instructor_id, status);
