from .database import connection


TEST_PATIENTS = [
    {
        "id": "test-patient-001",
        "name": "TEST Patient One",
        "case_id": "TEST-0001",
        "language": "English",
        "status": "Active care",
        "risk_level": "low",
        "age": 64,
        "caregiver": "TEST Caregiver One",
        "phone": "Not collected",
        "consent": "Development test consent",
        "follow_up": "Development test record",
    },
    {
        "id": "test-patient-002",
        "name": "TEST Patient Two",
        "case_id": "TEST-0002",
        "language": "English",
        "status": "Active care",
        "risk_level": "medium",
        "age": 58,
        "caregiver": "TEST Caregiver Two",
        "phone": "Not collected",
        "consent": "Development test consent",
        "follow_up": "Development test record",
    },
]

TEST_ACTIVITIES = [
    ("test-activity-001", TEST_PATIENTS[0]["id"], "Voice check-in completed", "2026-11-01T10:42:00+00:00", "teal"),
    ("test-activity-002", TEST_PATIENTS[0]["id"], "Follow-up reminder sent", "2026-10-31T10:00:00+00:00", "amber"),
    ("test-activity-003", TEST_PATIENTS[1]["id"], "Care plan acknowledged", "2026-11-01T09:30:00+00:00", "green"),
]


def _insert_test_data(db) -> None:
    for patient in TEST_PATIENTS:
        db.execute(
            """
            INSERT OR IGNORE INTO patients
            (id, name, case_id, language, status, risk_level, age, caregiver, phone,
             consent, follow_up, synthetic, test_record)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1)
            """,
            tuple(patient.values()),
        )
    db.executemany(
        """
        INSERT OR IGNORE INTO activities
        (id, patient_id, text, occurred_at, tone, synthetic)
        VALUES (?, ?, ?, ?, ?, 1)
        """,
        TEST_ACTIVITIES,
    )


def seed_demo_data_if_missing() -> None:
    with connection() as db:
        existing = db.execute(
            "SELECT COUNT(*) FROM patients WHERE synthetic = 1 AND test_record = 1"
        ).fetchone()[0]
        if existing < len(TEST_PATIENTS):
            _insert_test_data(db)


def seed_test_data() -> None:
    """Explicitly replace synthetic local test data with the two demo patients."""
    with connection() as db:
        db.execute("DELETE FROM activities WHERE synthetic = 1")
        db.execute("DELETE FROM patients WHERE synthetic = 1 AND test_record = 1")
        _insert_test_data(db)


if __name__ == "__main__":
    seed_test_data()
    print("Seeded two synthetic development test patients.")
