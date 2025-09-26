import unittest

from api import app, appointments, extract_and_validate_data_fields, validate_category_types, category_types


class TestApi(unittest.TestCase):

    def setUp(self):
        appointments.clear()
        self.client = app.test_client()

    def test_list_appointments_empty(self):
        response = self.client.get("/appointments")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, [])

    def test_list_appointments_with_entries(self):
        self.client.post("/appointments",
                         json = {"title": "Meeting", "start": "2025-09-26 10:00", "end": "2025-09-26 12:00",
                                 "category": "general"})
        self.client.post("/appointments",
                         json = {"title": "Meeting2", "start": "2025-09-26 13:00", "end": "2025-09-26 14:00",
                                 "category": "general"})

        response = self.client.get("/appointments")
        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(appointments), 2)

    def test_create_appointment(self):
        response = self.client.post("/appointments",
                                    json = {"title": "Meeting", "start": "2025-09-26 10:00",
                                            "end": "2025-09-26 12:00", "category": "general"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(appointments[0]["title"], "Meeting")
        self.assertEqual(appointments[0]["start"], "2025-09-26 10:00")
        self.assertEqual(appointments[0]["end"], "2025-09-26 12:00")
        self.assertEqual(appointments[0]["category"], "general")

    def test_create_overlapping_appointment(self):
        self.client.post("/appointments",
                         json = {"title": "Meeting", "start": "2025-09-26 10:00", "end": "2025-09-26 12:00",
                                 "category": "general"})
        response = self.client.post("/appointments",
                                    json = {"title": "Meeting2", "start": "2025-09-26 09:00", "end": "2025-09-26 13:00",
                                            "category": "general"})

        self.assertEqual(response.status_code, 409)
        self.assertIn("error", response.json)
        self.assertEqual(response.json["error"], "Overlapping appointment")

    def test_update_appointment(self):
        self.client.post("/appointments",
                         json = {"title": "Meeting", "start": "2025-09-26 10:00", "end": "2025-09-26 12:00",
                                 "category": "general"})
        appt_id = appointments[0]["id"]
        response = self.client.put(f"/appointments/{appt_id}",
                                   json = {"title": "Sommerfest Meeting", "start": "2025-09-26 13:00",
                                           "end": "2025-09-26 15:00", "category": "general"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(appointments[0]["title"], "Sommerfest Meeting")
        self.assertEqual(appointments[0]["start"], "2025-09-26 13:00")
        self.assertEqual(appointments[0]["end"], "2025-09-26 15:00")
        self.assertEqual(appointments[0]["category"], "general")

    def test_update_overlapping_appointment(self):
        self.client.post("/appointments",
                         json = {"title": "Meeting", "start": "2025-09-26 10:00", "end": "2025-09-26 12:00",
                                 "category": "general"})
        self.client.post("/appointments",
                         json = {"title": "Meeting2", "start": "2025-09-26 13:00", "end": "2025-09-26 15:00",
                                 "category": "general"})
        response = self.client.put("/appointments/2",
                                   json = {"title": "Meeting2", "start": "2025-09-26 11:00", "end": "2025-09-26 14:00",
                                           "category": "general"})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json["error"], "Overlapping appointment")

    def test_update_overlapping_appointment_id_error(self):
        self.client.post("/appointments",
                         json = {"title": "Meeting", "start": "2025-09-26 10:00", "end": "2025-09-26 12:00",
                                 "category": "general"})
        response = self.client.put("/appointments/2",
                                   json = {"title": "Meeting", "start": "2025-09-26 13:00", "end": "2025-09-26 14:00",
                                           "category": "general"})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["error"], "Appointment not found")

    def test_delete_appointment(self):
        self.client.post("/appointments",
                         json = {"title": "Meeting", "start": "2025-09-26 10:00", "end": "2025-09-26 12:00",
                                 "category": "general"})
        appt_id = appointments[0]["id"]
        response = self.client.delete(f"/appointments/{appt_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "deleted")
        self.assertEqual(len(appointments), 0)

    def test_delete_appointment_not_found(self):
        self.client.post("/appointments",
                         json = {"title": "Meeting", "start": "2025-09-26 10:00", "end": "2025-09-26 12:00",
                                 "category": "general"})
        response = self.client.delete("/appointments/8")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["error"], "Appointment not found")
        self.assertEqual(len(appointments), 1)

    def test_invalid_appointments(self):
        categorys = {"title", "start", "end", "category"}
        fehlerhafte_termine = [
            {},
            {"title": "1"},
            {"title": "1", "end": "1"},
            {"start": "1", "end": "1"},
            {"title": "1", "start": "1"},
            {"title": "1", "start": "1", "end": "1", "geheim": "1"}
        ]

        for json_data in fehlerhafte_termine:
            self.assertNotEqual(categorys, set(json_data.keys()))

    def test_valid_appointment(self):
        json_data = {"title": "Meeting", "start": "2025-09-26 10:00", "end": "2025-09-26 12:00", "category": "general"}
        self.assertEqual({"title", "start", "end", "category"}, set(json_data.keys()))

    def test_extract_fields_with_valid_appointment(self):
        json_data = {"title": "Meeting", "start": "2025-09-26 10:00", "end": "2025-09-26 12:00", "category": "general"}
        result = extract_and_validate_data_fields(json_data)
        self.assertEqual(result, ("Meeting", "2025-09-26 10:00", "2025-09-26 12:00", "general"))

    def test_extract_fields_with_invalid_appointment(self):
        with self.assertRaises(ValueError) as contextManager:
            extract_and_validate_data_fields({})

        self.assertEqual(contextManager.exception.args[0], "Invalid appointment: wrong or missing fields")

    def test_check_appointment_list(self):
        self.assertEqual(len(appointments), 0)

        response = self.client.post("/appointments",
                                    json = {"title": "Meeting", "start": "2025-09-26 10:00", "end": "2025-09-26 12:00",
                                            "category": "general"})
        self.assertEqual(response.status_code, 201)

        self.assertEqual(len(appointments), 1)
        self.assertEqual(appointments[0]["title"], "Meeting")
        self.assertEqual(appointments[0]["start"], "2025-09-26 10:00")
        self.assertEqual(appointments[0]["end"], "2025-09-26 12:00")

    def test_list_appointments_with_category_filter(self):
        appointments.append({"title": "Arzt", "start": "13:00", "end": "14:00", "category": "health"})
        appointments.append({"title": "Meeting", "start": "15:00", "end": "16:00", "category": "work"})
        appointments.append({"title": "Zahnarzt", "start": "18:00", "end": "18:30", "category": "health"})

        response = self.client.get("/appointments?category=health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 2)
        self.assertEqual(response.json[0]["category"], "health")
        self.assertEqual(response.json[1]["category"], "health")

    def test_list_appointments_with_invalid_category(self):
        appointments.append({"title": "Meeting", "start": "10:00", "end": "12:00", "category": "doesnotexist"})

        response = self.client.get("/appointments?category=doesnotexist")
        self.assertIn("error", response.json)
        self.assertEqual(response.json["error"],
                         "Invalid category. Must be one of ['health', 'general', 'work', 'social']")

    def test_no_valid_category_type(self):
        category = {"category": "abc"}
        with self.assertRaises(ValueError) as contextManager:
            validate_category_types(category)
        self.assertEqual(contextManager.exception.args[0], f"Invalid category. Must be one of {category_types}")

    def test_no_appointments_for_category(self):
        appointments.append({"title": "Meeting", "start": "10:00", "end": "12:00", "category": "general"})

        response = self.client.get("/appointments?category=health")
        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.json)
        self.assertEqual(response.json["error"], "No appointments found for this category")
