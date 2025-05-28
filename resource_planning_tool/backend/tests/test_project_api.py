import pytest
import json
from resource_planning_tool.backend.models import Person, Project

# Test data
PROJECT_VALID_PAYLOAD_TEMPLATE = {"name": "Test Project Alpha", "budget": 10000.50}
PROJECT_UPDATE_PAYLOAD_TEMPLATE = {"name": "Test Project Alpha Updated", "budget": 12000.75}

@pytest.fixture(scope="function")
def sample_manager(client, db_session):
    """Creates a sample person to act as a project manager for tests."""
    payload = {"name": "Project Manager Test User", "working_hours": 40}
    response = client.post('/api/persons', json=payload)
    assert response.status_code == 201
    manager_data = response.get_json()
    # Ensure this person is committed to the db_session for relationship loading
    manager = db_session.get(Person, manager_data['id'])
    assert manager is not None
    return manager # Return the SQLAlchemy object

def test_create_project_success(client, db_session, sample_manager):
    """Test successful project creation."""
    payload = {**PROJECT_VALID_PAYLOAD_TEMPLATE, "project_manager_id": sample_manager.id}
    response = client.post('/api/projects', json=payload)
    assert response.status_code == 201
    data = response.get_json()
    assert data['name'] == PROJECT_VALID_PAYLOAD_TEMPLATE['name']
    assert data['project_manager_id'] == sample_manager.id
    assert data['project_manager_name'] == sample_manager.name
    assert float(data['budget']) == PROJECT_VALID_PAYLOAD_TEMPLATE['budget']
    assert 'id' in data

    project = db_session.get(Project, data['id'])
    assert project is not None
    assert project.name == PROJECT_VALID_PAYLOAD_TEMPLATE['name']

def test_create_project_missing_name(client, db_session, sample_manager):
    """Test project creation with missing name."""
    payload = {"project_manager_id": sample_manager.id, "budget": 5000}
    response = client.post('/api/projects', json=payload)
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'Name is required' in data['error']

def test_create_project_missing_manager_id(client, db_session):
    """Test project creation with missing project_manager_id."""
    payload = {"name": "Missing Manager Project", "budget": 5000}
    response = client.post('/api/projects', json=payload)
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'Project manager ID is required' in data['error']

def test_create_project_non_existent_manager(client, db_session):
    """Test project creation with a non-existent project_manager_id."""
    payload = {**PROJECT_VALID_PAYLOAD_TEMPLATE, "project_manager_id": 9999} # Assuming 9999 does not exist
    response = client.post('/api/projects', json=payload)
    assert response.status_code == 404 # Based on API implementation
    data = response.get_json()
    assert 'error' in data
    assert 'Person with ID 9999 not found' in data['error']

def test_create_project_invalid_budget(client, db_session, sample_manager):
    """Test project creation with an invalid budget type."""
    payload = {**PROJECT_VALID_PAYLOAD_TEMPLATE, "project_manager_id": sample_manager.id, "budget": "not-a-number"}
    response = client.post('/api/projects', json=payload)
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'Budget must be a valid number' in data['error']

def test_get_projects_empty(client, db_session):
    """Test getting projects when the database is empty."""
    response = client.get('/api/projects')
    assert response.status_code == 200
    assert response.get_json() == []

def test_get_projects_multiple(client, db_session, sample_manager):
    """Test getting multiple projects."""
    payload1 = {"name": "Project X", "project_manager_id": sample_manager.id, "budget": 100}
    payload2 = {"name": "Project Y", "project_manager_id": sample_manager.id, "budget": 200}
    project1_resp = client.post('/api/projects', json=payload1).get_json()
    project2_resp = client.post('/api/projects', json=payload2).get_json()

    response = client.get('/api/projects')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2
    returned_ids = {item['id'] for item in data}
    expected_ids = {project1_resp['id'], project2_resp['id']}
    assert returned_ids == expected_ids

def test_get_project_success(client, db_session, sample_manager):
    """Test fetching an existing project by ID."""
    payload = {**PROJECT_VALID_PAYLOAD_TEMPLATE, "project_manager_id": sample_manager.id}
    create_response = client.post('/api/projects', json=payload)
    project_id = create_response.get_json()['id']

    response = client.get(f'/api/projects/{project_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['name'] == PROJECT_VALID_PAYLOAD_TEMPLATE['name']
    assert data['id'] == project_id
    assert data['project_manager_name'] == sample_manager.name

def test_get_project_not_found(client, db_session):
    """Test fetching a non-existent project."""
    response = client.get('/api/projects/9999')
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data
    assert 'Project not found' in data['error']

def test_update_project_success(client, db_session, sample_manager):
    """Test successful update of an existing project."""
    payload_initial = {**PROJECT_VALID_PAYLOAD_TEMPLATE, "project_manager_id": sample_manager.id}
    create_response = client.post('/api/projects', json=payload_initial)
    project_id = create_response.get_json()['id']

    # Create another person to change manager
    other_manager_payload = {"name": "Other Manager", "working_hours": 30}
    other_manager_id = client.post('/api/persons', json=other_manager_payload).get_json()['id']
    
    update_payload = {**PROJECT_UPDATE_PAYLOAD_TEMPLATE, "project_manager_id": other_manager_id}
    response = client.put(f'/api/projects/{project_id}', json=update_payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data['name'] == PROJECT_UPDATE_PAYLOAD_TEMPLATE['name']
    assert data['project_manager_id'] == other_manager_id
    assert float(data['budget']) == PROJECT_UPDATE_PAYLOAD_TEMPLATE['budget']

    updated_project = db_session.get(Project, project_id)
    assert updated_project.name == PROJECT_UPDATE_PAYLOAD_TEMPLATE['name']
    assert updated_project.project_manager_id == other_manager_id

def test_update_project_not_found(client, db_session, sample_manager):
    """Test updating a non-existent project."""
    update_payload = {**PROJECT_UPDATE_PAYLOAD_TEMPLATE, "project_manager_id": sample_manager.id}
    response = client.put('/api/projects/9999', json=update_payload)
    assert response.status_code == 404

def test_update_project_invalid_data(client, db_session, sample_manager):
    """Test updating a project with invalid data."""
    payload_initial = {**PROJECT_VALID_PAYLOAD_TEMPLATE, "project_manager_id": sample_manager.id}
    create_response = client.post('/api/projects', json=payload_initial)
    project_id = create_response.get_json()['id']

    invalid_payload_name = {"name": "", "project_manager_id": sample_manager.id}
    response = client.put(f'/api/projects/{project_id}', json=invalid_payload_name)
    assert response.status_code == 400
    assert 'Name must be a non-empty string' in response.get_json()['error']

    invalid_payload_manager = {"name": "Valid Name", "project_manager_id": 9876} # Non-existent manager
    response = client.put(f'/api/projects/{project_id}', json=invalid_payload_manager)
    assert response.status_code == 404 # API returns 404 for non-existent manager on update
    assert 'Person with ID 9876 not found' in response.get_json()['error']


def test_delete_project_success(client, db_session, sample_manager):
    """Test successful deletion of a project."""
    payload = {**PROJECT_VALID_PAYLOAD_TEMPLATE, "project_manager_id": sample_manager.id}
    create_response = client.post('/api/projects', json=payload)
    project_id = create_response.get_json()['id']

    response = client.delete(f'/api/projects/{project_id}')
    assert response.status_code == 200
    assert 'Project deleted' in response.get_json()['message']

    deleted_project = db_session.get(Project, project_id)
    assert deleted_project is None
    
    get_response = client.get(f'/api/projects/{project_id}')
    assert get_response.status_code == 404

def test_delete_project_not_found(client, db_session):
    """Test deleting a non-existent project."""
    response = client.delete('/api/projects/9999')
    assert response.status_code == 404
    assert 'Project not found' in response.get_json()['error']
