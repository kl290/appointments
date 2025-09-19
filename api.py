from flask import Flask, request, jsonify

app = Flask(__name__)

appointments = []
next_id = 1

@app.route("/appointments", methods=["GET"])
def list_appointments():
    return jsonify(appointments), 200

@app.route("/appointments", methods=["POST"])
def create_appointment():
    global next_id
    data = request.get_json()

    start = data.get("start")
    end = data.get("end")
    title = data.get("title", "")

    for appointment in appointments:
        if (start >= appointment["start"] and start <= appointment["end"]) or \
                (end >= appointment["start"] and end <= appointment["end"]):
            return jsonify({"error": "Overlapping appointment"}), 200

    appointment = {
        "id": next_id,
        "title": title,
        "start": start,
        "end": end
    }
    appointments.append(appointment)
    next_id += 1

    return jsonify(appointment), 200

@app.route("/appointments/<int:appt_id>", methods=["PUT"])
def update_appointment(appt_id):
    data = request.get_json()

    for appt in appointments:
        if appt["id"] == appt_id:
            appt["title"] = data.get("title", appt["title"])
            appt["start"] = data.get("start", appt["start"])
            appt["end"] = data.get("end", appt["end"])
            return jsonify(appt), 200

    return jsonify({"error": "Appointment not found"}), 200


@app.route("/appointments/<int:appt_id>", methods=["DELETE"])
def delete_appointment(appt_id):
    global appointments
    appointments = [a for a in appointments if a["id"] != appt_id]
    return jsonify({"status": "deleted"}), 200


if __name__ == "__main__":
    app.run(debug=True)
