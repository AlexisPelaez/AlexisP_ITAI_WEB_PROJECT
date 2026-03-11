from . import db

class PreSimResponse(db.Model):
    __tablename__ = "pre_sim_responses"

    id = db.Column(db.Integer, primary_key=True)
    test_run_id = db.Column(db.String, nullable=False)

    pq1 = db.Column(db.Text, nullable=False)
    pq1_correct = db.Column(db.Integer, nullable=False)
    pq2 = db.Column(db.Text, nullable=False)
    pq2_correct = db.Column(db.Integer, nullable=False)
    pq3 = db.Column(db.Text, nullable=False)
    pq3_correct = db.Column(db.Integer, nullable=False)
    pq4 = db.Column(db.Text, nullable=False)
    pq4_correct = db.Column(db.Integer, nullable=False)
    pq5 = db.Column(db.Text, nullable=False)
    pq5_correct = db.Column(db.Integer, nullable=False)


class SimResponse(db.Model):
    __tablename__ = "sim_responses"

    id = db.Column(db.Integer, primary_key=True)
    test_run_id = db.Column(db.String, nullable=False)
    
    pq1 = db.Column(db.Text, nullable=False)
    pq1_correct = db.Column(db.Integer, nullable=False)
    pq2 = db.Column(db.Text, nullable=False)
    pq2_correct = db.Column(db.Integer, nullable=False)
    pq3 = db.Column(db.Text, nullable=False)
    pq3_correct = db.Column(db.Integer, nullable=False)
    pq4 = db.Column(db.Text, nullable=False)
    pq4_correct = db.Column(db.Integer, nullable=False)
    pq5 = db.Column(db.Text, nullable=False)
    pq5_correct = db.Column(db.Integer, nullable=False)
