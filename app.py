from datetime import datetime
from flask import Flask, jsonify, render_template, request, abort
from bson.objectid import ObjectId
from bson.datetime_ms import DatetimeMS
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
    fields = {}
    for doc in documents:
        for key in doc.keys():
            fields.update({key: str(type(doc[key]).__name__)})
            if str(type(doc[key]).__name__) == "ObjectId":
                doc[key] = str(doc[key])
    response = {
        "collection_name": name,
        "fields": fields,
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


@ app.route('/api/collections/document/<collection_name>/<document_id>', methods=['DELETE'])
def delete_document(collection_name, document_id):
    db[collection_name].delete_one({"_id": ObjectId(document_id)})
    return jsonify({"message": "Документ успішно видалено"}), 200


@ app.route('/api/collections/document/<collection_name>/<document_id>', methods=['PUT'])
def update_document(collection_name, document_id):
    updated_data = request.json
    db[collection_name].update_one(
        {"_id": ObjectId(document_id)}, {"$set": updated_data})
    return jsonify({"message": "Документ успішно оновлено"}), 200


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
        print(collection_name)
        print(document_id)
        print(field_name)
        print(new_value)
        print(new_type)
        if new_type == "string":
            new_value = str(new_value)
        elif new_type == "int":
            new_value = int(new_value)
        elif new_type == "float":
            new_value = float(new_value)
        elif new_type == "boolean":
            new_value = bool(new_value)
        elif new_type == "date":
            new_value =  datetime.fromisoformat(new_value.replace("Z", "+00:00"))
            print(new_value)
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
    return render_template(
        "index.html"
    )


if __name__ == '__main__':
    app.run(debug=True)
