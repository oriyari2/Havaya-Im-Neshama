EXPECTED_TABLES = [
    "users",
    "customers",
    "customer_contacts",
    "instructors",
    "activities",
    "activity_images",
    "activity_instruction_notes",
    "inventory_items",
    "activity_equipment_requirements",
    "bookings",
    "booking_activities",
    "booking_instructors",
    "booking_equipment_items",
    "booking_price_components",
]


CREATE_EXTENSION_SQL = "CREATE EXTENSION IF NOT EXISTS pgcrypto;"


CREATE_TABLE_SQL = [
    """
    CREATE TABLE IF NOT EXISTS customers (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        name text NOT NULL,
        customer_type text,
        city text,
        address text,
        phone text,
        email text,
        notes text,
        is_active boolean NOT NULL DEFAULT true,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS customer_contacts (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        customer_id uuid NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
        full_name text NOT NULL,
        role_title text,
        phone text,
        email text,
        is_primary boolean NOT NULL DEFAULT false,
        notes text,
        is_active boolean NOT NULL DEFAULT true,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS instructors (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        full_name text NOT NULL,
        phone text,
        email text,
        city text,
        notes text,
        is_active boolean NOT NULL DEFAULT true,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS users (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        email text NOT NULL UNIQUE,
        password_hash text NOT NULL,
        role text NOT NULL CHECK (role IN ('manager', 'instructor', 'customer')),
        is_active boolean NOT NULL DEFAULT true,
        customer_id uuid REFERENCES customers(id),
        instructor_id uuid REFERENCES instructors(id),
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS activities (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        name text NOT NULL,
        description text,
        target_audience text,
        duration_minutes integer,
        recommended_capacity integer,
        pricing_rule text,
        required_equipment text,
        preparation_notes text,
        season text,
        tags text,
        default_duration_minutes integer,
        min_participants integer,
        max_participants integer,
        base_price numeric,
        price_notes text,
        default_setup_minutes integer,
        default_cleanup_minutes integer,
        is_active boolean NOT NULL DEFAULT true,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS activity_instruction_notes (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        activity_id uuid NOT NULL REFERENCES activities(id) ON DELETE CASCADE,
        title text NOT NULL,
        body text NOT NULL,
        sort_order integer NOT NULL DEFAULT 0,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS activity_images (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        activity_id uuid NOT NULL REFERENCES activities(id) ON DELETE CASCADE,
        public_id text NOT NULL,
        secure_url text NOT NULL,
        original_filename text,
        content_type text,
        width integer,
        height integer,
        bytes integer,
        is_primary boolean NOT NULL DEFAULT true,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS inventory_items (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        name text NOT NULL,
        category text,
        unit text,
        quantity_total integer NOT NULL DEFAULT 0,
        quantity_available integer NOT NULL DEFAULT 0,
        storage_location text,
        needs_charging boolean NOT NULL DEFAULT false,
        notes text,
        is_active boolean NOT NULL DEFAULT true,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS activity_equipment_requirements (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        activity_id uuid NOT NULL REFERENCES activities(id) ON DELETE CASCADE,
        inventory_item_id uuid NOT NULL REFERENCES inventory_items(id),
        quantity_required integer NOT NULL DEFAULT 1,
        quantity_per_participant numeric,
        is_optional boolean NOT NULL DEFAULT false,
        notes text,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS bookings (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        customer_id uuid NOT NULL REFERENCES customers(id),
        primary_contact_id uuid REFERENCES customer_contacts(id),
        event_title text,
        event_date timestamptz,
        location_name text,
        location_address text,
        city text,
        participants_count integer,
        audience_type text,
        status text NOT NULL DEFAULT 'draft',
        internal_notes text,
        customer_notes text,
        requires_vehicle boolean NOT NULL DEFAULT false,
        vehicle_notes text,
        loading_notes text,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS booking_activities (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        booking_id uuid NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
        activity_id uuid NOT NULL REFERENCES activities(id),
        start_time timestamptz,
        duration_minutes integer,
        participants_count integer,
        location_detail text,
        sort_order integer NOT NULL DEFAULT 0,
        notes text,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS booking_instructors (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        booking_activity_id uuid NOT NULL REFERENCES booking_activities(id) ON DELETE CASCADE,
        instructor_id uuid NOT NULL REFERENCES instructors(id),
        role text,
        payment_status text NOT NULL DEFAULT 'not_relevant',
        notes text,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS booking_equipment_items (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        booking_id uuid NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
        inventory_item_id uuid NOT NULL REFERENCES inventory_items(id),
        quantity_planned integer NOT NULL DEFAULT 1,
        quantity_packed integer,
        quantity_returned integer,
        status text NOT NULL DEFAULT 'planned',
        notes text,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS booking_price_components (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        booking_id uuid NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
        component_type text NOT NULL,
        description text NOT NULL,
        quantity numeric NOT NULL DEFAULT 1,
        unit_price numeric NOT NULL DEFAULT 0,
        total_price numeric NOT NULL DEFAULT 0,
        sort_order integer NOT NULL DEFAULT 0,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
    );
    """,
]


ALTER_TABLE_SQL = [
    "ALTER TABLE activities ADD COLUMN IF NOT EXISTS target_audience text;",
    "ALTER TABLE activities ADD COLUMN IF NOT EXISTS duration_minutes integer;",
    "ALTER TABLE activities ADD COLUMN IF NOT EXISTS recommended_capacity integer;",
    "ALTER TABLE activities ADD COLUMN IF NOT EXISTS pricing_rule text;",
    "ALTER TABLE activities ADD COLUMN IF NOT EXISTS required_equipment text;",
    "ALTER TABLE activities ADD COLUMN IF NOT EXISTS preparation_notes text;",
    "ALTER TABLE activities ADD COLUMN IF NOT EXISTS season text;",
    "ALTER TABLE activities ADD COLUMN IF NOT EXISTS tags text;",
]


CREATE_INDEX_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",
    "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);",
    "CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(name);",
    "CREATE INDEX IF NOT EXISTS idx_customers_city ON customers(city);",
    "CREATE INDEX IF NOT EXISTS idx_customer_contacts_customer_id ON customer_contacts(customer_id);",
    "CREATE INDEX IF NOT EXISTS idx_instructors_full_name ON instructors(full_name);",
    "CREATE INDEX IF NOT EXISTS idx_activities_name ON activities(name);",
    "CREATE INDEX IF NOT EXISTS idx_activities_is_active ON activities(is_active);",
    "CREATE INDEX IF NOT EXISTS idx_activities_season ON activities(season);",
    "CREATE INDEX IF NOT EXISTS idx_activity_images_activity_id ON activity_images(activity_id);",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_activity_images_one_primary ON activity_images(activity_id) WHERE is_primary = true;",
    "CREATE INDEX IF NOT EXISTS idx_bookings_customer_id ON bookings(customer_id);",
    "CREATE INDEX IF NOT EXISTS idx_bookings_event_date ON bookings(event_date);",
    "CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings(status);",
    "CREATE INDEX IF NOT EXISTS idx_booking_activities_booking_id ON booking_activities(booking_id);",
    "CREATE INDEX IF NOT EXISTS idx_booking_instructors_booking_activity_id ON booking_instructors(booking_activity_id);",
    "CREATE INDEX IF NOT EXISTS idx_booking_instructors_instructor_id ON booking_instructors(instructor_id);",
    "CREATE INDEX IF NOT EXISTS idx_booking_equipment_items_booking_id ON booking_equipment_items(booking_id);",
    "CREATE INDEX IF NOT EXISTS idx_booking_price_components_booking_id ON booking_price_components(booking_id);",
]
