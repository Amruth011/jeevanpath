from .database import connection


TEST_PATIENT = {
    "id": "test-patient-001",
    "name": "Test Patient",
    "case_id": "TEST-0001",
    "language": "English",
    "status": "Active care",
    "risk_level": "low",
    "age": 64,
    "caregiver": "Test caregiver",
    "phone": "Not collected",
    "consent": "Development test consent",
    "follow_up": "Development test record",
}

TEST_ACTIVITIES = [
    ("test-activity-001", "Voice check-in completed", "2026-11-01T10:42:00+00:00", "teal"),
    ("test-activity-002", "Follow-up reminder sent", "2026-10-31T10:00:00+00:00", "amber"),
]


def seed_test_data() -> None:
    with connection() as db:
        db.execute("DELETE FROM activities WHERE synthetic = 1")
        db.execute("DELETE FROM patients WHERE synthetic = 1 AND test_record = 1")
        db.execute(
            """
            INSERT OR REPLACE INTO patients
            (id, name, case_id, language, status, risk_level, age, caregiver, phone,
             consent, follow_up, synthetic, test_record)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1)
            """,
            tuple(TEST_PATIENT.values()),
        )
        db.executemany(
            """
            INSERT OR REPLACE INTO activities
            (id, patient_id, text, occurred_at, tone, synthetic)
            VALUES (?, ?, ?, ?, ?, 1)
            """,
            [(activity_id, TEST_PATIENT["id"], text, occurred_at, tone) for activity_id, text, occurred_at, tone in TEST_ACTIVITIES],
        )


if __name__ == "__main__":
    seed_test_data()
    print("Seeded one synthetic development test patient.")
