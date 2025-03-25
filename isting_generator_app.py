# listing_generator_app.py

from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
from werkzeug.utils import secure_filename
import csv
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'super-secret-listing-key-2852'

CSV_FILE = 'listings.csv'

def generate_title(data):
    return f"{data['brand']} {data['item_type']} {data['size']} {data['colour']} – {data['condition']} – BNWT"

def generate_description(data):
    return f"""
Brand: {data['brand']}  
Size: {data['size']}  
Condition: {data['condition']}  
Material: {data['material']}  
Colour: {data['colour']}  
Notes: {data['notes']}  

🚚 Fast dispatch – usually same day!  
🚶 Feel free to bundle items!
"""

def save_to_csv(data):
    file_path = 'listings.csv'
    if not os.path.exists(file_path):
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([...])  # headers

    new_id = get_next_id()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    with open(file_path, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            new_id, timestamp, data['brand'], data['item_type'], data['size'],
            data['colour'], data['condition'], data['material'], data['notes'],
            data.get('price', ''), data.get('parcel_size', ''), '', '', 'Draft'
        ])

def get_next_id():
    if not os.path.exists(CSV_FILE):
        return 1
    with open(CSV_FILE, 'r') as file:
        reader = csv.DictReader(file)
        rows = list(reader)
        if not rows:
            return 1
        last_id = int(rows[-1]['id'])
        return last_id + 1

def read_listings():
    if not os.path.exists(CSV_FILE):
        return []
    with open(CSV_FILE, 'r') as file:
        reader = csv.DictReader(file)
        return list(reader)

def write_all_listings(listings):
    with open('listings.csv', 'w', newline='') as f:
        fieldnames = [
            'id', 'timestamp', 'brand', 'item_type', 'size', 'colour',
            'condition', 'material', 'notes', 'price', 'parcel_size',
            'title', 'description', 'status'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in listings:
            clean_row = {k: v for k, v in row.items() if k in fieldnames}
            writer.writerow(clean_row)

@app.route('/')
def index():
    listings = read_listings()
    status_filter = request.args.get('status')
    if status_filter:
        listings = [l for l in listings if l['status'] == status_filter]
    return render_template('index.html', listings=listings, active_filter=status_filter)

@app.route('/new', methods=['GET', 'POST'])
def new_listing():
    if request.method == 'POST':
        save_to_csv(request.form)
        return redirect(url_for('index'))
    return render_template('new.html')

@app.route('/generate/<int:item_id>', methods=['GET', 'POST'])
def generate(item_id):
    listings = read_listings()
    listing = next((l for l in listings if int(l['id']) == item_id), None)

    if not listing:
        return "Listing not found", 404

    if request.method == 'POST':
        title = generate_title(listing)
        description = generate_description(listing)
        listing['title'] = title
        listing['description'] = description
        listing['status'] = 'Generated'
        write_all_listings(listings)
        return render_template('generate.html', listing=listing, title=title, description=description, submitted=True)

    return render_template('generate.html', listing=listing, submitted=False)

@app.route('/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_listing(item_id):
    listings = read_listings()
    listing = next((l for l in listings if int(l['id']) == item_id), None)

    if not listing:
        return "Listing not found", 404

    if request.method == 'POST':
        for key in ['brand', 'item_type', 'size', 'colour', 'condition', 'material', 'notes', 'price', 'parcel_size']:
            listing[key] = request.form.get(key, '')
        write_all_listings(listings)
        flash(f'Listing #{item_id} updated successfully!')
        return redirect(url_for('index'))

    return render_template('edit.html', listing=listing)

@app.route('/delete/<int:item_id>', methods=['POST'])
def delete_listing(item_id):
    listings = read_listings()
    listings = [l for l in listings if int(l['id']) != item_id]
    write_all_listings(listings)
    flash(f'Listing #{item_id} deleted.')
    return redirect(url_for('index'))

@app.route('/update-status/<int:item_id>', methods=['POST'])
def update_status(item_id):
    listings = read_listings()
    for listing in listings:
        if int(listing['id']) == item_id:
            listing['status'] = request.form['status']
            break
    write_all_listings(listings)
    flash('Status updated successfully!')
    return redirect(url_for('index'))

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if not file:
            flash('No file selected.')
            return redirect(request.url)

        filename = secure_filename(file.filename)
        if filename.endswith('.csv'):
            df = pd.read_csv(file)
        elif filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file)
        else:
            flash('Invalid file format. Please upload a CSV or Excel file.')
            return redirect(request.url)

        required_cols = {'brand', 'item_type', 'size', 'colour', 'condition', 'material', 'notes', 'price', 'parcel_size'}
        df.columns = [col.lower() for col in df.columns]
        if not required_cols.issubset(df.columns):
            flash('Missing required columns in your file.')
            return redirect(request.url)

        added = 0
        for _, row in df.iterrows():
            data = {
                'brand': row['brand'],
                'item_type': row['item_type'],
                'size': row['size'],
                'colour': row['colour'],
                'condition': row['condition'],
                'material': row['material'],
                'notes': row['notes'],
                'price': row.get('price', ''),
                'parcel_size': row.get('parcel_size', '')
            }

            save_to_csv(data)
            added += 1

        flash(f'{added} listings successfully uploaded.')
        return redirect(url_for('index'))

    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True)