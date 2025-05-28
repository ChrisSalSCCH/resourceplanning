# Resource Planning Tool

## Overview

The Resource Planning Tool is a web application designed to help manage resources (persons) and their assignments to various projects. It provides a backend API for creating, reading, updating, and deleting persons, projects, and their assignments. It also includes a view for project managers to see all projects they manage along with the assignments under those projects.

## Current Status

*   **Backend API:** Complete. All specified CRUD operations for Persons, Projects, and Assignments, as well as the Project Manager View, have been implemented.
*   **Frontend Development:** Started. TypeScript models and Angular services for interacting with the backend API were created. However, frontend development was halted due to persistent environmental/tooling issues within the development sandbox that prevented the crucial `HttpClient` setup in the Angular application. Without this, the frontend services cannot communicate with the backend.
*   **Backend Testing:** PyTest unit and integration tests have been written for the backend API and are located in `resource_planning_tool/backend/tests/`. However, their reliable execution was hindered by environmental/tooling issues, particularly with Python virtual environment setup and consistent `pytest` execution within the sandbox.

## Backend Setup and Running

1.  **Navigate to Backend Directory:**
    ```bash
    cd resource_planning_tool/backend
    ```

2.  **Create and Activate Virtual Environment:**
    It's recommended to use a Python virtual environment.
    ```bash
    # Create a virtual environment (e.g., named 'venv')
    python3 -m venv venv
    # Activate the virtual environment
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies:**
    Install all required packages from `requirements.txt`.
    ```bash
    pip install -r requirements.txt
    ```

4.  **Initialize the Database:**
    This command creates the SQLite database file (`resource_planner.db`) and all necessary tables.
    ```bash
    flask init-db
    ```
    You should see a message: "Initialized the database and created all tables."

5.  **Run the Flask Development Server:**
    ```bash
    flask run
    ```
    The backend API will typically be available at `http://127.0.0.1:5000` or `http://localhost:5000`.

## Backend API Endpoints

The base URL for all API endpoints is typically `http://localhost:5000/api`.

### Health Check

*   **`GET /api/health`**
    *   **Description:** Checks the health of the API.
    *   **Example Response (200 OK):**
        ```json
        {
          "status": "OK"
        }
        ```

### Persons

*   **`POST /api/persons`**
    *   **Description:** Creates a new person.
    *   **Example Request Body:**
        ```json
        {
          "name": "Alice Wonderland",
          "working_hours": 35
        }
        ```
    *   **Example Response (201 Created):**
        ```json
        {
          "id": 1,
          "name": "Alice Wonderland",
          "working_hours": 35
        }
        ```

*   **`GET /api/persons`**
    *   **Description:** Retrieves a list of all persons.
    *   **Example Response (200 OK):**
        ```json
        [
          {
            "id": 1,
            "name": "Alice Wonderland",
            "working_hours": 35
          },
          {
            "id": 2,
            "name": "Bob The Builder",
            "working_hours": 40
          }
        ]
        ```

*   **`GET /api/persons/<int:person_id>`**
    *   **Description:** Retrieves a specific person by their ID.
    *   **Example Response (200 OK):**
        ```json
        {
          "id": 1,
          "name": "Alice Wonderland",
          "working_hours": 35
        }
        ```

*   **`PUT /api/persons/<int:person_id>`**
    *   **Description:** Updates an existing person.
    *   **Example Request Body:**
        ```json
        {
          "name": "Alice W. (Updated)",
          "working_hours": 38
        }
        ```
    *   **Example Response (200 OK):**
        ```json
        {
          "id": 1,
          "name": "Alice W. (Updated)",
          "working_hours": 38
        }
        ```

*   **`DELETE /api/persons/<int:person_id>`**
    *   **Description:** Deletes a person.
    *   **Example Response (200 OK):**
        ```json
        {
          "message": "Person deleted"
        }
        ```

### Projects

*   **`POST /api/projects`**
    *   **Description:** Creates a new project.
    *   **Example Request Body:**
        ```json
        {
          "name": "Project Phoenix",
          "project_manager_id": 1,
          "budget": "50000.00"
        }
        ```
    *   **Example Response (201 Created):**
        ```json
        {
          "id": 1,
          "name": "Project Phoenix",
          "project_manager_id": 1,
          "project_manager_name": "Alice Wonderland",
          "budget": "50000.00"
        }
        ```

*   **`GET /api/projects`**
    *   **Description:** Retrieves a list of all projects.
    *   **Example Response (200 OK):** (Similar structure to individual project, in a list)

*   **`GET /api/projects/<int:project_id>`**
    *   **Description:** Retrieves a specific project by its ID.
    *   **Example Response (200 OK):** (Similar to POST response)

*   **`PUT /api/projects/<int:project_id>`**
    *   **Description:** Updates an existing project.
    *   **Example Request Body:**
        ```json
        {
          "name": "Project Phoenix Revamped",
          "budget": "55000.00"
        }
        ```
    *   **Example Response (200 OK):** (Reflects updated data)

*   **`DELETE /api/projects/<int:project_id>`**
    *   **Description:** Deletes a project.
    *   **Example Response (200 OK):**
        ```json
        {
          "message": "Project deleted"
        }
        ```

### Assignments

*   **`POST /api/assignments`**
    *   **Description:** Creates a new assignment, linking a person to a project.
    *   **Example Request Body:**
        ```json
        {
          "project_id": 1,
          "person_id": 2,
          "assigned_hours": 80,
          "timeline_start": "2024-01-01",
          "timeline_end": "2024-02-28"
        }
        ```
    *   **Example Response (201 Created):**
        ```json
        {
          "id": 1,
          "project_id": 1,
          "project_name": "Project Phoenix",
          "person_id": 2,
          "person_name": "Bob The Builder",
          "assigned_hours": 80,
          "timeline_start": "2024-01-01",
          "timeline_end": "2024-02-28"
        }
        ```

*   **`GET /api/projects/<int:project_id>/assignments`**
    *   **Description:** Retrieves all assignments for a specific project.
    *   **Example Response (200 OK):** (List of assignment objects)

*   **`GET /api/persons/<int:person_id>/assignments`**
    *   **Description:** Retrieves all assignments for a specific person.
    *   **Example Response (200 OK):** (List of assignment objects)

*   **`PUT /api/assignments/<int:assignment_id>`**
    *   **Description:** Updates an existing assignment.
    *   **Example Request Body:**
        ```json
        {
          "assigned_hours": 100,
          "timeline_end": "2024-03-15"
        }
        ```
    *   **Example Response (200 OK):** (Reflects updated assignment data)

*   **`DELETE /api/assignments/<int:assignment_id>`**
    *   **Description:** Deletes an assignment.
    *   **Example Response (200 OK):**
        ```json
        {
          "message": "Assignment deleted"
        }
        ```

### Project Manager View

*   **`GET /api/project_manager/<int:manager_id>/projects`**
    *   **Description:** Retrieves all projects managed by a specific person (manager), including all assignments for each project.
    *   **Example Response (200 OK):**
        ```json
        [
          {
            "id": 1,
            "name": "Project Phoenix",
            "project_manager_id": 1,
            "project_manager_name": "Alice Wonderland",
            "budget": "50000.00",
            "assignments": [
              {
                "id": 1,
                "project_id": 1,
                "project_name": "Project Phoenix",
                "person_id": 2,
                "person_name": "Bob The Builder",
                "assigned_hours": 80,
                "timeline_start": "2024-01-01",
                "timeline_end": "2024-02-28"
              }
              // ... other assignments for this project
            ]
          }
          // ... other projects managed by this person
        ]
        ```

## Backend Testing

*   **Location:** PyTest tests are located in the `resource_planning_tool/backend/tests/` directory.
*   **Dependency:** `pytest` is required and is listed in `requirements.txt`.
*   **Running Tests:**
    Navigate to the `resource_planning_tool/backend` directory and run:
    ```bash
    # Ensure PYTHONPATH is set if running from a different root or if module errors occur
    # export PYTHONPATH=/path/to/your/project/root:$PYTHONPATH
    python3 -m pytest 
    # or simply
    # pytest
    ```
*   **Note on Execution:** As mentioned in the "Current Status," reliable execution of these tests was hindered by environmental issues within the development sandbox. The tests are designed to cover all API endpoints and their logic.

## Frontend Setup (Brief Note)

*   The `resource_planning_tool/frontend/resource-planner-ui/` directory contains an Angular project.
*   Frontend development was initiated with the creation of data models and services to interact with the backend.
*   **Status:** Incomplete. Development was halted due to persistent issues in the development environment that prevented the setup of `HttpClientModule` (or `provideHttpClient()`), which is essential for Angular services to make HTTP requests to the backend. The created services are therefore non-functional in their current state.
