from flask import Flask, request, jsonify

app = Flask(__name__)

appointments = []
next_id = 1
category_types = ["health", "general", "work", "social"]


def extract_and_validate_data_fields(json_data):
    validate_appointment(json_data)

    title = json_data.get("title")
    start = json_data.get("start")
    end = json_data.get("end")
    category = json_data.get("category")

    validate_category_types(category)

    return title, start, end, category


def validate_appointment(json_data):
    if {"title", "start", "end", "category"} != set(json_data.keys()):
        raise ValueError("Invalid appointment: wrong or missing fields")


def validate_category_types(category):
    if category not in category_types:
        raise ValueError(f"Invalid category. Must be one of {category_types}")


@app.route("/appointments", methods = ["GET"])
def list_appointments():
    category_filter = request.args.get("category")

    if category_filter:
        try:
            validate_category_types(category_filter)
        except ValueError as e:
            return jsonify({"error": str(e)})

        filtered = [appt for appt in appointments if appt["category"] == category_filter]

        if not filtered:
            return jsonify({"error": "No appointments found for this category"}), 404
        return jsonify(filtered), 200
    return jsonify(appointments), 200


@app.route("/appointments", methods = ["POST"])
def create_appointment():
    global next_id
    data = request.get_json()
    title, start, end, category = extract_and_validate_data_fields(data)

    for appointment in appointments:
        if end >= appointment["start"] and start <= appointment["end"]:
            return jsonify({"error": "Overlapping appointment"}), 409

    appointment = {
        "id": next_id,
        "title": title,
        "start": start,
        "end": end,
        "category": category,
    }
    appointments.append(appointment)
    next_id += 1

    return jsonify(appointment), 201


@app.route("/appointments/<int:appt_id>", methods = ["PUT"])
def update_appointment(appt_id):
    data = request.get_json()
    title, start, end, category = extract_and_validate_data_fields(data)

    for appt in appointments:
        if end >= appt["start"] and start <= appt["end"]:
            return jsonify({"error": "Overlapping appointment"}), 409

        if appt["id"] == appt_id:
            appt["title"] = title
            appt["start"] = start
            appt["end"] = end
            appt["category"] = category
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
