from __future__ import annotations

from uuid import UUID


ACTIVITY_IMAGE_COLUMNS = (
    "id, activity_id, public_id, secure_url, original_filename, content_type, "
    "width, height, bytes, is_primary, created_at, updated_at"
)


def list_activity_images(cur, activity_id: UUID) -> list[dict]:
    cur.execute(
        f"""
        SELECT {ACTIVITY_IMAGE_COLUMNS}
        FROM activity_images
        WHERE activity_id = %s
        ORDER BY is_primary DESC, created_at ASC, id ASC;
        """,
        (activity_id,),
    )
    return list(cur.fetchall())


def get_activity_image(cur, activity_id: UUID, image_id: UUID) -> dict | None:
    cur.execute(
        f"""
        SELECT {ACTIVITY_IMAGE_COLUMNS}
        FROM activity_images
        WHERE activity_id = %s AND id = %s;
        """,
        (activity_id, image_id),
    )
    return cur.fetchone()


def create_activity_image(cur, data: dict) -> dict:
    if data.get("is_primary", True):
        cur.execute(
            "UPDATE activity_images SET is_primary = false, updated_at = now() WHERE activity_id = %s;",
            (data["activity_id"],),
        )

    cur.execute(
        f"""
        INSERT INTO activity_images (
            activity_id, public_id, secure_url, original_filename, content_type,
            width, height, bytes, is_primary
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING {ACTIVITY_IMAGE_COLUMNS};
        """,
        (
            data["activity_id"],
            data["public_id"],
            data["secure_url"],
            data["original_filename"],
            data["content_type"],
            data["width"],
            data["height"],
            data["bytes"],
            data.get("is_primary", True),
        ),
    )
    return cur.fetchone()


def delete_activity_image(cur, activity_id: UUID, image_id: UUID) -> dict | None:
    cur.execute(
        f"""
        DELETE FROM activity_images
        WHERE activity_id = %s AND id = %s
        RETURNING {ACTIVITY_IMAGE_COLUMNS};
        """,
        (activity_id, image_id),
    )
    return cur.fetchone()

