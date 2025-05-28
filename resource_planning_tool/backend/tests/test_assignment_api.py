import pytest
import json
from datetime import date, timedelta
from resource_planning_tool.backend.models import Person, Project, Assignment

# Test data
ASSIGNMENT_VALID_PAYLOAD_TEMPLATE = {"assigned_hours": 20, 
                                     "timeline_start": date.today().isoformat(), 
                                     "timeline_end": (date.today() + timedelta(days=10)).isoformat()}

@pytest.fixture(scope="function")
def sample_person_1(client, db_session):
    """Creates a sample person for assignment tests."""
    payload = {"name": "Assignee Person One", "working_hours": 40}
    response = client.post('/api/persons', json=payload)
    assert response.status_code == 201
    person_data = response.get_json()
    person = db_session.get(Person, person_data['id'])
    assert person is not None
    return person

@pytest.fixture(scope="function")
def sample_person_2(client, db_session):
    """Creates another sample person (e.g., a project manager)."""
    payload = {"name": "Project Manager AssignTest", "working_hours": 40}
    response = client.post('/api/persons', json=payload)
    assert response.status_code == 201
    pm_data = response.get_json()
    pm = db_session.get(Person, pm_data['id'])
    assert pm is not None
    return pm

@pytest.fixture(scope="function")
def sample_project(client, db_session, sample_person_2): # sample_person_2 is the PM
    """Creates a sample project for assignment tests."""
    payload = {"name": "Assignment Test Project", "project_manager_id": sample_person_2.id, "budget": 5000}
    response = client.post('/api/projects', json=payload)
    assert response.status_code == 201
    project_data = response.get_json()
    project = db_session.get(Project, project_data['id'])
    assert project is not None
    return project

# --- Assignment CRUD Tests ---

def test_create_assignment_success(client, db_session, sample_project, sample_person_1):
    """Test successful assignment creation."""
    payload = {**ASSIGNMENT_VALID_PAYLOAD_TEMPLATE, 
               "project_id": sample_project.id, 
               "person_id": sample_person_1.id}
    response = client.post('/api/assignments', json=payload)
    assert response.status_code == 201
    data = response.get_json()
    assert data['project_id'] == sample_project.id
    assert data['person_id'] == sample_person_1.id
    assert data['assigned_hours'] == ASSIGNMENT_VALID_PAYLOAD_TEMPLATE['assigned_hours']
    assert data['timeline_start'] == ASSIGNMENT_VALID_PAYLOAD_TEMPLATE['timeline_start']
    
    assignment = db_session.get(Assignment, data['id'])
    assert assignment is not None
    assert assignment.project.name == sample_project.name # Check relationship loading

def test_create_assignment_non_existent_project(client, db_session, sample_person_1):
    """Test assignment creation with non-existent project_id."""
    payload = {**ASSIGNMENT_VALID_PAYLOAD_TEMPLATE, "project_id": 9999, "person_id": sample_person_1.id}
    response = client.post('/api/assignments', json=payload)
    assert response.status_code == 404 # API returns 404 if project not found
    assert 'Project with ID 9999 not found' in response.get_json()['error']

def test_create_assignment_non_existent_person(client, db_session, sample_project):
    """Test assignment creation with non-existent person_id."""
    payload = {**ASSIGNMENT_VALID_PAYLOAD_TEMPLATE, "project_id": sample_project.id, "person_id": 9998}
    response = client.post('/api/assignments', json=payload)
    assert response.status_code == 404 # API returns 404 if person not found
    assert 'Person with ID 9998 not found' in response.get_json()['error']

def test_create_assignment_invalid_hours(client, db_session, sample_project, sample_person_1):
    """Test assignment creation with invalid assigned_hours."""
    payload = {**ASSIGNMENT_VALID_PAYLOAD_TEMPLATE, 
               "project_id": sample_project.id, 
               "person_id": sample_person_1.id,
               "assigned_hours": -5} # Invalid hours
    response = client.post('/api/assignments', json=payload)
    assert response.status_code == 400
    assert 'assigned_hours must be a positive integer' in response.get_json()['error']

def test_create_assignment_invalid_dates(client, db_session, sample_project, sample_person_1):
    """Test assignment creation with invalid date format or logic."""
    # Invalid date format
    payload_format = {**ASSIGNMENT_VALID_PAYLOAD_TEMPLATE, 
                      "project_id": sample_project.id, 
                      "person_id": sample_person_1.id,
                      "timeline_start": "2023/01/01"}
    response_format = client.post('/api/assignments', json=payload_format)
    assert response_format.status_code == 400
    assert 'Invalid date format' in response_format.get_json()['error']

    # timeline_start after timeline_end
    payload_logic = {**ASSIGNMENT_VALID_PAYLOAD_TEMPLATE, 
                     "project_id": sample_project.id, 
                     "person_id": sample_person_1.id,
                     "timeline_start": (date.today() + timedelta(days=5)).isoformat(),
                     "timeline_end": date.today().isoformat()}
    response_logic = client.post('/api/assignments', json=payload_logic)
    assert response_logic.status_code == 400
    assert 'timeline_start cannot be after timeline_end' in response_logic.get_json()['error']

def test_get_assignments_for_project(client, db_session, sample_project, sample_person_1):
    """Test fetching assignments for a specific project."""
    # Create an assignment for the project
    assign_payload = {**ASSIGNMENT_VALID_PAYLOAD_TEMPLATE, 
                      "project_id": sample_project.id, 
                      "person_id": sample_person_1.id}
    client.post('/api/assignments', json=assign_payload)

    response = client.get(f'/api/projects/{sample_project.id}/assignments')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['project_id'] == sample_project.id
    assert data[0]['person_id'] == sample_person_1.id

def test_get_assignments_for_project_none(client, db_session, sample_project):
    """Test fetching assignments for a project with no assignments."""
    response = client.get(f'/api/projects/{sample_project.id}/assignments')
    assert response.status_code == 200
    assert response.get_json() == []

def test_get_assignments_for_project_not_found(client, db_session):
    """Test fetching assignments for a non-existent project."""
    response = client.get('/api/projects/9999/assignments')
    assert response.status_code == 404
    assert 'Project not found' in response.get_json()['error']

def test_get_assignments_for_person(client, db_session, sample_project, sample_person_1):
    """Test fetching assignments for a specific person."""
    assign_payload = {**ASSIGNMENT_VALID_PAYLOAD_TEMPLATE, 
                      "project_id": sample_project.id, 
                      "person_id": sample_person_1.id}
    client.post('/api/assignments', json=assign_payload)

    response = client.get(f'/api/persons/{sample_person_1.id}/assignments')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['person_id'] == sample_person_1.id
    assert data[0]['project_id'] == sample_project.id

def test_update_assignment_success(client, db_session, sample_project, sample_person_1):
    """Test successful update of an assignment."""
    assign_payload = {**ASSIGNMENT_VALID_PAYLOAD_TEMPLATE, 
                      "project_id": sample_project.id, 
                      "person_id": sample_person_1.id}
    create_resp = client.post('/api/assignments', json=assign_payload)
    assignment_id = create_resp.get_json()['id']

    update_payload = {"assigned_hours": 30, "timeline_end": (date.today() + timedelta(days=20)).isoformat()}
    response = client.put(f'/api/assignments/{assignment_id}', json=update_payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data['assigned_hours'] == 30
    assert data['timeline_end'] == update_payload['timeline_end']
    
    updated_assignment = db_session.get(Assignment, assignment_id)
    assert updated_assignment.assigned_hours == 30

def test_delete_assignment_success(client, db_session, sample_project, sample_person_1):
    """Test successful deletion of an assignment."""
    assign_payload = {**ASSIGNMENT_VALID_PAYLOAD_TEMPLATE, 
                      "project_id": sample_project.id, 
                      "person_id": sample_person_1.id}
    create_resp = client.post('/api/assignments', json=assign_payload)
    assignment_id = create_resp.get_json()['id']

    response = client.delete(f'/api/assignments/{assignment_id}')
    assert response.status_code == 200
    assert 'Assignment deleted' in response.get_json()['message']

    deleted_assignment = db_session.get(Assignment, assignment_id)
    assert deleted_assignment is None

# --- Project Manager View Test ---

def test_get_manager_projects_with_assignments(client, db_session, sample_person_1, sample_person_2, sample_project):
    """Test the project manager view endpoint."""
    # sample_person_2 is the manager of sample_project
    # Assign sample_person_1 to sample_project
    assign_payload = {**ASSIGNMENT_VALID_PAYLOAD_TEMPLATE, 
                      "project_id": sample_project.id, 
                      "person_id": sample_person_1.id}
    client.post('/api/assignments', json=assign_payload)

    # Create another project managed by sample_person_2, but with no assignments
    project2_payload = {"name": "Empty Project PM2", "project_manager_id": sample_person_2.id, "budget": 100}
    client.post('/api/projects', json=project2_payload)

    response = client.get(f'/api/project_manager/{sample_person_2.id}/projects')
    assert response.status_code == 200
    data = response.get_json()
    
    assert len(data) == 2 # sample_project and project2
    
    found_sample_project = False
    for proj_data in data:
        if proj_data['id'] == sample_project.id:
            found_sample_project = True
            assert proj_data['name'] == sample_project.name
            assert 'assignments' in proj_data
            assert len(proj_data['assignments']) == 1
            assert proj_data['assignments'][0]['person_id'] == sample_person_1.id
            assert proj_data['assignments'][0]['assigned_hours'] == ASSIGNMENT_VALID_PAYLOAD_TEMPLATE['assigned_hours']
        elif proj_data['name'] == "Empty Project PM2":
             assert 'assignments' in proj_data
             assert len(proj_data['assignments']) == 0


    assert found_sample_project, "The main sample project with assignments was not found in the manager's view."

def test_get_manager_projects_no_projects(client, db_session, sample_person_1):
    """Test project manager view when the manager has no projects."""
    # sample_person_1 is not a manager of any projects initially
    response = client.get(f'/api/project_manager/{sample_person_1.id}/projects')
    assert response.status_code == 200
    assert response.get_json() == []

def test_get_manager_projects_manager_not_found(client, db_session):
    """Test project manager view with a non-existent manager ID."""
    response = client.get('/api/project_manager/9999/projects')
    assert response.status_code == 404
    assert 'Project manager (Person) not found' in response.get_json()['error']
