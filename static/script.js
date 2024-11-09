const apiUrl = 'http://127.0.0.1:5000/api';

async function fetchCollections() {
    const response = await fetch('/api/collections');
    const collections = await response.json();
    const collectionList = document.getElementById('collection-list');
    collectionList.innerHTML = ''; // Clear list before rendering

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

                for (const [key, value] of Object.entries(doc)) {
                    const fieldDiv = document.createElement('div');
                    if (key !== '_id') {

                        fieldDiv.classList.add('field-container');
                        fieldDiv.setAttribute('data-field-name', key); // Set unique data attribute

                        const renameBtn = document.createElement('button');
                        renameBtn.textContent = 'Rename';
                        renameBtn.classList.add('rename-btn');
                        renameBtn.onclick = () => renameField(collectionName, doc._id, key);

                        const removeBtn = document.createElement('button');
                        removeBtn.textContent = 'Remove';
                        removeBtn.classList.add('remove-btn');
                        removeBtn.onclick = () => deleteField(collectionName, doc._id, key);

                        const editBtn = document.createElement('button');
                        editBtn.textContent = 'Edit';
                        editBtn.classList.add('edit-btn');
                        editBtn.onclick = () => showEditFieldInput(collectionName, doc._id, key, value);

                        fieldDiv.appendChild(renameBtn);
                        fieldDiv.appendChild(removeBtn);
                        fieldDiv.appendChild(editBtn);

                        const fieldContent = document.createElement('p');
                        fieldContent.innerHTML = `<strong>${key}:</strong> ${value} <span class="field-type">Type: ${typeof value}</span>`;
                        fieldDiv.appendChild(fieldContent);
                        card.appendChild(fieldDiv);
                    }
                }
                documentCardsContainer.appendChild(card);
            });
        })
        .catch(error => console.error('Error fetching collection details:', error));
}

function showEditFieldInput(collectionName, documentId, fieldName, currentValue) {
    // Select the field container using data attribute
    const fieldDiv = document.querySelector(`.field-container[data-field-name="${fieldName}"]`);
    if (!fieldDiv) return; // Exit if the field container is not found

    // Create an input field with the initial type
    const inputField = document.createElement('input');
    inputField.classList.add('edit-input');

    // Handle different types for the input field
    if (typeof currentValue === 'string') {
        inputField.type = 'text';
        inputField.value = currentValue;
    } else if (typeof currentValue === 'number') {
        // Check if it's an integer or float
        if (Number.isInteger(currentValue)) {
            inputField.type = 'number';
            inputField.value = currentValue;
        } else {
            inputField.type = 'number';
            inputField.step = 'any';  // Allow decimals for float
            inputField.value = currentValue;
        }
    } else if (Object.prototype.toString.call(currentValue) === '[object Date]') {
        inputField.type = 'date';
        inputField.value = new Date(currentValue).toISOString().split('T')[0]; // Format as YYYY-MM-DD
    } else if (typeof currentValue === 'boolean') {
        inputField.type = 'checkbox';
        inputField.checked = currentValue;
    } else if (currentValue && currentValue.$oid) {
        // Handle ObjectId (assuming it's an object with an $oid field)
        inputField.type = 'text';
        inputField.value = currentValue.$oid; // This will display the ObjectId string value
    } else {
        inputField.type = 'text'; // Default to text for other types
        inputField.value = currentValue;
    }

    // Create a dropdown for selecting the type
    const typeSelect = document.createElement('select');
    const types = ['text', 'number (int)', 'number (float)', 'date', 'boolean', 'ObjectId'];
    types.forEach(type => {
        const option = document.createElement('option');
        option.value = type;
        option.textContent = type;
        if (type === (typeof currentValue === 'boolean' ? 'boolean' : inputField.type)) {
            option.selected = true;
        }
        typeSelect.appendChild(option);
    });

    // Update input field type when a new type is selected
    typeSelect.onchange = () => {
        const selectedType = typeSelect.value;
        if (selectedType === 'boolean') {
            inputField.type = 'checkbox';
            inputField.checked = false; // Default value for checkbox
        } else if (selectedType === 'ObjectId') {
            inputField.type = 'text';
            inputField.value = ''; // Empty for new ObjectId
        } else if (selectedType === 'number (int)') {
            inputField.type = 'number';
            inputField.step = ''; // Remove decimal step for integer
            inputField.value = Math.floor(inputField.value); // Round to integer if needed
        } else if (selectedType === 'number (float)') {
            inputField.type = 'number';
            inputField.step = 'any'; // Allow decimals for float
            inputField.value = parseFloat(inputField.value); // Ensure it's float
        } else if (selectedType === 'date') {
            inputField.type = 'date';
            inputField.value = currentValue ? new Date(currentValue).toISOString().split('T')[0] : ''; // Format as YYYY-MM-DD
        } else {
            inputField.type = selectedType;
            inputField.value = currentValue;
        }
    };

    // Create a save button
    const saveBtn = document.createElement('button');
    saveBtn.textContent = 'Save';
    saveBtn.classList.add('save-btn');
    saveBtn.onclick = () => updateField(collectionName, documentId, fieldName, inputField.value, typeSelect.value);

    // Clear the existing content and add the input field, type selector, and save button
    fieldDiv.innerHTML = `<strong>${fieldName}:</strong> `;
    fieldDiv.appendChild(inputField);
    fieldDiv.appendChild(typeSelect);
    fieldDiv.appendChild(saveBtn);
}

function updateField(collectionName, documentId, fieldName, newValue, newType) {
    if (newType === 'boolean') {
        newValue = Boolean(newValue); // Ensure boolean conversion
    } else if (newType === 'ObjectId') {
        newValue = { $oid: newValue }; // Handle ObjectId format
    } else if (newType === 'number (int)') {
        newValue = parseInt(newValue); // Ensure the value is an integer
    } else if (newType === 'number (float)') {
        newValue = parseFloat(newValue); // Ensure the value is a float
    } else if (newType === 'date') {
        // Convert date string to Date object
        newValue = new Date(newValue); // This ensures that it's a valid Date object
    }

    fetch(`${apiUrl}/documents/${collectionName}/${fieldName}/${documentId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ new_value: newValue, new_type: newType })
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            alert(data.message);
            fetchCollectionDetails(collectionName);  // Refresh the details
        } else {
            alert(data.error);
        }
    })
    .catch(error => console.error('Error updating field:', error));
}

// Function to rename a field
async function renameField(collectionName, documentId, oldFieldName) {
    console.log(collectionName)
    console.log(documentId)
    console.log(oldFieldName)
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

// Function to delete a field
async function deleteField(collectionName, documentId, fieldName) {
    const approve = confirm("ви дійнсо хочете видалити це поле з документа?");
    if (approve) {
        const response = await fetch(`${apiUrl}/fields/${collectionName}/${fieldName}/${documentId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                collectionName: collectionName,
                documentId: documentId,
                fieldName: fieldName
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