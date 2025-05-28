"""
Main Flask application file for the Resource Planning Tool backend API.

This file sets up the Flask application, configures CORS, initializes SQLAlchemy
for database interaction, and defines all the API endpoints for managing
Persons, Projects, and Assignments. It also includes a CLI command for
database initialization.
"""
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from .models import db, Person, Project, Assignment # Ensure models are imported
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)

# Configure CORS: Allow requests from the Angular frontend (typically http://localhost:4200)
# to access API endpoints (prefixed with /api/).
CORS(app, resources={r"/api/*": {"origins": "http://localhost:4200"}})

# Configure the SQLite database
# The database file (resource_planner.db) will be created in the same directory as this app.py file.
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'resource_planner.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Disable modification tracking to save resources

# Initialize SQLAlchemy with the Flask app instance. This connects SQLAlchemy to the app.
db.init_app(app)

@app.route('/api/health')
def health():
    """
    Health check endpoint.
    
    Returns:
        JSON: A JSON response with status 'OK' and HTTP status code 200.
    """
    return jsonify({'status': 'OK'}), 200

# --- Person Management Endpoints ---

@app.route('/api/persons', methods=['POST'])
def create_person():
    """
    Creates a new person.
    Expects a JSON body with 'name' (required) and 'working_hours' (optional).
    
    Returns:
        JSON: The created person object with HTTP status code 201 on success.
        JSON: An error message with HTTP status code 400 for invalid input.
        JSON: An error message with HTTP status code 500 for server errors.
    """
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({'error': 'Name is required'}), 400
    
    name = data.get('name')
    working_hours = data.get('working_hours') # Optional

    # Validate input data types and constraints
    if not isinstance(name, str) or len(name.strip()) == 0:
        return jsonify({'error': 'Name must be a non-empty string'}), 400
    if working_hours is not None and not isinstance(working_hours, int):
        return jsonify({'error': 'Working hours must be an integer'}), 400

    try:
        # Create new Person instance
        person = Person(name=name.strip(), working_hours=working_hours)
        db.session.add(person)
        db.session.commit()
        return jsonify(person.to_dict()), 201 # Return created person and 201 status
    except Exception as e:
        db.session.rollback() # Rollback in case of error
        app.logger.error(f"Error creating person: {e}") # Log the error
        return jsonify({'error': 'Could not create person', 'message': str(e)}), 500

@app.route('/api/persons', methods=['GET'])
def get_persons():
    """
    Retrieves a list of all persons.
    
    Returns:
        JSON: A list of person objects with HTTP status code 200.
        JSON: An error message with HTTP status code 500 for server errors.
    """
    try:
        persons = Person.query.all()
        return jsonify([person.to_dict() for person in persons]), 200
    except Exception as e:
        app.logger.error(f"Error retrieving persons: {e}")
        return jsonify({'error': 'Could not retrieve persons', 'message': str(e)}), 500

@app.route('/api/persons/<int:person_id>', methods=['GET'])
def get_person(person_id):
    """
    Retrieves a single person by their ID.
    
    Args:
        person_id (int): The unique ID of the person.
        
    Returns:
        JSON: The person object with HTTP status code 200 if found.
        JSON: An error message with HTTP status code 404 if not found.
        JSON: An error message with HTTP status code 500 for server errors.
    """
    try:
        # db.session.get() is preferred for fetching by primary key
        person = db.session.get(Person, person_id) 
        if person:
            return jsonify(person.to_dict()), 200
        else:
            return jsonify({'error': 'Person not found'}), 404
    except Exception as e:
        app.logger.error(f"Error retrieving person {person_id}: {e}")
        return jsonify({'error': 'Could not retrieve person', 'message': str(e)}), 500

@app.route('/api/persons/<int:person_id>', methods=['PUT'])
def update_person(person_id):
    """
    Updates an existing person by their ID.
    Expects a JSON body with 'name' and/or 'working_hours'.
    
    Args:
        person_id (int): The unique ID of the person to update.
        
    Returns:
        JSON: The updated person object with HTTP status code 200.
        JSON: An error message with HTTP status code 404 if not found.
        JSON: An error message with HTTP status code 400 for invalid input.
        JSON: An error message with HTTP status code 500 for server errors.
    """
    try:
        person = db.session.get(Person, person_id)
        if not person:
            return jsonify({'error': 'Person not found'}), 404

        data = request.get_json()
        if not data: # Check if any data is sent
            return jsonify({'error': 'No data provided for update'}), 400

        # Update fields if provided in the request, otherwise keep existing values
        name = data.get('name', person.name)
        working_hours = data.get('working_hours', person.working_hours)

        # Validate new values
        if not isinstance(name, str) or len(name.strip()) == 0:
            return jsonify({'error': 'Name must be a non-empty string'}), 400
        # Allow working_hours to be explicitly set to null (None in Python)
        if working_hours is not None and not isinstance(working_hours, int):
            return jsonify({'error': 'Working hours must be an integer or null'}), 400
        
        person.name = name.strip()
        person.working_hours = working_hours
        
        db.session.commit()
        return jsonify(person.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating person {person_id}: {e}")
        return jsonify({'error': 'Could not update person', 'message': str(e)}), 500

@app.route('/api/persons/<int:person_id>', methods=['DELETE'])
def delete_person(person_id):
    """
    Deletes a person by their ID.
    
    Args:
        person_id (int): The unique ID of the person to delete.
        
    Returns:
        JSON: A success message with HTTP status code 200.
        JSON: An error message with HTTP status code 404 if not found.
        JSON: An error message with HTTP status code 500 for server errors.
    """
    try:
        person = db.session.get(Person, person_id)
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        # Future consideration: Check for dependencies (e.g., if person manages projects or has assignments)
        # For now, direct deletion is allowed.
        # if person.managed_projects.count() > 0: # Using .count() for dynamic relationships
        #    return jsonify({'error': 'Cannot delete person: is a project manager for existing projects'}), 400
        # if person.assignments.count() > 0:
        #    return jsonify({'error': 'Cannot delete person: has existing assignments'}), 400

        db.session.delete(person)
        db.session.commit()
        return jsonify({'message': 'Person deleted'}), 200 # Standard to return 204 No Content on successful DELETE
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting person {person_id}: {e}")
        return jsonify({'error': 'Could not delete person', 'message': str(e)}), 500

# --- Project Management Endpoints ---

@app.route('/api/projects', methods=['POST'])
def create_project():
    """
    Creates a new project.
    Expects JSON body with 'name', 'project_manager_id' (required), and 'budget' (optional).
    
    Returns:
        JSON: The created project object with HTTP status code 201.
        JSON: Error messages for invalid input (400), non-existent manager (404), or server errors (500).
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No input data provided'}), 400

    name = data.get('name')
    project_manager_id = data.get('project_manager_id')
    budget = data.get('budget') # Optional

    # Validate required fields and types
    if not name or not isinstance(name, str) or len(name.strip()) == 0:
        return jsonify({'error': 'Name is required and must be a non-empty string'}), 400
    if project_manager_id is None or not isinstance(project_manager_id, int):
        return jsonify({'error': 'Project manager ID is required and must be an integer'}), 400

    # Check if the specified project manager exists
    manager = db.session.get(Person, project_manager_id)
    if not manager:
        return jsonify({'error': f'Person with ID {project_manager_id} not found as project manager'}), 404

    # Validate budget if provided
    if budget is not None:
        try:
            # Attempt to convert to float for validation; actual storage is Numeric
            budget = float(budget) 
        except ValueError:
            return jsonify({'error': 'Budget must be a valid number'}), 400
    
    try:
        project = Project(
            name=name.strip(), 
            project_manager_id=project_manager_id, 
            budget=budget # SQLAlchemy handles Numeric conversion
        )
        db.session.add(project)
        db.session.commit()
        return jsonify(project.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating project: {e}")
        return jsonify({'error': 'Could not create project', 'message': str(e)}), 500

@app.route('/api/projects', methods=['GET'])
def get_projects():
    """
    Retrieves a list of all projects.
    
    Returns:
        JSON: A list of project objects with HTTP status code 200.
        JSON: An error message with HTTP status code 500 for server errors.
    """
    try:
        projects = Project.query.all()
        return jsonify([project.to_dict() for project in projects]), 200
    except Exception as e:
        app.logger.error(f"Error retrieving projects: {e}")
        return jsonify({'error': 'Could not retrieve projects', 'message': str(e)}), 500

@app.route('/api/projects/<int:project_id>', methods=['GET'])
def get_project(project_id):
    """
    Retrieves a single project by its ID.
    
    Args:
        project_id (int): The unique ID of the project.
        
    Returns:
        JSON: The project object with HTTP status code 200 if found.
        JSON: An error message with HTTP status code 404 if not found.
        JSON: An error message with HTTP status code 500 for server errors.
    """
    try:
        project = db.session.get(Project, project_id)
        if project:
            return jsonify(project.to_dict()), 200
        else:
            return jsonify({'error': 'Project not found'}), 404
    except Exception as e:
        app.logger.error(f"Error retrieving project {project_id}: {e}")
        return jsonify({'error': 'Could not retrieve project', 'message': str(e)}), 500

@app.route('/api/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    """
    Updates an existing project by its ID.
    Expects JSON body with 'name', 'project_manager_id', and/or 'budget'.
    
    Args:
        project_id (int): The unique ID of the project to update.
        
    Returns:
        JSON: The updated project object with HTTP status code 200.
        JSON: Error messages for not found (404), invalid input (400), or server errors (500).
    """
    try:
        project = db.session.get(Project, project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided for update'}), 400

        name = data.get('name', project.name)
        project_manager_id = data.get('project_manager_id', project.project_manager_id)
        budget = data.get('budget', project.budget) # Keep original budget if not provided
        
        # Validate new values
        if not name or not isinstance(name, str) or len(name.strip()) == 0:
            return jsonify({'error': 'Name must be a non-empty string'}), 400
        if project_manager_id is None or not isinstance(project_manager_id, int): # Must always be an int
            return jsonify({'error': 'Project manager ID must be an integer'}), 400

        # If project_manager_id is being changed, verify the new manager exists
        if project_manager_id != project.project_manager_id:
            manager = db.session.get(Person, project_manager_id)
            if not manager:
                return jsonify({'error': f'Person with ID {project_manager_id} not found as project manager'}), 404

        if budget is not None: # Allow budget to be set to null (None) by not providing it or explicitly setting if API allows
            try:
                budget = float(budget) # Validate if provided
            except ValueError:
                return jsonify({'error': 'Budget must be a valid number'}), 400
        
        project.name = name.strip()
        project.project_manager_id = project_manager_id
        project.budget = budget # Assign validated budget
        
        db.session.commit()
        return jsonify(project.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating project {project_id}: {e}")
        return jsonify({'error': 'Could not update project', 'message': str(e)}), 500

@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    """
    Deletes a project by its ID.
    
    Args:
        project_id (int): The unique ID of the project to delete.
        
    Returns:
        JSON: A success message with HTTP status code 200.
        JSON: An error message with HTTP status code 404 if not found.
        JSON: An error message with HTTP status code 500 for server errors.
    """
    try:
        project = db.session.get(Project, project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        # Future consideration: Check for active assignments.
        # if project.assignments.count() > 0:
        #     return jsonify({'error': 'Cannot delete project: has active assignments'}), 400

        db.session.delete(project)
        db.session.commit()
        return jsonify({'message': 'Project deleted'}), 200
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting project {project_id}: {e}")
        return jsonify({'error': 'Could not delete project', 'message': str(e)}), 500

# --- Assignment Management Endpoints ---

@app.route('/api/assignments', methods=['POST'])
def create_assignment():
    """
    Creates a new assignment, linking a person to a project.
    Expects JSON body with 'project_id', 'person_id', 'assigned_hours', 
    'timeline_start' (YYYY-MM-DD), and 'timeline_end' (YYYY-MM-DD).
    
    Returns:
        JSON: The created assignment object with HTTP status code 201.
        JSON: Error messages for invalid input (400), non-existent project/person (404), or server errors (500).
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No input data provided'}), 400

    # Extract required fields
    project_id = data.get('project_id')
    person_id = data.get('person_id')
    assigned_hours = data.get('assigned_hours')
    timeline_start_str = data.get('timeline_start')
    timeline_end_str = data.get('timeline_end')

    # Validate presence of all required fields
    if not all([isinstance(project_id, int), isinstance(person_id, int), 
                isinstance(assigned_hours, int), timeline_start_str, timeline_end_str]):
        return jsonify({'error': 'Missing or invalid type for one or more required fields: project_id (int), person_id (int), assigned_hours (int), timeline_start (str), timeline_end (str)'}), 400

    # Validate positive assigned_hours
    if assigned_hours <= 0:
        return jsonify({'error': 'assigned_hours must be a positive integer'}), 400

    # Validate existence of linked project and person
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({'error': f'Project with ID {project_id} not found'}), 404
    person = db.session.get(Person, person_id)
    if not person:
        return jsonify({'error': f'Person with ID {person_id} not found'}), 404

    # Validate and parse date strings
    try:
        timeline_start = datetime.strptime(timeline_start_str, '%Y-%m-%d').date()
        timeline_end = datetime.strptime(timeline_end_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    if timeline_start > timeline_end:
        return jsonify({'error': 'timeline_start cannot be after timeline_end'}), 400

    try:
        assignment = Assignment(
            project_id=project_id,
            person_id=person_id,
            assigned_hours=assigned_hours,
            timeline_start=timeline_start,
            timeline_end=timeline_end
        )
        db.session.add(assignment)
        db.session.commit()
        return jsonify(assignment.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating assignment: {e}")
        return jsonify({'error': 'Could not create assignment', 'message': str(e)}), 500

@app.route('/api/projects/<int:project_id>/assignments', methods=['GET'])
def get_assignments_for_project(project_id):
    """
    Retrieves all assignments for a specific project.
    
    Args:
        project_id (int): The ID of the project.
        
    Returns:
        JSON: A list of assignment objects for the project, status 200.
        JSON: Error 404 if project not found.
    """
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    # Assuming 'assignments' is a dynamic relationship on Project model
    assignments = project.assignments.all() 
    return jsonify([assignment.to_dict() for assignment in assignments]), 200

@app.route('/api/persons/<int:person_id>/assignments', methods=['GET'])
def get_assignments_for_person(person_id):
    """
    Retrieves all assignments for a specific person.
    
    Args:
        person_id (int): The ID of the person.
        
    Returns:
        JSON: A list of assignment objects for the person, status 200.
        JSON: Error 404 if person not found.
    """
    person = db.session.get(Person, person_id)
    if not person:
        return jsonify({'error': 'Person not found'}), 404
        
    # Assuming 'assignments' is a dynamic relationship on Person model
    assignments = person.assignments.all()
    return jsonify([assignment.to_dict() for assignment in assignments]), 200

@app.route('/api/assignments/<int:assignment_id>', methods=['PUT'])
def update_assignment(assignment_id):
    """
    Updates an existing assignment by its ID.
    Expects JSON body with fields to update (e.g., 'assigned_hours', 'timeline_start', 'timeline_end').
    
    Args:
        assignment_id (int): The ID of the assignment to update.
        
    Returns:
        JSON: The updated assignment object, status 200.
        JSON: Error 404 if assignment not found, 400 for invalid data.
    """
    assignment = db.session.get(Assignment, assignment_id)
    if not assignment:
        return jsonify({'error': 'Assignment not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No input data provided'}), 400

    # Update fields, defaulting to existing values if not provided
    # Note: project_id and person_id are typically not changed in an update,
    # if they need to change, it's often a new assignment.
    # However, if allowed, validation for their existence would be needed.
    assigned_hours = data.get('assigned_hours', assignment.assigned_hours)
    timeline_start_str = data.get('timeline_start', assignment.timeline_start.isoformat() if assignment.timeline_start else None)
    timeline_end_str = data.get('timeline_end', assignment.timeline_end.isoformat() if assignment.timeline_end else None)

    # Validations
    if not isinstance(assigned_hours, int) or assigned_hours <= 0:
        return jsonify({'error': 'assigned_hours must be a positive integer'}), 400
    
    # Validate and parse dates if provided
    try:
        timeline_start = datetime.strptime(timeline_start_str, '%Y-%m-%d').date() if timeline_start_str else assignment.timeline_start
        timeline_end = datetime.strptime(timeline_end_str, '%Y-%m-%d').date() if timeline_end_str else assignment.timeline_end
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    if timeline_start and timeline_end and timeline_start > timeline_end: # Check only if both are present
        return jsonify({'error': 'timeline_start cannot be after timeline_end'}), 400
    
    assignment.assigned_hours = assigned_hours
    assignment.timeline_start = timeline_start
    assignment.timeline_end = timeline_end

    try:
        db.session.commit()
        return jsonify(assignment.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating assignment {assignment_id}: {e}")
        return jsonify({'error': 'Could not update assignment', 'message': str(e)}), 500

@app.route('/api/assignments/<int:assignment_id>', methods=['DELETE'])
def delete_assignment(assignment_id):
    """
    Deletes an assignment by its ID.
    
    Args:
        assignment_id (int): The ID of the assignment to delete.
        
    Returns:
        JSON: Success message, status 200.
        JSON: Error 404 if assignment not found.
    """
    assignment = db.session.get(Assignment, assignment_id)
    if not assignment:
        return jsonify({'error': 'Assignment not found'}), 404
    
    try:
        db.session.delete(assignment)
        db.session.commit()
        return jsonify({'message': 'Assignment deleted'}), 200
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting assignment {assignment_id}: {e}")
        return jsonify({'error': 'Could not delete assignment', 'message': str(e)}), 500

# --- Project Manager View Endpoint ---
@app.route('/api/project_manager/<int:manager_id>/projects', methods=['GET'])
def get_manager_projects_with_assignments(manager_id):
    """
    Retrieves all projects managed by a specific person (manager),
    along with all assignments for each of those projects.
    
    Args:
        manager_id (int): The ID of the person (project manager).
        
    Returns:
        JSON: A list of project objects, each including a list of its assignments. Status 200.
        JSON: Error 404 if the manager (Person) is not found.
    """
    manager = db.session.get(Person, manager_id)
    if not manager:
        return jsonify({'error': 'Project manager (Person) not found'}), 404

    # Fetch projects managed by this person.
    # Assumes 'managed_projects' is a dynamic relationship on Person model.
    projects_managed = manager.managed_projects.all() 
    
    result = []
    for project in projects_managed:
        project_data = project.to_dict() 
        # Fetch assignments for the current project.
        # Assumes 'assignments' is a dynamic relationship on Project model.
        project_assignments = project.assignments.all()
        project_data['assignments'] = [assignment.to_dict() for assignment in project_assignments]
        result.append(project_data)
        
    return jsonify(result), 200

# --- CLI Commands ---
@app.cli.command('init-db')
def init_db_command():
    """
    Flask CLI command to initialize the database.
    Creates all database tables based on defined SQLAlchemy models.
    Run with `flask init-db`.
    """
    with app.app_context(): # Ensure operations are within application context
        db.create_all()
    print('Initialized the database and created all tables.')

if __name__ == '__main__':
    # Standard way to run Flask dev server: `flask run` in terminal.
    # `app.run()` is also possible but `flask run` is preferred for development.
    # Set FLASK_APP=app.py (or your file name) and FLASK_DEBUG=1 for development mode.
    app.run(debug=True)
