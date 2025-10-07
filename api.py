from datetime import datetime, timedelta

from flask import Flask, request, jsonify

app = Flask(__name__)

appointments = []
next_id = 1
CATEGORY_TYPES = ["health", "general", "work", "social"]
TIME_FORMAT = "%Y-%m-%d %H:%M"


def extract_and_validate_data_fields(json_data):
    validate_appointment(json_data)

    title = json_data.get("title")
    start_str = json_data.get("start")
    end_str = json_data.get("end")
    category = json_data.get("category")

    validate_category_types(category)
    start = datetime.strptime(start_str, TIME_FORMAT)
    end = datetime.strptime(end_str, TIME_FORMAT)

    return title, start, end, category


def validate_appointment(json_data):
    if ["category", "end", "start", "title"] != sorted(json_data.keys()):
        raise ValueError("Invalid appointment: wrong or missing fields")


def validate_category_types(category):
    if category not in CATEGORY_TYPES:
        raise ValueError(f"Invalid category. Must be one of {CATEGORY_TYPES}")


def serialize_datetime_format(appt):
    return {
        "id": appt["id"],
        "title": appt["title"],
        "start": appt["start"].strftime(TIME_FORMAT),
        "end": appt["end"].strftime(TIME_FORMAT),
        "category": appt["category"]
    }


@app.route("/appointments", methods = ["GET"])
def list_appointments():
    category_filter = request.args.get("category")

    if category_filter:
        try:
            validate_category_types(category_filter)
        except ValueError as e:
            return jsonify({"error": str(e)})

        filtered = [serialize_datetime_format(appt) for appt in appointments if appt["category"] == category_filter]

        if not filtered:
            return jsonify({"error": "No appointments found for this category"}), 404
        return jsonify(filtered), 200
    return jsonify([serialize_datetime_format(appt) for appt in appointments]), 200


@app.route("/appointments", methods = ["POST"])
def create_appointment():
    global next_id
    data = request.get_json()
    try:
        title, start, end, category = extract_and_validate_data_fields(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

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
    return jsonify(serialize_datetime_format(appointment)), 201


@app.route("/appointments/<int:appt_id>", methods = ["PUT"])
def update_appointment(appt_id):
    data = request.get_json()
    try:
        title, start, end, category = extract_and_validate_data_fields(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    for appt in appointments:
        if appt["id"] != appt_id and end >= appt["start"] and start <= appt["end"]:
            return jsonify({"error": "Overlapping appointment"}), 409

        if appt["id"] == appt_id:
            appt["title"] = title
            appt["start"] = start
            appt["end"] = end
            appt["category"] = category
            return jsonify(serialize_datetime_format(appt)), 200

    return jsonify({"error": "Appointment not found"}), 404


@app.route("/appointments/<int:appt_id>", methods = ["DELETE"])
def delete_appointment(appt_id):
    for appt in appointments:
        if appt["id"] == appt_id:
            appointments.remove(appt)
            return jsonify({"status": "deleted"}), 200

    return jsonify({"error": "Appointment not found"}), 404


@app.route("/appointments/shift/<int:appt_id>", methods = ["POST"])
def shift_appointment(appt_id):
    amount_start = request.args.get("amount_start", "0")
    amount_end = request.args.get("amount_end", "0")

    try:
        shift_st = timedelta(days = float(amount_start))
        shift_end = timedelta(days = float(amount_end))
    except ValueError:
        return jsonify({"error": "Invalid amount. Must be a number."}), 400

    for appt in appointments:
        if appt["id"] == appt_id:
            new_start = appt["start"] + shift_st
            new_end = appt["end"] + shift_end

            if new_start > new_end:
                return jsonify({"error": "Shift would result in start after end"}), 400

            for other in appointments:
                if other["id"] != appt_id and new_end > other["start"] and new_start < other["end"]:
                    return jsonify({"error": "Shift would cause overlapping appointment"}), 409

            appt["start"] = new_start
            appt["end"] = new_end
            return jsonify(serialize_datetime_format(appt)), 200

    return jsonify({"error": "Appointment not found"}), 404


app.config['app.json.sort_keys'] = False

if __name__ == "__main__":  # pragma: no coverage
    app.run(debug = True)
