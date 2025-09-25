import unittest
from unittest.mock import patch

from api import app, appointments, is_valid_appointment, extract_data_fields


class TestApi(unittest.TestCase):

    def setUp(self):
        appointments.clear()
        self.client = app.test_client()

    def test_list_appointments_empty(self):
        response = self.client.get("/appointments")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, [])

    def test_list_appointments_with_entries(self):
        self.client.post("/appointments", json = {"title": "Meeting", "start": "10:00", "end": "12:00"})
        self.client.post("/appointments", json = {"title": "Meeting2", "start": "13:00", "end": "14:00"})

        response = self.client.get("/appointments")
        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(appointments), 2)

    def test_create_appointment(self):
        response = self.client.post("/appointments", json = {"title": "Meeting", "start": "10:00", "end": "12:00"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(appointments[0]["title"], "Meeting")
        self.assertEqual(appointments[0]["start"], "10:00")
        self.assertEqual(appointments[0]["end"], "12:00")

    def test_create_overlapping_appointment(self):
        self.client.post("/appointments", json = {"title": "Meeting", "start": "10:00", "end": "12:00"})
        response = self.client.post("/appointments", json = {"title": "Meeting2", "start": "09:00", "end": "13:00"})
        self.assertEqual(response.status_code, 409)
        self.assertIn("error", response.json)
        self.assertEqual(response.json["error"], "Overlapping appointment")

    def test_update_appointment(self):
        self.client.post("/appointments", json = {"title": "Meeting", "start": "10:00", "end": "12:00"})
        appt_id = appointments[0]["id"]
        response = self.client.put(f"/appointments/{appt_id}",
                                   json = {"title": "Sommerfest Meeting", "start": "13:00", "end": "15:00"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(appointments[0]["title"], "Sommerfest Meeting")
        self.assertEqual(appointments[0]["start"], "13:00")
        self.assertEqual(appointments[0]["end"], "15:00")

    def test_update_overlapping_appointment(self):
        self.client.post("/appointments",
                         json = {"title": "Meeting", "start": "10:00", "end": "12:00"})
        self.client.post("/appointments", json = {"title": "Meeting2", "start": "13:00", "end": "15:00"})
        response = self.client.put("/appointments/2",
                                   json = {"title": "Meeting2", "start": "11:00", "end": "14:00"})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json["error"], "Overlapping appointment")

    def test_update_overlapping_appointment_id_error(self):
        self.client.post("/appointments", json = {"title": "Meeting", "start": "10:00", "end": "12:00"})
        response = self.client.put("/appointments/2",
                                   json = {"title": "Meeting", "start": "13:00", "end": "14:00"})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["error"], "Appointment not found")

    def test_delete_appointment(self):
        self.client.post("/appointments", json = {"title": "Meeting", "start": "10:00", "end": "12:00"})
        appt_id = appointments[0]["id"]
        response = self.client.delete(f"/appointments/{appt_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "deleted")
        self.assertEqual(len(appointments), 0)

    def test_delete_appointment_not_found(self):
        self.client.post("/appointments", json = {"title": "Meeting", "start": "10:00", "end": "12:00"})
        response = self.client.delete("/appointments/8")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["error"], "Appointment not found")
        self.assertEqual(len(appointments), 1)

    def test_invalide_termine(self):
        fehlerhafte_termine = [
            {},
            {"title": "1"},
            {"title": "1", "end": "1"},
            {"start": "1", "end": "1"},
            {"title": "1", "start": "1"},
            {"title": "1", "start": "1", "end": "1", "geheim": "1"}
        ]

        for json_data in fehlerhafte_termine:
            self.assertFalse(is_valid_appointment(json_data))

    def test_valider_termin(self):
        json_data = {"title": "Meeting", "start": "10:00", "end": "12:00"}
        is_valid_appointment(json_data)

    @patch('api.is_valid_appointment', return_value = True)
    def test_extract_fields_with_valid_appointment(self, mock_is_valid_appointment):
        json_data = {"title": "Meeting", "start": "10:00", "end": "12:00"}
        result = extract_data_fields(json_data)
        mock_is_valid_appointment.assert_called()
        self.assertEqual(result, ("Meeting", "10:00", "12:00"))

    @patch('api.is_valid_appointment', return_value = False)
    def test_mit_invalidem_spieler_objekt(self, mock_is_valid_appointment):
        with self.assertRaises(ValueError) as contextManager:
            extract_data_fields({})
        mock_is_valid_appointment.assert_called()
        self.assertEqual(contextManager.exception.args[0], "Invalid appointment: wrong or missing fields")

    def test_check_appointment_list(self):
        self.assertEqual(len(appointments), 0)

        response = self.client.post("/appointments", json = {"title": "Meeting", "start": "10:00", "end": "12:00"})
        self.assertEqual(response.status_code, 201)

        self.assertEqual(len(appointments), 1)
        self.assertEqual(appointments[0]["title"], "Meeting")
        self.assertEqual(appointments[0]["start"], "10:00")
        self.assertEqual(appointments[0]["end"], "12:00")
