import pytest
import json
from resource_planning_tool.backend.models import Person

# Test data
PERSON_VALID_PAYLOAD = {"name": "John Doe", "working_hours": 40}
PERSON_VALID_PAYLOAD_2 = {"name": "Jane Smith", "working_hours": 35}
PERSON_UPDATE_PAYLOAD = {"name": "Johnathan Doe", "working_hours": 38}
PERSON_INVALID_NAME_PAYLOAD = {"name": "", "working_hours": 40} # Empty name
PERSON_INVALID_HOURS_PAYLOAD = {"name": "Test Person", "working_hours": "invalid"} # Invalid hours type

def test_create_person_success(client, db_session):
    """Test successful person creation."""
    response = client.post('/api/persons', json=PERSON_VALID_PAYLOAD)
    assert response.status_code == 201
    data = response.get_json()
    assert data['name'] == PERSON_VALID_PAYLOAD['name']
    assert data['working_hours'] == PERSON_VALID_PAYLOAD['working_hours']
    assert 'id' in data
    
    # Verify in DB
    person = db_session.get(Person, data['id'])
    assert person is not None
    assert person.name == PERSON_VALID_PAYLOAD['name']

def test_create_person_missing_name(client, db_session):
    """Test person creation with missing name."""
    payload = {"working_hours": 40}
    response = client.post('/api/persons', json=payload)
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'Name is required' in data['error']

def test_create_person_invalid_working_hours(client, db_session):
    """Test person creation with invalid working_hours type."""
    response = client.post('/api/persons', json=PERSON_INVALID_HOURS_PAYLOAD)
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'Working hours must be an integer' in data['error']

def test_create_person_empty_name_string(client, db_session):
    """Test person creation with empty name string."""
    payload = {"name": "   ", "working_hours": 30} # Name with only spaces
    response = client.post('/api/persons', json=payload)
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'Name must be a non-empty string' in data['error']


def test_get_persons_empty(client, db_session):
    """Test getting persons when the database is empty."""
    response = client.get('/api/persons')
    assert response.status_code == 200
    assert response.get_json() == []

def test_get_persons_multiple(client, db_session):
    """Test getting multiple persons."""
    person1_resp = client.post('/api/persons', json=PERSON_VALID_PAYLOAD).get_json()
    person2_resp = client.post('/api/persons', json=PERSON_VALID_PAYLOAD_2).get_json()

    response = client.get('/api/persons')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2
    
    # Check if the returned persons match the created ones by checking IDs
    returned_ids = {item['id'] for item in data}
    expected_ids = {person1_resp['id'], person2_resp['id']}
    assert returned_ids == expected_ids

def test_get_person_success(client, db_session):
    """Test fetching an existing person by ID."""
    create_response = client.post('/api/persons', json=PERSON_VALID_PAYLOAD)
    person_id = create_response.get_json()['id']

    response = client.get(f'/api/persons/{person_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['name'] == PERSON_VALID_PAYLOAD['name']
    assert data['id'] == person_id

def test_get_person_not_found(client, db_session):
    """Test fetching a non-existent person."""
    response = client.get('/api/persons/9999') # Assuming 9999 does not exist
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data
    assert 'Person not found' in data['error']

def test_update_person_success(client, db_session):
    """Test successful update of an existing person."""
    create_response = client.post('/api/persons', json=PERSON_VALID_PAYLOAD)
    person_id = create_response.get_json()['id']

    response = client.put(f'/api/persons/{person_id}', json=PERSON_UPDATE_PAYLOAD)
    assert response.status_code == 200
    data = response.get_json()
    assert data['name'] == PERSON_UPDATE_PAYLOAD['name']
    assert data['working_hours'] == PERSON_UPDATE_PAYLOAD['working_hours']
    
    # Verify in DB
    updated_person = db_session.get(Person, person_id)
    assert updated_person.name == PERSON_UPDATE_PAYLOAD['name']

def test_update_person_not_found(client, db_session):
    """Test updating a non-existent person."""
    response = client.put('/api/persons/9999', json=PERSON_UPDATE_PAYLOAD)
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data
    assert 'Person not found' in data['error']

def test_update_person_invalid_data(client, db_session):
    """Test updating a person with invalid data (e.g., empty name)."""
    create_response = client.post('/api/persons', json=PERSON_VALID_PAYLOAD)
    person_id = create_response.get_json()['id']

    response = client.put(f'/api/persons/{person_id}', json=PERSON_INVALID_NAME_PAYLOAD)
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'Name must be a non-empty string' in data['error']
    
    response_invalid_hours = client.put(f'/api/persons/{person_id}', json=PERSON_INVALID_HOURS_PAYLOAD)
    assert response_invalid_hours.status_code == 400
    data_invalid_hours = response_invalid_hours.get_json()
    assert 'error' in data_invalid_hours
    assert 'Working hours must be an integer or null' in data_invalid_hours['error']


def test_delete_person_success(client, db_session):
    """Test successful deletion of a person."""
    create_response = client.post('/api/persons', json=PERSON_VALID_PAYLOAD)
    person_id = create_response.get_json()['id']

    response = client.delete(f'/api/persons/{person_id}')
    assert response.status_code == 200 # API returns 200 with message
    data = response.get_json()
    assert 'message' in data
    assert 'Person deleted' in data['message']

    # Verify person is removed from the database
    deleted_person = db_session.get(Person, person_id)
    assert deleted_person is None
    
    # Also try fetching via GET to confirm 404
    get_response = client.get(f'/api/persons/{person_id}')
    assert get_response.status_code == 404


def test_delete_person_not_found(client, db_session):
    """Test deleting a non-existent person."""
    response = client.delete('/api/persons/9999')
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data
    assert 'Person not found' in data['error']
