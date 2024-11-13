const apiUrl = 'http://127.0.0.1:5000/api';

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

function deleteCookie(name) {
    document.cookie = name + '=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
    hideElementsBasedOnRole();
}

async function fetchCollections() {
    const response = await fetch('/api/collections');
    const collections = await response.json();
    const collectionList = document.getElementById('collection-list');
    collectionList.innerHTML = '';

    Object.keys(collections).forEach(name => {
        const li = document.createElement('li');
        li.textContent = `${name} (${collections[name]}) `;
        li.onclick = () => fetchCollectionDetails(name);
        li.classList.add("collection")

        const renameBtn = document.createElement('button');
        renameBtn.textContent = 'Rename';
        renameBtn.onclick = () => renameCollection(name);
        li.appendChild(renameBtn);

        const deleteBtn = document.createElement('button');
        deleteBtn.textContent = 'Delete';
        deleteBtn.onclick = () => deleteCollection(name);
        li.appendChild(deleteBtn);

        collectionList.appendChild(li);
    });
}

async function createCollection() {
    const collectionName = document.getElementById('new-collection-name').value.trim();
    if (!collectionName) {
        alert('Please enter a collection name.');
        return;
    }

    const response = await fetch(`/api/collections/${collectionName}`, {
        method: 'POST'
    });

    if (response.ok) {
        alert(`Collection "${collectionName}" created successfully.`);
        document.getElementById('new-collection-name').value = ''; // Clear input
        fetchCollections(); // Refresh collection list
    } else {
        const errorData = await response.json();
        alert(`Error: ${errorData.error}`);
    }
}

async function deleteCollection(name) {
    const response = await fetch(`/api/collections/${name}`, {
        method: 'DELETE'
    });
    if (response.ok) {
        alert(`Collection "${name}" deleted.`);
        fetchCollections();
    } else {
        alert('Error deleting collection.');
    }
}

async function renameCollection(oldName) {
    const newName = prompt('Enter new collection name:');
    if (newName && newName !== oldName) {
        const response = await fetch(`/api/collections/${oldName}/rename/${newName}`, {
            method: 'PUT'
        });
        if (response.ok) {
            alert(`Collection "${oldName}" renamed to "${newName}".`);
            fetchCollections();
        } else {
            alert('Error renaming collection.');
        }
    }
}

function fetchCollectionDetails(collectionName) {
    fetch(`${apiUrl}/collections/${collectionName}`)
        .then(response => response.json())
        .then(data => {
            const documentCardsContainer = document.getElementById('document-cards');
            documentCardsContainer.innerHTML = '';

            data.documents.forEach(doc => {
                const card = document.createElement('div');
                card.classList.add('card');
                card.innerHTML = `<h3>Document ID: ${doc._id}</h3>`;

                const deleteDocBtn = document.createElement('button');
                deleteDocBtn.textContent = 'Delete Document';
                deleteDocBtn.classList.add('delete-doc-btn', "card-buttons", 'operator-only');
                deleteDocBtn.onclick = () => deleteDocument(collectionName, doc._id);
                card.appendChild(deleteDocBtn);

                for (const [key, value] of Object.entries(doc)) {
                    if (key !== '_id' && key != "fields") {
                        const fieldDiv = document.createElement('div');
                        fieldDiv.classList.add('field-container');
                        fieldDiv.setAttribute('data-field-name', key);

                        const renameBtn = document.createElement('button');
                        renameBtn.textContent = 'Rename';
                        renameBtn.classList.add('rename-btn', "card-buttons", 'admin-only');
                        renameBtn.onclick = () => renameField(collectionName, doc._id, key);

                        const removeBtn = document.createElement('button');
                        removeBtn.textContent = 'Remove';
                        removeBtn.classList.add('remove-btn', "card-buttons", 'admin-only');
                        removeBtn.onclick = () => deleteField(collectionName, doc._id, key);

                        const editBtn = document.createElement('button');
                        editBtn.textContent = 'Edit';
                        editBtn.classList.add('edit-btn', "card-buttons", 'operator-only');
                        editBtn.onclick = () => showEditFieldInput(collectionName, doc._id, key, value);

                        fieldDiv.appendChild(renameBtn);
                        fieldDiv.appendChild(removeBtn);
                        fieldDiv.appendChild(editBtn);

                        const fieldContent = document.createElement('p');
                        fieldContent.innerHTML = `<strong>${key}:</strong> ${value} <span class="field-type">Type: ${doc["fields"][key]}</span>`;
                        fieldDiv.appendChild(fieldContent);
                        card.appendChild(fieldDiv);
                    }
                }

                const addFieldDiv = document.createElement('div');
                addFieldDiv.classList.add('add-field-container');

                const addFieldBtn = document.createElement('button');
                addFieldBtn.textContent = 'Add Field';
                addFieldBtn.classList.add('add-field-btn', "card-buttons", 'admin-only');
                addFieldBtn.onclick = () => showAddFieldInput(addFieldDiv, collectionName, doc._id);
                card.appendChild(addFieldBtn);

                card.appendChild(addFieldDiv);

                documentCardsContainer.appendChild(card);
            });
            hideElementsBasedOnRole();
        })
        .catch(error => console.error('Error fetching collection details:', error));
}

function showAddFieldInput(container, collectionName, documentId) {
    container.innerHTML = '';

    const fieldNameInput = document.createElement('input');
    fieldNameInput.placeholder = 'Field Name';
    fieldNameInput.type = 'string';
    container.appendChild(fieldNameInput);

    const fieldTypeSelect = document.createElement('select');
    ['string', 'int', 'float', 'boolean', 'date', 'ObjectId'].forEach(type => {
        const option = document.createElement('option');
        option.value = type;
        option.textContent = type;
        fieldTypeSelect.appendChild(option);
    });
    container.appendChild(fieldTypeSelect);

    const fieldValueInput = document.createElement('input');
    container.appendChild(fieldValueInput);

    fieldTypeSelect.onchange = () => {
        const selectedType = fieldTypeSelect.value;
        if (selectedType === 'int') {
            fieldValueInput.type = 'number';
            fieldValueInput.step = '1';
        } else if (selectedType === 'float') {
            fieldValueInput.type = 'number';
            fieldValueInput.step = '0.01';
        } else if (selectedType === 'date') {
            fieldValueInput.type = 'date';
        } else if (selectedType === 'boolean') {
            fieldValueInput.type = 'checkbox';
        } else {
            fieldValueInput.type = 'string';
        }
    };
    fieldTypeSelect.onchange();

    const submitBtn = document.createElement('button');
    submitBtn.textContent = 'Add Field';
    submitBtn.onclick = () => {
        const fieldName = fieldNameInput.value;
        const fieldType = fieldTypeSelect.value;
        let fieldValue = fieldValueInput.value;

        if (fieldType === 'int') {
            fieldValue = parseInt(fieldValue, 10);
        } else if (fieldType === 'float') {
            fieldValue = parseFloat(fieldValue);
        } else if (fieldType === 'boolean') {
            fieldValue = fieldValueInput.checked;
        } else if (fieldType === 'date') {
            fieldValue = new Date(fieldValueInput.value);
        }

        addFieldToDocument(collectionName, documentId, fieldName, fieldValue, fieldType);
    };
    container.appendChild(submitBtn);
}

function addFieldToDocument(collectionName, documentId, fieldName, fieldValue, fieldType) {
    fetch(`${apiUrl}/fields`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                "collection_name": collectionName,
                "documentId": documentId,
                "field_name": fieldName,
                "field_value": fieldValue,
                "field_type": fieldType
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Field added successfully!');
                fetchCollectionDetails(collectionName);
            } else {
                alert(`Error adding field: ${data.error}`);
            }
        })
        .catch(error => console.error('Error adding field:', error));
}

function deleteDocument(collectionName, documentId) {
    fetch(`${apiUrl}/documents/${collectionName}/${documentId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Document deleted successfully!');
                fetchCollectionDetails(collectionName);
            } else {
                alert(`Error deleting document: ${data.error}`);
            }
        })
        .catch(error => console.error('Error deleting document:', error));
}


function showEditFieldInput(collectionName, documentId, fieldName, currentValue) {
    const fieldDiv = document.querySelector(`.field-container[data-field-name="${fieldName}"]`);
    if (!fieldDiv) return;

    const inputField = document.createElement('input');
    inputField.classList.add('edit-input');

    if (typeof currentValue === 'string') {
        inputField.type = 'text';
        inputField.value = currentValue;
    } else if (typeof currentValue === 'number') {
        if (Number.isInteger(currentValue)) {
            inputField.type = 'number';
            inputField.value = currentValue;
        } else {
            inputField.type = 'number';
            inputField.step = 'any';
            inputField.value = currentValue;
        }
    } else if (Object.prototype.toString.call(currentValue) === '[object Date]') {
        inputField.type = 'date';
        inputField.value = new Date(currentValue).toISOString().split('T')[0];
    } else if (typeof currentValue === 'boolean') {
        inputField.type = 'checkbox';
        inputField.checked = currentValue;
    } else if (currentValue && currentValue.$oid) {
        inputField.type = 'text';
        inputField.value = currentValue.$oid;
    } else {
        inputField.type = 'text';
        inputField.value = currentValue;
    }

    const typeSelect = document.createElement('select');
    const types = ['text', 'int', 'float', 'date', 'boolean', 'ObjectId'];
    types.forEach(type => {
        const option = document.createElement('option');
        option.value = type;
        option.textContent = type;
        if (type === (typeof currentValue === 'boolean' ? 'boolean' : inputField.type)) {
            option.selected = true;
        }
        typeSelect.appendChild(option);
    });

    typeSelect.onchange = () => {
        const selectedType = typeSelect.value;
        if (selectedType === 'boolean') {
            inputField.type = 'checkbox';
            inputField.checked = false;
        } else if (selectedType === 'ObjectId') {
            inputField.type = 'text';
            inputField.value = '';
        } else if (selectedType === 'int') {
            inputField.type = 'number';
            inputField.step = '';
            inputField.value = Math.floor(inputField.value);
        } else if (selectedType === 'float') {
            inputField.type = 'number';
            inputField.step = 'any';
            inputField.value = parseFloat(inputField.value);
        } else if (selectedType === 'date') {
            inputField.type = 'date';
            inputField.value = currentValue ? new Date(currentValue).toISOString().split('T')[0] : '';
        } else {
            inputField.type = selectedType;
            inputField.value = currentValue;
        }
    };

    const saveBtn = document.createElement('button');
    saveBtn.textContent = 'Save';
    saveBtn.classList.add('save-btn');
    saveBtn.onclick = () => updateField(collectionName, documentId, fieldName, inputField.type != "checkbox" ? inputField.value : inputField.checked, typeSelect.value);

    fieldDiv.innerHTML = `<strong>${fieldName}:</strong> `;
    fieldDiv.appendChild(inputField);
    fieldDiv.appendChild(typeSelect);
    fieldDiv.appendChild(saveBtn);
}

function updateField(collectionName, documentId, fieldName, newValue, newType) {
    if (newType === 'boolean') {
        newValue = Boolean(newValue);
    } else if (newType === 'ObjectId') {
        newValue = {
            $oid: newValue
        };
    } else if (newType === 'int') {
        newValue = parseInt(newValue);
    } else if (newType === 'float') {
        newValue = parseFloat(newValue);
    } else if (newType === 'date') {
        newValue = new Date(newValue);
    }

    fetch(`${apiUrl}/documents/${collectionName}/${fieldName}/${documentId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                "new_value": newValue,
                "new_type": newType
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                alert(data.message);
                fetchCollectionDetails(collectionName);
            } else {
                alert(data.error);
            }
        })
        .catch(error => console.error('Error updating field:', error));
}

async function renameField(collectionName, documentId, oldFieldName) {
    const newFieldName = prompt(`Enter new name for field "${oldFieldName}":`);
    if (!newFieldName || newFieldName === oldFieldName) return;

    const response = await fetch(`${apiUrl}/fields/${collectionName}/${oldFieldName}/${newFieldName}/${documentId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        }
    });

    if (response.ok) {
        alert(`Field "${oldFieldName}" renamed to "${newFieldName}".`);
        fetchCollectionDetails(collectionName);
    } else {
        const errorData = await response.json();
        alert(`Error renaming field: ${errorData.error}`);
    }
}

async function deleteField(collectionName, documentId, fieldName) {
    const approve = confirm("ви дійсно хочете видалити це поле з документа?");
    if (approve) {
        const response = await fetch(`${apiUrl}/fields/${collectionName}/${fieldName}/${documentId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                "collectionName": collectionName,
                "documentId": documentId,
                "fieldName": fieldName
            })
        });

        if (response.ok) {
            alert(`Field "${fieldName}" removed.`);
            fetchCollectionDetails(collectionName);
        } else {
            const errorData = await response.json();
            alert(`Error deleting field: ${errorData.error}`);
        }
    }
}

document.getElementById('add-document-form').onsubmit = function (event) {
    event.preventDefault();
    const collectionName = document.getElementById('collection-name').value;
    const documentData = JSON.parse(document.getElementById('document-data').value);

    fetch(`${apiUrl}/collection/${collectionName}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(documentData)
        })
        .then(response => response.json())
        .then(data => alert(data.message || 'Document added successfully!'))
        .catch(error => console.error('Error adding document:', error));
};


function hideElementsBasedOnRole() {
    const roles = ['owner', 'admin', 'operator', "user"];
    for (let i = 0; i < roles.length; i++) {
        const elements = document.querySelectorAll(`.${roles[i]}-only`);
        elements.forEach(element => {
            element.style.display = 'none';
        });
    }
    const index = roles.indexOf(getCookie("userRole"));
    if (index === -1)
        return;
    for (let i = index; i < roles.length; i++) {
        const elements = document.querySelectorAll(`.${roles[i]}-only`);
        elements.forEach(element => {
            element.style.display = 'block';
        });
    }
}
hideElementsBasedOnRole();