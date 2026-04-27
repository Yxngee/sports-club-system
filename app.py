from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
db = SQLAlchemy(app)

# -------- DATABASE --------

class PurchaseOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_by = db.Column(db.String(100))
    status = db.Column(db.String(50))

# -------- ROUTES --------

@app.route('/')
def home():
    orders = PurchaseOrder.query.all()
    return render_template('home.html', orders=orders)

@app.route('/create', methods=['POST'])
def create():
    user = request.form['user']
    order = PurchaseOrder(created_by=user, status="Pending")
    db.session.add(order)
    db.session.commit()
    return redirect('/')

@app.route('/approve/<int:id>')
def approve(id):
    order = PurchaseOrder.query.get(id)
    order.status = "Approved"
    db.session.commit()
    return redirect('/')

# -------- RUN --------

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)