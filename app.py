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
                if str(type(doc[key]).__name__) == "ObjectId":
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


@app.route('/api/fields/<collection_name>/<document_id>', methods=['POST'])
def add_field_to_document(collection_name, document_id):
    try:
        data = request.json
        field_name = data.get("field_name")
        field_value = data.get("field_value")
        field_type = data.get("field_type")

        # Convert field_value based on field_type
        if field_type == "number (int)":
            field_value = int(field_value)
        elif field_type == "number (float)":
            field_value = float(field_value)
        elif field_type == "boolean":
            field_value = bool(field_value)
        elif field_type == "date":
            # Assuming the date is in ISO format; adjust as necessary
            from datetime import datetime
            field_value = datetime.fromisoformat(field_value)
        elif field_type == "ObjectId":
            field_value = ObjectId(field_value)

        # Update document in MongoDB
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


@ app.route('/api/collection/<collection_name>/<field_name>/<field_type>', methods=['POST'])
def add_field(collection_name, field_name, field_type):
    if not field_type:
        return jsonify({"error": "Необхідний тип поля"}), 400

    if not field_name:
        return jsonify({"error": "Необхідна назва поля"}), 400
    default_value = ""
    if field_type == "string":
        default_value = ""
    elif field_type == "int":
        default_value = 0
    elif field_type == "float":
        default_value = 0.0
    elif field_type == "boolean":
        default_value = False
    elif field_type == "date":
        default_value = datetime.now()
    elif field_type == 'objectId':
        default_value = ''
    else:
        return jsonify({"error": "Невизначений тип поля"}), 400
    db[collection_name].update_many({}, {"$set": {field_name: default_value}})
    return jsonify({"message": "Поле успішно додане"}), 200


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
    return jsonify({"role": user["access_rights"]})


@app.route('/api/authorization/register', methods=['POST'])
def register_user():
    # Get the data from the request
    data = request.get_json()

    # Extract username, password, and role from the request body
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')

    # Check if all fields are provided
    if not username or not password or not role:
        return jsonify({"success": False, "message": "All fields are required"}), 400

    # Check if the user already exists
    users = db["Keys"].find()
    existing_user = next(
        (user for user in users if user['username'] == username), None)
    if existing_user:
        return jsonify({"success": False, "message": "Username already exists"}), 400

    # Add the new user to the list
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


@app.route("/request3", methods=["GET"])
def get_request3():
    return render_template("request3.html")


@app.route("/request4", methods=["GET"])
def get_request4():
    return render_template("request4.html")


@app.route("/request5", methods=["GET"])
def get_request5():
    return render_template("request5.html")


@app.route("/request6", methods=["GET"])
def get_request6():
    return render_template("request6.html")


@app.route("/request7", methods=["GET"])
def get_request7():
    return render_template("request7.html")


@app.route("/request8", methods=["GET"])
def get_request8():
    return render_template("request8.html")


@app.route("/request9", methods=["GET"])
def get_request9():
    return render_template("request9.html")


@app.route("/request10", methods=["GET"])
def get_request10():
    return render_template("request10.html")


if __name__ == '__main__':
    app.run(debug=True)
