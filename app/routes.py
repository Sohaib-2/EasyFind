from flask import Blueprint, render_template, request, redirect, url_for, send_file
from . import socketio
from flask_socketio import emit
from scraping import scrape_companies
import os

bp = Blueprint('main', __name__)

@bp.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        category = request.form['category']
        location = request.form['location']
        search_type = request.form['search_type']
        num_companies = int(request.form['num_companies'])
        output_file = "results.csv"  # You can change this to a dynamic filename if needed

        socketio.start_background_task(target=scrape_companies, category=category, location=location, search_type=search_type, num_companies=num_companies, output_file=output_file)

        return redirect(url_for('main.results'))

    return render_template('index.html')

@bp.route('/results', methods=['GET'])
def results():
    return render_template('results.html')

@bp.route('/download', methods=['GET'])
def download():
    path = "../results.csv"
    return send_file(path, as_attachment=True)
