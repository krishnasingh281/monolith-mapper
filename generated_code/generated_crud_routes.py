import os
from flask import Flask, jsonify, request
from models import db, Analysis
app = Flask(__name__)
@app.route('/analysis', methods=['POST'])
def create_analysis():
    analysis = Analysis(project_id=request.json['project_id'], analysis_type=request.json['analysis_type'], input_data=request.json['input_data'])
    db.session.add(analysis)
    db.session.commit()
    return jsonify({'message': 'Analysis created successfully'}), 201
@app.route('/analysis', methods=['GET'])
def get_analysis():
    analyses = Analysis.query.all()
    return jsonify([a.to_dict() for a in analyses])
@app.route('/analysis/<int:id>', methods=['PUT'])
def update_analysis(id):
    analysis = Analysis.query.get(id)
    if analysis:
        analysis.project_id = request.json['project_id']
        analysis.analysis_type = request.json['analysis_type']
        analysis.input_data = request.json['input_data']
        db.session.commit()
        return jsonify({'message': 'Analysis updated successfully'}), 200
    else:
        return jsonify({'message': 'Analysis not found'}), 404
@app.route('/analysis/<int:id>', methods=['DELETE'])
def delete_analysis(id):
    analysis = Analysis.query.get(id)
    if analysis:
        db.session.delete(analysis)
        db.session.commit()
        return jsonify({'message': 'Analysis deleted successfully'}), 200
    else:
        return jsonify({'message': 'Analysis not found'}), 404