Worker Breakout Application
This is a Flask application designed to manage worker assignments across various sections in a retail environment. The application allows for adding, editing, and deleting workers, calculating worker distribution based on workload, and visualizing the distribution with a bar graph.
Features
* Add, edit, and delete worker profiles.
* Calculate worker distribution based on workload percentages.
* Display worker assignments in a tabular format.
* Visualize workload distribution using a bar graph.
Technologies Used
* Python
* Flask
* Jinja2
* Pandas
* JavaScript (Chart.js)
* HTML/CSS (Bootstrap)
* Heroku (Deployment)
Setup and Installation
Prerequisites
* Python 3.10.x
* Pip (Python package installer)
Installation
    1. Clone the repository:


        git clone https://github.com/hayasep/worker-breakout-app.git
        cd worker-breakout-app


    2. Create and activate a virtual environment:


        python -m venv venv
        source venv/bin/activate   
        # On Windows use`venv\Scripts\activate`


    3. Install the dependencies:


        pip install -r requirements.txt


    4. Create a runtime.txt file with the following content to specify the Python version:
        txt

        python-3.10.12


    5. Run the application locally:

        
        flask run

        The application will be available at http://127.0.0.1:5000.

Usage
    1. Navigate to the home page to view the worker breakout form.
    2. Add, edit, or delete workers through the 'Manage Workers' page.
    3. Upload a CSV file with section data to automatically populate the workload times.
    4. Calculate the worker distribution based on the entered workload times.
    5. View the worker assignments and workload distribution graph.


Contributing
Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.
License
This project is licensed under the MIT License. See the LICENSE file for details.