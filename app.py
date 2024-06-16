import pandas as pd
from werkzeug.utils import secure_filename
import os
from flask import Flask, render_template, request, redirect, url_for, flash
import pickle
import math
import random
from flask import session


app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure the upload folder exists
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

class Worker:
    def __init__(self, name, preference, alternatives):
        self.name = name
        self.preference = preference
        self.alternatives = alternatives
        self.is_working = False

def calculate_workers_needed(workload, total_workers, capacities):
    total_workload = sum(workload)
    if total_workload == 0:
        return [0] * len(workload)

    workload_ratio = [w / total_workload for w in workload]
    workers_needed = [max(1, round(ratio * total_workers)) if workload[i] > 0 else 0 for i, ratio in enumerate(workload_ratio)]
    
    for i in range(len(workers_needed)):
        if capacities[i] is not None and workers_needed[i] > capacities[i]:
            workers_needed[i] = capacities[i]

    return workers_needed

def load_workers():
    if os.path.exists('workers.pkl'):
        with open('workers.pkl', 'rb') as f:
            return pickle.load(f)
    return []

def save_workers(workers):
    with open('workers.pkl', 'wb') as f:
        pickle.dump(workers, f)

def distribute_workers(workers, sections, workers_needed):
    workers = sorted(workers, key=lambda w: len(w.alternatives))  # Sort workers by their versatility (alternatives)
    worker_distribution = {section: [] for section in sections}
    excess_workers = []

    # Step 1: Assign workers to their preferred sections
    for worker in workers:
        if worker.is_working and worker.preference in sections:
            worker_distribution[worker.preference].append(worker.name)
            worker.is_working = False  # Mark worker as assigned

    # Step 2: Assign workers based on their alternatives if no preference is available
    for section in sections:
        if not worker_distribution[section]:  # If no workers assigned to the section
            for worker in workers:
                if worker.is_working and section in worker.alternatives:
                    worker_distribution[section].append(worker.name)
                    worker.is_working = False  # Mark worker as assigned
                    break

    # Step 3: Fill in sections without any workers by looking at already assigned workers' alternatives
    for section in sections:
        if not worker_distribution[section]:  # If still no workers assigned to the section
            for assigned_section in sections:
                if worker_distribution[assigned_section]:  # Look at sections with assigned workers
                    for worker_name in worker_distribution[assigned_section]:
                        worker = next(w for w in workers if w.name == worker_name)
                        if section in worker.alternatives:
                            worker_distribution[section].append(worker_name)
                            worker_distribution[assigned_section].remove(worker_name)
                            break
                    if worker_distribution[section]:
                        break

    # Step 4: Identify overstaffed sections and move excess workers to excess pool
    for section, needed in zip(sections, workers_needed):
        while len(worker_distribution[section]) > needed:
            excess_worker = worker_distribution[section].pop()
            excess_workers.append(excess_worker)

    # Step 5: Fill understaffed sections from excess workers
    for section, needed in zip(sections, workers_needed):
        while len(worker_distribution[section]) < needed:
            if not excess_workers:
                break  # If there are no more excess workers, break out of the loop
            suitable_worker = None
            for worker_name in excess_workers:
                worker = next(w for w in workers if w.name == worker_name)
                if section in worker.alternatives:
                    suitable_worker = worker_name
                    break

            if suitable_worker:
                excess_workers.remove(suitable_worker)
                worker_distribution[section].append(suitable_worker)
            else:
                # No suitable worker found in alternatives, take a random worker from excess pool
                worker_distribution[section].append(excess_workers.pop(0))

    return worker_distribution, excess_workers

sections = ["HBA", "Stationary", "Kitchen", "C/D", "Chemicals/Paper", "Sports", "Toys", "Seasonal",
            "Pets", "Infants", "HBA Repacks", "C/D Repacks", "A&A"]
workers = load_workers()

@app.route('/')
def index():
    section_data = session.get('section_data', {})
    return render_template('index.html', sections=sections, workers=workers, section_data=section_data)


@app.route('/manage_workers', methods=['GET', 'POST'])
def manage_workers():
    if request.method == 'POST':
        name = request.form['name']
        preference = request.form['preference']
        alternatives = request.form.getlist('alternatives')
        new_worker = Worker(name, preference, alternatives)
        workers.append(new_worker)
        flash(f'Worker {name} added successfully!', 'success')
        return redirect(url_for('manage_workers'))
    return render_template('manage_workers.html', workers=workers, sections=sections)

@app.route('/edit_worker/<name>', methods=['GET', 'POST'])
def edit_worker(name):
    worker = next((w for w in workers if w.name == name), None)
    if request.method == 'POST':
        if worker:
            worker.name = request.form['name']
            worker.preference = request.form['preference']
            worker.alternatives = request.form.getlist('alternatives')
            flash(f'Worker {worker.name} updated successfully!', 'success')
            return redirect(url_for('manage_workers'))
    return render_template('edit_worker.html', worker=worker, sections=sections)

@app.route('/delete_worker/<name>', methods=['POST'])
def delete_worker(name):
    global workers
    workers = [w for w in workers if w.name != name]
    flash(f'Worker {name} deleted successfully!', 'danger')
    return redirect(url_for('manage_workers'))


@app.route('/calculate_distribution', methods=['POST'])
def calculate_distribution():
    total_workers = len(request.form.getlist('working'))

    workload = [float(request.form.get(f'time_{section}', 0)) for section in sections]
    max_capacities = [int(request.form.get(f'cap_{section}', 0)) if request.form.get(f'cap_{section}') else None for section in sections]
    total_workload = sum(workload)
    workload_percentages = [(w / total_workload) * 100 if total_workload > 0 else 0 for w in workload]
    
    # Calculate suggested workers needed without considering max capacities
    suggested_workers_needed = calculate_workers_needed(workload, total_workers, [None] * len(sections))
    
    # Calculate workers needed with considering max capacities
    workers_needed = calculate_workers_needed(workload, total_workers, max_capacities)

    for worker in workers:
        worker.is_working = worker.name in request.form.getlist('working')

    worker_distribution, excess_workers = distribute_workers(workers, sections, workers_needed)
    
    # Adding stock_times and total_stock_time for the bar chart
    stock_times = workload
    total_stock_time = total_workload

    return render_template('worker_distribution.html', 
                           worker_distribution=worker_distribution, 
                           excess_workers=excess_workers, 
                           workers_needed=workers_needed, 
                           suggested_workers_needed=suggested_workers_needed, 
                           workload_percentages=workload_percentages, 
                           total_workers=total_workers, 
                           max_workers=max_capacities,
                           sections=sections,
                           stock_times=stock_times,
                           total_stock_time=total_stock_time)




@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(request.url)
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Read the CSV file
    data = pd.read_csv(filepath)

    # Remove commas from numeric values
    data.replace({',': ''}, regex=True, inplace=True)

    # Convert relevant columns to numeric, errors='coerce' will turn non-numeric values into NaN
    data = data.apply(pd.to_numeric, errors='coerce')

    # Calculate values for each section based on the provided logic
    hba_full_case_eaches = data.iloc[25:32, 2].sum()
    hba_total_eaches = data.iloc[25:32, 5].sum()
    hba_stocking_time = data.iloc[25:32, 6].sum()
    hba = round((hba_full_case_eaches / hba_total_eaches) * hba_stocking_time, 1)

    hba_repacks_each = data.iloc[26:32, 4].sum()
    hba_repacks_total = data.iloc[26:32, 5].sum()
    hba_repacks_stocking_time = data.iloc[26:32, 6].sum()
    hba_repacks = round((hba_repacks_each / hba_repacks_total) * hba_repacks_stocking_time, 1)

    section_data = {
        "HBA": hba,
        "Stationary": round(data.iloc[63, 6], 1),
        "Kitchen": round(data.iloc[61:63, 6].sum(), 1),
        "C/D": round((data.iloc[42:57, 2].sum() / data.iloc[42:57, 5].sum()) * data.iloc[42:57, 6].sum(), 1),
        "Chemicals/Paper": round(data.iloc[10:14, 6].sum() + data.iloc[21:25, 6].sum(), 1),
        "Sports": round(data.iloc[64:67, 6].sum(), 1),
        "Toys": round(data.iloc[3:8, 6].sum(), 1),
        "Seasonal": round(data.iloc[69:75, 6].sum(), 1),
        "Pets": round(data.iloc[14:17, 6].sum(), 1),
        "Infants": round(data.iloc[17:20, 6].sum(), 1),
        "HBA Repacks": hba_repacks,
        "C/D Repacks": round((data.iloc[42:57, 4].sum() / data.iloc[42:57, 5].sum()) * data.iloc[42:57, 6].sum(), 1),
        "A&A": round(data.iloc[57:61, 6].sum(), 1)
    }

    # Store the section data in the session
    session['section_data'] = section_data

    flash('CSV uploaded and processed successfully.', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

