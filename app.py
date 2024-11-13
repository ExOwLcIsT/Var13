from datetime import datetime
from flask import Flask, jsonify, render_template, request, abort
from bson.objectid import ObjectId
from config import get_db

app = Flask(__name__)
db = get_db()


@ app.route('/api/collections', methods=['GET'])
def get_collections():
    collections_info = {}
    collection_names = db.list_collection_names()
    for collection_name in collection_names:
        collection = db[collection_name]
        document_count = collection.count_documents({})
        collections_info[collection_name] = document_count
    return jsonify(collections_info)


@ app.route('/api/collections/<name>', methods=['GET'])
def get_collection(name):
    if name not in db.list_collection_names():
        return jsonify({"error": "Колекцію не знайдено"}), 404

    documents = list(db[name].find({}))
    for doc in documents:
        doc.update({"fields": {}})
        for key in doc.keys():
            if (key != "fields"):
                doc["fields"].update({key: str(type(doc[key]).__name__)})
                doc[key] = str(doc[key])
    response = {
        "collection_name": name,
        "documents": documents
    }

    return jsonify(response), 200


@ app.route('/api/collections/<name>', methods=['DELETE'])
def delete_collection(name):
    db[name].drop()
    collection_names = db.list_collection_names()
    return jsonify(collection_names), 200


@ app.route('/api/collections/<name>', methods=['POST'])
def create_collection(name):
    try:

        if not name:
            return jsonify({'error': 'Необхідна назва колекції'}), 400

        collection = db[name]
        collection.insert_one({"status": "dummy_data"})
        return jsonify({'message': f'Колекція "{name}" успішно створена'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ app.route('/api/collections/<old_name>/<new_name>', methods=['PUT'])
def rename_collection(old_name, new_name):
    try:

        if not old_name or not new_name:
            return jsonify({'error': 'Необхідна нова нзва колекції'}), 400

        db[old_name].rename(new_name)
        return jsonify({'message': f'Колекція "{old_name}" успішно перейменована на "{new_name}"'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/fields/<collection_name>/<old_name>/<new_name>/<document_id>', methods=['PUT'])
def rename_field(collection_name, old_name, new_name, document_id):
    try:
        # Find the document by its ID
        document = db[collection_name].find_one({"_id": ObjectId(document_id)})

        if document is None:
            return jsonify({"error": "Document not found"}), 404

        # Check if the old field name exists in the document
        if old_name not in document:
            return jsonify({"error": f"Field '{old_name}' does not exist in the document"}), 400

        # Update the document: set the new field and remove the old field
        db[collection_name].update_one(
            {"_id": ObjectId(document_id)},
            {"$set": {new_name: document[old_name]}, "$unset": {old_name: ""}}
        )

        return jsonify({"message": f"Field '{old_name}' successfully renamed to '{new_name}'"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ app.route('/api/fields/<collection_name>/<field_name>/<document_id>', methods=['DELETE'])
def delete_field(collection_name, field_name, document_id):
    db[collection_name].update_one({"_id": ObjectId(document_id)}, {
                                   "$unset": {field_name: ""}})
    return jsonify({"message": "Поле успішно видалене"}), 200


@app.route('/api/fields', methods=['POST'])
def add_field_to_document():
    try:
        data = request.json
        collection_name = data.get("collection_name")
        field_name = data.get("field_name")
        field_value = data.get("field_value")
        field_type = data.get("field_type")
        document_id = data.get("documentId")
        print(data)
        if field_type == "int":
            field_value = int(field_value)
        elif field_type == "float":
            field_value = float(field_value)
        elif field_type == "boolean":
            field_value = bool(field_value)
        elif field_type == "date":
            from datetime import datetime
            field_value = datetime.fromisoformat(field_value)
        elif field_type == "ObjectId":
            field_value = ObjectId(field_value)

        result = db[collection_name].update_one(
            {"_id": ObjectId(document_id)},
            {"$set": {field_name: field_value}}
        )

        if result.modified_count == 1:
            return jsonify({"success": True, "message": "Field added successfully."}), 200
        else:
            return jsonify({"success": False, "error": "Field not added."}), 400

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/documents/<collection_name>/<document_id>', methods=['DELETE'])
def delete_document(collection_name, document_id):
    try:
        result = db[collection_name].delete_one({"_id": ObjectId(document_id)})

        if result.deleted_count == 1:
            return jsonify({"success": True, "message": "Document deleted successfully."}), 200
        else:
            return jsonify({"success": False, "error": "Document not found."}), 404

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@ app.route('/api/collection/<collection_name>', methods=['POST'])
def add_document(collection_name):
    data = request.get_json()

    result = db[collection_name].insert_one(data)
    if result.inserted_id:
        return jsonify({"message": "Документ успішно додано", "id": str(result.inserted_id)}), 200
    else:
        return jsonify({"error": "Не вдалося додати документ"}), 500


@app.route('/api/documents/<collection_name>/<field_name>/<document_id>', methods=['PUT'])
def update_document_field(collection_name, document_id, field_name):

    try:
        new_value = request.json.get('new_value')
        new_type = request.json.get('new_type')
        if new_type == "string":
            new_value = str(new_value)
        elif new_type == "int":
            new_value = int(new_value)
        elif new_type == "float":
            new_value = float(new_value)
        elif new_type == "boolean":
            new_value = bool(new_value)
        elif new_type == "date":
            new_value = datetime.fromisoformat(
                new_value.replace("Z", "+00:00"))
        else:
            return jsonify({"error": "Unsupported field type"}), 400

        result = db[collection_name].update_one(
            {"_id": ObjectId(document_id)},
            {"$set": {field_name: new_value}}
        )
        if result.modified_count == 1:
            return jsonify({"message": "Field successfully updated"}), 200
        else:
            return jsonify({"error": "Field not updated"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ app.route('/', methods=['GET'])
def get_index_page():
    return render_template("index.html")


@ app.route('/authorization', methods=['GET'])
def get_authorize_page():
    return render_template("authorize.html")


@app.route('/api/authorization/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    user = db["Keys"].find_one({"username": username, "password": password})
    if user is None:
        return jsonify({"message": "неправильне ім'я користувача або пароль"}), 400
    return jsonify({"role": user["role"]})


@app.route('/api/authorization/register', methods=['POST'])
def register_user():
    data = request.get_json()

    username = data.get('username')
    password = data.get('password')
    role = data.get('role')

    if not username or not password or not role:
        return jsonify({"success": False, "message": "All fields are required"}), 400

    users = db["Keys"].find()
    existing_user = next(
        (user for user in users if user['username'] == username), None)
    if existing_user:
        return jsonify({"success": False, "message": "Username already exists"}), 400

    db["Keys"].insert_one(
        {"username": username, "password": password, "role": role})

    return jsonify({"success": True, "message": "User registered successfully"}), 201


@app.route("/request1", methods=["GET"])
def get_request1():
    return render_template("request1.html")


@app.route("/api/request1", methods=["GET"])
def get_request1_data():
    profits = 0
    costs = 0

    groups = list(db["групи"].find({}))
    for group in groups:
        flight = db["рейси"].find_one({"_id": group["рейс"]})
        tourists = db["туристи"].find({})
        tourists = list(
            tourist for tourist in tourists if tourist["_id"] in group["туристи"])
        costs += sum(tourist["страхові_виплати"] for tourist in tourists)
        plane = db["літаки"].find_one({"_id": flight["літак"]})
        costs += plane["вартість_обслуговування"]

        excursions = list(db["екскурсії"].find({}))
        excursions = list(
            excursion for excursion in excursions if excursion["_id"] in group["екскурсії"])
        costs += sum(excursion["вартість_бронювання"]
                     for excursion in excursions) * tourists.__len__()
        profits += flight["вартість"] * \
            (sum(tourist["діти"] for tourist in tourists) + 1)
        profits += sum(tourist["вартість_упакування"] for tourist in tourists)
    return jsonify({"витрати": costs, "доходи": profits, "рентабельність": profits/costs})


@app.route("/request2", methods=["GET"])
def get_request2():
    return render_template("request2.html")


@app.route("/api/request2", methods=["POST"])
def get_request2_data():
    costs = 0
    plane_costs = 0
    excursion_costs = 0
    insurance_costs = 0
    start = request.json.get("start")
    end = request.json.get("end")
    start = datetime.fromisoformat(start)
    end = datetime.fromisoformat(end)
    groups = list(db["групи"].find({}))
    groups = list(group for group in groups if (
        start < group["дата_повернення"] and end > group["дата_відправлення"]))
    for group in groups:
        flight = db["рейси"].find_one({"_id": group["рейс"]})
        tourists = db["туристи"].find({})
        tourists = list(
            tourist for tourist in tourists if tourist["_id"] in group["туристи"])
        insurance_costs += sum(tourist["страхові_виплати"]
                               for tourist in tourists)
        costs += sum(tourist["страхові_виплати"] for tourist in tourists)
        plane = db["літаки"].find_one({"_id": flight["літак"]})
        plane_costs += plane["вартість_обслуговування"]
        costs += plane["вартість_обслуговування"]

        excursions = list(db["екскурсії"].find({}))
        excursions = list(
            excursion for excursion in excursions if excursion["_id"] in group["екскурсії"])

        excursion_costs += sum(excursion["вартість_бронювання"]
                               for excursion in excursions) * tourists.__len__()
        costs += sum(excursion["вартість_бронювання"]
                     for excursion in excursions) * tourists.__len__()

    return jsonify({"загальні витрати": costs, "витрати на літаки": plane_costs, "витрати на страховку": insurance_costs, "витрати на екскурсії:": excursion_costs})


@app.route("/request3", methods=["GET"])
def get_request3():
    return render_template("request3.html")


@app.route("/api/request3", methods=["POST"])
def get_request3_data():
    baggage = 0
    occupied_seats = 0
    date = request.json.get("date")
    date = datetime.fromisoformat(date)
    print(date)
    groups = list(db["групи"].find({}))
    print(groups)
    groups = list(group for group in groups if (
        date == group["дата_повернення"] or date == group["дата_відправлення"]))
    if (groups.__len__() == 0):
        return jsonify({"message": "рейсів не знайдено"}), 404
    for group in groups:
        tourists = db["туристи"].find({})
        tourists = list(
            tourist for tourist in tourists if tourist["_id"] in group["туристи"])
        baggage = (sum(tourist["вага_вантажу"] for tourist in tourists))
        occupied_seats = (sum(tourist["діти"] for tourist in tourists) + 1)
    return jsonify({"зайнятих_місць": occupied_seats, "вага_вантажу": baggage}), 200


@app.route("/request4", methods=["GET"])
def get_request4():
    return render_template("request4.html")


@app.route("/api/request4", methods=["POST"])
def get_request4_data():
    start = request.json.get("start")
    end = request.json.get("end")
    start = datetime.fromisoformat(start)
    end = datetime.fromisoformat(end)
    top_exc = {}
    total_trsts = set()
    groups = list(db["групи"].find({}))
    groups = list(group for group in groups if (
        start < group["дата_повернення"] and end > group["дата_відправлення"]))
    for group in groups:
        tourists = db["туристи"].find({})
        tourists = list(tourist for tourist in tourists if (
            tourist["_id"] in group["туристи"] and tourist["тип_туриста"] == "відпочинок"))
        total_trsts.update(list(tourist["ПІБ"] for tourist in tourists))
        for exc in group["екскурсії"]:
            top_exc.update({exc: tourists.__len__()})
    top1_exc = db["екскурсії"].find_one(
        {"_id": max(top_exc, key=top_exc.get)}, {"_id": 0})
    tourists_count = total_trsts.__len__()
    tourists = list(db["туристи"].find({}))
    for tourist in tourists:
        if tourist["ПІБ"] in total_trsts:
            tourists_count += tourist["діти"]
    return jsonify({"кількість туристів ": tourists_count, "найпопулярніша екскурсія":  str(top1_exc)}), 200


@app.route("/request5", methods=["GET"])
def get_request5():
    return render_template("request5.html")


@app.route("/api/request5", methods=["POST"])
def get_request5_data():
    start = request.json.get("start")
    end = request.json.get("end")
    start = datetime.fromisoformat(start)
    end = datetime.fromisoformat(end)
    total_trsts = set()
    total_baggage = 0
    groups = list(db["групи"].find({}))
    groups = list(group for group in groups if (
        start < group["дата_повернення"] and end > group["дата_відправлення"]))
    for group in groups:
        tourists = db["туристи"].find({})
        tourists = list(tourist for tourist in tourists if (
            tourist["_id"] in group["туристи"] and tourist["тип_туриста"] == "вантаж"))
        total_trsts.update(list(tourist["ПІБ"] for tourist in tourists))
    for tourist in tourists:
        if tourist["ПІБ"] in total_trsts:
            total_baggage += tourist["вага_вантажу"]
    return jsonify({"місць для вантажу": total_trsts.__len__(), "загальна вага вантажу": total_baggage, "кількість літаків": groups.__len__()}), 200


@app.route("/request6", methods=["GET"])
def get_request6():
    return render_template("request6.html")


@app.route("/api/request6", methods=["POST"])
def get_request6_data():
    tourist_id = request.json.get("tourist_id")
    country = request.json.get("country")

    if not tourist_id or not country:
        return jsonify({"error": "Необхідні параметри tourist_id та country"}), 400
    tourist_id = ObjectId(tourist_id)
    tourist = db["туристи"].find_one({"_id": tourist_id})
    if not tourist:
        return jsonify({"error": "Туриста не знайдено"}), 404

    visit_count = 0
    flight_dates = []
    hotels = []
    excursions = []
    baggage_info = []

    groups = list(db["групи"].find({"туристи": tourist_id}))
    for group in groups:
        flight = db["рейси"].find_one({"_id": group["рейс"]})
        if flight and flight["країна_прибуття"] == country:
            visit_count += 1
            flight_dates.append({
                "дата_відправлення": group["дата_відправлення"],
                "дата_повернення": group["дата_повернення"]
            })
            hotels += group["готелі"]

            for excursion_id in group["екскурсії"]:
                excursion = db["екскурсії"].find_one({"_id": excursion_id})
                if excursion:
                    excursions.append({
                        "країна екскурсії": excursion["країна"],
                        "агентство": excursion["агентство"]
                    })

            baggage_info = tourist["вага_вантажу"]

    result = {
        "турист": tourist["ПІБ"],
        "кількість_відвідувань": visit_count,
        "дати_перебування": str(flight_dates),
        "готелі": list(set(hotels)),
        "екскурсії": str(excursions),
        "вантаж": str(baggage_info)
    }

    return jsonify(result)


@app.route("/request7", methods=["GET"])
def get_request7():
    return render_template("request7.html")


@app.route("/api/request7", methods=["POST"])
def get_request7_data():
    group_id = request.json.get("group_id")
    tourist_type = request.json.get("type")

    if not group_id:
        return jsonify({"error": "Необхідний параметр group_id"}), 400

    group_id = ObjectId(group_id)

    group = db["групи"].find_one({"_id": group_id})
    if not group:
        return jsonify({"error": "Групу не знайдено"}), 404

    total_profits = 0
    total_costs = 0
    category_profits = 0
    category_costs = 0

    flight = db["рейси"].find_one({"_id": group["рейс"]})
    if flight:
        plane = db["літаки"].find_one({"_id": flight["літак"]})
        if plane:
            total_costs += plane["вартість_обслуговування"]

        total_profits += flight["вартість"]

    tourists = list(db["туристи"].find({"_id": {"$in": group["туристи"]}}))

    for tourist in tourists:
        total_costs += tourist["страхові_виплати"]
        total_profits += tourist.get("вартість_упакування", 0)

        if not tourist_type or tourist["тип_туриста"] == tourist_type:
            category_costs += tourist["страхові_виплати"]
            category_profits += tourist.get("вартість_упакування", 0)

    excursions = list(db["екскурсії"].find(
        {"_id": {"$in": group["екскурсії"]}}))
    for excursion in excursions:
        total_costs += excursion["вартість_бронювання"] * len(tourists)
        if not tourist_type:
            category_costs += excursion["вартість_бронювання"] * len(tourists)
        else:
            for tourist in tourists:
                if tourist["тип_туриста"] == tourist_type:
                    category_costs += excursion["вартість_бронювання"]

    result = {
        "загальні": {
            "доходи": total_profits,
            "витрати": total_costs,
            "рентабельність": total_profits / total_costs if total_costs != 0 else 0
        },
        "категорія": {
            "тип туриста": tourist_type if tourist_type else "всі",
            "доходи": category_profits,
            "витрати": category_costs,
            "рентабельність": category_profits / category_costs if category_costs != 0 else 0
        }
    }

    return jsonify(result)


@app.route("/request8", methods=["GET"])
def get_request8():
    return render_template("request8.html")


@app.route("/api/request8", methods=["GET"])
def get_request8_data():
    hotels = list(db["готелі"].find({}, {"_id": 0}))
    return jsonify(hotels)


@app.route("/request9", methods=["GET"])
def get_request9():
    return render_template("request9.html")


@app.route("/api/request9", methods=["GET"])
def get_request9_data():
    tourists = list(db["туристи"].find(
        {}, {"_id": 0, "ПІБ": 1, "вік": 1, "стать": 1}))

    baggage_tourists = list(db["туристи"].find(
        {"тип_туриста": "вантаж"}, {"_id": 0, "ПІБ": 1, "вік": 1, "стать": 1}))

    rest_tourists = list(db["туристи"].find(
        {"тип_туриста": "відпочинок"}, {"_id": 0, "ПІБ": 1, "вік": 1, "стать": 1}))
    return jsonify({"tourists": tourists, "baggage_tourists": baggage_tourists, "rest_tourists": rest_tourists})


@app.route("/request10", methods=["GET"])
def get_request10():
    return render_template("request10.html")


@app.route("/api/request10", methods=["POST"])
def get_request10_data():
    country = request.json.get("country")
    start_date_str = request.json.get("start")
    end_date_str = request.json.get("end")

    start_date = datetime.fromisoformat(start_date_str)
    end_date = datetime.fromisoformat(end_date_str)

    groups = db["групи"].find({})
    groups = list(group for group in groups if (
        start_date < group["дата_повернення"] and end_date > group["дата_відправлення"]))
    all_travelers = []

    for group in groups:
        flight = db["рейси"].find_one({"_id": group["рейс"]})
        if flight and flight["країна_прибуття"] == country:
            tourists = db["туристи"].find({"_id": {"$in": group["туристи"]}})

            for tourist in tourists:
                tourist_info = {
                    "ПІБ": tourist["ПІБ"],
                    "паспортні_дані": tourist["паспортні_дані"],
                    "тип_туриста": tourist["тип_туриста"],
                    "вага_вантажу": tourist.get("вага_вантажу", 0),
                    "готель": tourist.get("готель"),
                    "дата_відправлення": group["дата_відправлення"],
                    "дата_повернення": group["дата_повернення"]
                }

                all_travelers.append(tourist_info)

    return jsonify({
        "всі_туристи": all_travelers
    })


if __name__ == '__main__':
    app.run(debug=True)
