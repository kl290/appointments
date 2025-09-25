from flask import Flask, request, jsonify

app = Flask(__name__)

appointments = []
next_id = 1


def extract_data_fields(json_data):
    if not is_valid_appointment(json_data):
        raise ValueError("Invalid appointment: wrong or missing fields")

    return json_data.get("title"), json_data.get("start"), json_data.get("end")


def is_valid_appointment(json_data):
    return {"title", "start", "end"} == set(json_data.keys())


@app.route("/appointments", methods = ["GET"])
def list_appointments():
    return jsonify(appointments), 200


@app.route("/appointments", methods = ["POST"])
def create_appointment():
    global next_id
    data = request.get_json()
    title, start, end = extract_data_fields(data)

    for appointment in appointments:
        if end >= appointment["start"] and start <= appointment["end"]:
            return jsonify({"error": "Overlapping appointment"}), 409

    appointment = {
        "id": next_id,
        "title": title,
        "start": start,
        "end": end
    }
    appointments.append(appointment)
    next_id += 1

    return jsonify(appointment), 201


@app.route("/appointments/<int:appt_id>", methods = ["PUT"])
def update_appointment(appt_id):
    data = request.get_json()
    title, start, end = extract_data_fields(data)

    for appt in appointments:
        if end >= appt["start"] and start <= appt["end"]:
            return jsonify({"error": "Overlapping appointment"}), 409

        if appt["id"] == appt_id:
            appt["title"] = title
            appt["start"] = start
            appt["end"] = end
            return jsonify(appt), 200

    return jsonify({"error": "Appointment not found"}), 404


@app.route("/appointments/<int:appt_id>", methods = ["DELETE"])
def delete_appointment(appt_id):
    for appt in appointments:
        if appt["id"] == appt_id:
            appointments.remove(appt)
            return jsonify({"status": "deleted"}), 200

    return jsonify({"error": "Appointment not found"}), 404


if __name__ == "__main__":  # pragma: no coverage
    app.run(debug = True)
