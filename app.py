from flask import Flask, render_template, request, redirect, url_for, make_response, jsonify
import sqlite3
import json
import os
import calendar as cal_module
from datetime import datetime, date as date_obj, timedelta
from werkzeug.utils import secure_filename

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'tailor.db')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_upload(file, prefix):
    if file and file.filename and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{prefix}_{int(datetime.now().timestamp())}.{ext}"
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        return filename
    return None

SHOP_NAME     = "SHUBHAM NX"
SHOP_ADDRESS  = "Krishna Chowk, Vidya Nagar, New Sangavi, Pune, Pimpri-Chinchwad, Maharashtra 411061"
SHOP_CONTACTS = {"Master": "+91 96899 24060", "Shop": "+91 92846 30254"}

STITCHING_COST = {
    'shirt':        450,
    'pant':         550,
    'kurta':        500,
    'kurta_astar':  1000,
    'suit':         3200,
    'jacket':       1200,
    'pyjama':       500,
}

GARMENT_QTY_FIELD = {
    'shirt':  'No of Shirts',
    'pant':   'No of Pants',
    'kurta':  'No of Kurtas',
    'suit':   'No of Suits',
    'jacket': 'No of Jackets',
    'pyjama': 'No of Pyjamas',
}

GARMENT_FIELDS = {
    'shirt': ['No of Shirts', 'Shirt Type', 'Length', 'Chest', 'Stomach', 'Seat', 'Shoulder', 'Sleeve Length', 'Arm Hole', 'Elbow', 'Cuff', 'Neck', 'X-Chest', 'Front 1', 'Front 2', 'Front 3', 'Back 1', 'Back 2', 'Back 3', 'Front-patti', 'Collar', 'Sample Shirt', 'Collar Type', 'Cuff Type'],
    'pant':  ['No of Pants', 'Length', 'Waist', 'Seat', 'Seat Front', 'Seat Back', 'Thighs', 'Thighs Type', 'Knee', 'Knee Height', 'Calf', 'Bottom', 'Ring', 'Front Fork', 'Back Fork', 'Plates', 'Belt', 'Button', 'Sample Pant'],
    'kurta': ['No of Kurtas', 'Kurta Type', 'Length', 'Chest', 'Stomach', 'Seat', 'Shoulder', 'Sleeve Length', 'Arm Hole', 'Elbow', 'Cuff', 'Cuff Style', 'Neck', 'Collar', 'X-Chest', 'Front 1', 'Front 2', 'Front 3', 'Front 4', 'Back 1', 'Back 2', 'Back 3', 'Pockets', 'Astar', 'Collar Type', 'Sample Kurta'],
    'suit':  ['No of Suits', 'Length', 'Chest', 'Stomach', 'Seat', 'Shoulder', 'Sleeve Length', 'Arms', 'Neck'],
    'jacket':['No of Jackets', 'Length', 'Chest', 'Stomach', 'Seat', 'Shoulder', 'Sleeve Length', 'Arms', 'Neck'],
    'pyjama':['No of Pyjamas', 'Length', 'Waist', 'Seat', 'Thighs', 'Knee', 'Bottom', 'Ring'],
}

def field_key(field):
    return field.lower().replace(' ', '_')

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name     TEXT NOT NULL,
            mobile   TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS measurements (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id  INTEGER NOT NULL,
            garment_type TEXT NOT NULL,
            measurements TEXT NOT NULL,
            notes        TEXT,
            image        TEXT,
            order_date   DATE DEFAULT (date('now')),
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS receipts (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id   INTEGER NOT NULL,
            slip_no       TEXT NOT NULL,
            receipt_date  DATE NOT NULL,
            items         TEXT NOT NULL,
            total         REAL NOT NULL,
            advance       REAL NOT NULL DEFAULT 0,
            balance       REAL NOT NULL,
            delivery_date TEXT,
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    ''')
    # Migrations for existing databases
    for migration in [
        "ALTER TABLE measurements ADD COLUMN image TEXT",
        "ALTER TABLE measurements ADD COLUMN trial_date DATE",
        "ALTER TABLE measurements ADD COLUMN delivery_date DATE",
        "ALTER TABLE measurements ADD COLUMN status TEXT DEFAULT 'pending'",
        "ALTER TABLE measurements ADD COLUMN trial_done_date DATE",
        "ALTER TABLE measurements ADD COLUMN actual_delivery_date DATE",
    ]:
        try:
            conn.execute(migration)
        except Exception:
            pass
    conn.commit()
    conn.close()

# ── helpers ──────────────────────────────────────────────────────────────────

def parse_measurements(rows):
    result = []
    for m in rows:
        result.append({
            'id':                   m['id'],
            'garment_type':         m['garment_type'],
            'measurements':         json.loads(m['measurements']),
            'notes':                m['notes'],
            'image':                m['image'],
            'order_date':           m['order_date'],
            'trial_date':           m['trial_date'],
            'delivery_date':        m['delivery_date'],
            'created_at':           m['created_at'],
            'status':               m['status'] or 'pending',
            'trial_done_date':      m['trial_done_date'],
            'actual_delivery_date': m['actual_delivery_date'],
        })
    return result

# ── routes ───────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    query = request.args.get('q', '').strip()
    conn = get_db()
    if query:
        customers = conn.execute(
            "SELECT * FROM customers WHERE name LIKE ? OR mobile LIKE ? ORDER BY name",
            (f'%{query}%', f'%{query}%')
        ).fetchall()
    else:
        customers = conn.execute(
            "SELECT * FROM customers ORDER BY created_at DESC LIMIT 30"
        ).fetchall()
    today_str = datetime.now().strftime('%Y-%m-%d')
    overdue_count = conn.execute(
        "SELECT COUNT(*) FROM measurements WHERE delivery_date < ? AND (status IS NULL OR status != 'delivered')",
        (today_str,)
    ).fetchone()[0]
    conn.close()
    return render_template('index.html', customers=customers, query=query, shop=SHOP_NAME, overdue_count=overdue_count)


@app.route('/customer/add', methods=['GET', 'POST'])
def add_customer():
    error = None
    if request.method == 'POST':
        name   = request.form['name'].strip()
        mobile = request.form['mobile'].strip()
        if not name:
            error = 'Customer name is required.'
        else:
            conn = get_db()
            cur  = conn.execute("INSERT INTO customers (name, mobile) VALUES (?, ?)", (name, mobile))
            conn.commit()
            customer_id = cur.lastrowid
            conn.close()
            return redirect(url_for('customer', customer_id=customer_id))
    return render_template('add_customer.html', error=error, shop=SHOP_NAME)


@app.route('/customer/<int:customer_id>')
def customer(customer_id):
    conn = get_db()
    cust = conn.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()
    if not cust:
        conn.close()
        return "Customer not found", 404
    rows = conn.execute(
        "SELECT * FROM measurements WHERE customer_id = ? ORDER BY order_date DESC, created_at DESC",
        (customer_id,)
    ).fetchall()
    receipts = conn.execute(
        "SELECT * FROM receipts WHERE customer_id = ? ORDER BY receipt_date DESC, created_at DESC",
        (customer_id,)
    ).fetchall()
    conn.close()
    return render_template('customer.html', customer=cust,
                           measurements=parse_measurements(rows),
                           receipts=receipts, shop=SHOP_NAME)


@app.route('/customer/<int:customer_id>/edit', methods=['GET', 'POST'])
def edit_customer(customer_id):
    conn = get_db()
    cust = conn.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()
    if not cust:
        conn.close()
        return "Customer not found", 404
    error = None
    if request.method == 'POST':
        name   = request.form['name'].strip()
        mobile = request.form['mobile'].strip()
        if not name:
            error = 'Customer name is required.'
        else:
            conn.execute("UPDATE customers SET name=?, mobile=? WHERE id=?", (name, mobile, customer_id))
            conn.commit()
            conn.close()
            return redirect(url_for('customer', customer_id=customer_id))
    conn.close()
    return render_template('edit_customer.html', customer=cust, error=error, shop=SHOP_NAME)


@app.route('/customer/<int:customer_id>/add-measurement', methods=['GET', 'POST'])
def add_measurement(customer_id):
    conn = get_db()
    cust = conn.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()
    if not cust:
        conn.close()
        return "Customer not found", 404

    if request.method == 'POST':
        garment_type  = request.form.get('garment_type', '').lower()
        order_date    = request.form.get('order_date') or datetime.now().strftime('%Y-%m-%d')
        trial_date    = request.form.get('trial_date', '').strip() or None
        delivery_date = request.form.get('delivery_date', '').strip() or None
        notes         = request.form.get('notes', '').strip()
        fields        = GARMENT_FIELDS.get(garment_type, [])
        measurements  = {f: request.form.get(field_key(f), '').strip() for f in fields}
        image         = save_upload(request.files.get('fabric_photo'), f"fabric_{customer_id}")

        conn.execute(
            "INSERT INTO measurements (customer_id, garment_type, measurements, notes, image, order_date, trial_date, delivery_date) VALUES (?,?,?,?,?,?,?,?)",
            (customer_id, garment_type, json.dumps(measurements), notes, image, order_date, trial_date, delivery_date)
        )
        conn.commit()
        new_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()
        return redirect(url_for('print_measurement', measurement_id=new_id))

    conn.close()
    return render_template('add_measurement.html', customer=cust,
                           garment_fields=GARMENT_FIELDS, field_key=field_key,
                           today=datetime.now().strftime('%Y-%m-%d'), shop=SHOP_NAME)


@app.route('/measurement/<int:measurement_id>/edit', methods=['GET', 'POST'])
def edit_measurement(measurement_id):
    conn = get_db()
    m = conn.execute("SELECT * FROM measurements WHERE id = ?", (measurement_id,)).fetchone()
    if not m:
        conn.close()
        return "Not found", 404
    cust = conn.execute("SELECT * FROM customers WHERE id = ?", (m['customer_id'],)).fetchone()

    if request.method == 'POST':
        garment_type  = m['garment_type']
        order_date    = request.form.get('order_date') or m['order_date']
        trial_date    = request.form.get('trial_date', '').strip() or None
        delivery_date = request.form.get('delivery_date', '').strip() or None
        notes         = request.form.get('notes', '').strip()
        fields        = GARMENT_FIELDS.get(garment_type, [])
        measurements  = {f: request.form.get(field_key(f), '').strip() for f in fields}
        new_image     = save_upload(request.files.get('fabric_photo'), f"fabric_{m['customer_id']}")
        image         = new_image if new_image else m['image']

        conn.execute(
            "UPDATE measurements SET measurements=?, notes=?, image=?, order_date=?, trial_date=?, delivery_date=? WHERE id=?",
            (json.dumps(measurements), notes, image, order_date, trial_date, delivery_date, measurement_id)
        )
        conn.commit()
        conn.close()
        return redirect(url_for('print_measurement', measurement_id=measurement_id))

    existing = json.loads(m['measurements'])
    conn.close()
    return render_template('edit_measurement.html', customer=cust,
                           measurement=m, existing=existing,
                           garment_fields=GARMENT_FIELDS, field_key=field_key,
                           shop=SHOP_NAME)


@app.route('/measurement/<int:measurement_id>/print')
def print_measurement(measurement_id):
    conn = get_db()
    m    = conn.execute("SELECT * FROM measurements WHERE id = ?", (measurement_id,)).fetchone()
    if not m:
        conn.close()
        return "Not found", 404
    cust = conn.execute("SELECT * FROM customers WHERE id = ?", (m['customer_id'],)).fetchone()
    conn.close()
    data = {
        'id':                   m['id'],
        'garment_type':         m['garment_type'],
        'measurements':         json.loads(m['measurements']),
        'notes':                m['notes'],
        'image':                m['image'],
        'order_date':           m['order_date'],
        'trial_date':           m['trial_date'],
        'delivery_date':        m['delivery_date'],
        'status':               m['status'] or 'pending',
        'trial_done_date':      m['trial_done_date'],
        'actual_delivery_date': m['actual_delivery_date'],
    }
    return render_template('print_measurement.html', customer=cust, measurement=data, shop=SHOP_NAME)


@app.route('/measurement/<int:measurement_id>/delete', methods=['POST'])
def delete_measurement(measurement_id):
    conn = get_db()
    m    = conn.execute("SELECT customer_id FROM measurements WHERE id = ?", (measurement_id,)).fetchone()
    if m:
        customer_id = m['customer_id']
        conn.execute("DELETE FROM measurements WHERE id = ?", (measurement_id,))
        conn.commit()
    conn.close()
    return redirect(url_for('customer', customer_id=customer_id))


@app.route('/customer/<int:customer_id>/delete', methods=['POST'])
def delete_customer(customer_id):
    conn = get_db()
    conn.execute("DELETE FROM measurements WHERE customer_id = ?", (customer_id,))
    conn.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))


@app.route('/customer/<int:customer_id>/receipt', methods=['GET', 'POST'])
def receipt(customer_id):
    conn = get_db()
    cust = conn.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()
    if not cust:
        conn.close()
        return "Customer not found", 404

    if request.method == 'POST':
        selected_ids  = request.form.getlist('measurement_ids')
        advance       = float(request.form.get('advance', 0) or 0)

        if not selected_ids:
            conn.close()
            return redirect(url_for('receipt', customer_id=customer_id))

        placeholders = ','.join('?' * len(selected_ids))
        rows = conn.execute(
            f"SELECT * FROM measurements WHERE id IN ({placeholders}) AND customer_id = ? ORDER BY id",
            selected_ids + [customer_id]
        ).fetchall()

        items, total = [], 0
        for row in rows:
            garment = row['garment_type']
            mdata   = json.loads(row['measurements'])
            qty_key = GARMENT_QTY_FIELD.get(garment, '')
            qty     = int(mdata.get(qty_key) or 1)
            # Kurta with Astar = Yes gets a different price and label
            if garment == 'kurta' and mdata.get('Astar') == 'Yes':
                label = 'kurta-astar'
                rate  = STITCHING_COST['kurta_astar']
            else:
                label = garment
                rate  = STITCHING_COST.get(garment, 0)
            amount  = qty * rate
            total  += amount
            items.append({'garment': label, 'qty': qty, 'rate': rate, 'amount': amount,
                          'measurement_id': row['id']})

        balance       = total - advance
        slip_no       = f"#{min(int(i) for i in selected_ids):04d}"
        dates         = [r['delivery_date'] for r in rows if r['delivery_date']]
        delivery_date = max(dates) if dates else None
        today         = datetime.now().strftime('%Y-%m-%d')

        conn.execute(
            "INSERT INTO receipts (customer_id, slip_no, receipt_date, items, total, advance, balance, delivery_date) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (customer_id, slip_no, today, json.dumps(items), total, advance, balance, delivery_date)
        )
        conn.commit()
        new_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()
        return redirect(url_for('print_receipt', receipt_id=new_id))

    # GET — show all measurements with checkboxes
    all_rows = conn.execute(
        "SELECT * FROM measurements WHERE customer_id = ? ORDER BY order_date DESC, id DESC",
        (customer_id,)
    ).fetchall()

    slip_items = []
    for row in all_rows:
        garment = row['garment_type']
        mdata   = json.loads(row['measurements'])
        qty_key = GARMENT_QTY_FIELD.get(garment, '')
        qty     = int(mdata.get(qty_key) or 1)
        if garment == 'kurta' and mdata.get('Astar') == 'Yes':
            label = 'kurta-astar'
            rate  = STITCHING_COST['kurta_astar']
        else:
            label = garment
            rate  = STITCHING_COST.get(garment, 0)
        slip_items.append({
            'id':         row['id'],
            'garment':    label,
            'order_date': row['order_date'],
            'qty':        qty,
            'rate':       rate,
            'amount':     qty * rate,
        })

    conn.close()
    return render_template('receipt.html', customer=cust, slip_items=slip_items, shop=SHOP_NAME)


@app.route('/receipt/<int:receipt_id>/delete', methods=['POST'])
def delete_receipt(receipt_id):
    conn = get_db()
    r = conn.execute("SELECT customer_id FROM receipts WHERE id = ?", (receipt_id,)).fetchone()
    if r:
        customer_id = r['customer_id']
        conn.execute("DELETE FROM receipts WHERE id = ?", (receipt_id,))
        conn.commit()
    conn.close()
    return redirect(url_for('customer', customer_id=customer_id))


@app.route('/receipt/<int:receipt_id>/print')
def print_receipt(receipt_id):
    conn = get_db()
    r = conn.execute("SELECT * FROM receipts WHERE id = ?", (receipt_id,)).fetchone()
    if not r:
        conn.close()
        return "Receipt not found", 404
    cust = conn.execute("SELECT * FROM customers WHERE id = ?", (r['customer_id'],)).fetchone()
    conn.close()
    data = {
        'id':            r['id'],
        'slip_no':       r['slip_no'],
        'receipt_date':  r['receipt_date'],
        'line_items':    json.loads(r['items']),
        'total':         r['total'],
        'advance':       r['advance'],
        'balance':       r['balance'],
        'delivery_date': r['delivery_date'],
    }
    return render_template('print_receipt.html', customer=cust, receipt=data,
                           shop=SHOP_NAME, shop_address=SHOP_ADDRESS,
                           shop_contacts=SHOP_CONTACTS)


@app.route('/measurement/<int:measurement_id>/update-status', methods=['POST'])
def update_status(measurement_id):
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data'}), 400

    new_status = data.get('new_status')
    trial_done_date     = data.get('trial_done_date') or None
    actual_delivery_date = data.get('actual_delivery_date') or None

    valid_statuses = ['pending', 'in_progress', 'trial_ready', 'delivered']
    if new_status not in valid_statuses:
        return jsonify({'success': False, 'error': 'Invalid status'}), 400

    status_order = {'pending': 0, 'in_progress': 1, 'trial_ready': 2, 'delivered': 3}

    conn = get_db()
    m = conn.execute("SELECT status FROM measurements WHERE id = ?", (measurement_id,)).fetchone()
    if not m:
        conn.close()
        return jsonify({'success': False, 'error': 'Not found'}), 404

    current = m['status'] or 'pending'
    if status_order.get(new_status, -1) <= status_order.get(current, 0):
        conn.close()
        return jsonify({'success': False, 'error': 'Cannot move backward'}), 400

    conn.execute(
        "UPDATE measurements SET status=?, "
        "trial_done_date=COALESCE(?, trial_done_date), "
        "actual_delivery_date=COALESCE(?, actual_delivery_date) WHERE id=?",
        (new_status, trial_done_date, actual_delivery_date, measurement_id)
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/calendar')
def calendar_view():
    month_str = request.args.get('month', datetime.now().strftime('%Y-%m'))
    try:
        year, month = map(int, month_str.split('-'))
        if not (1 <= month <= 12):
            raise ValueError
    except Exception:
        year, month = datetime.now().year, datetime.now().month

    _, days_in_month = cal_module.monthrange(year, month)
    month_start = f"{year:04d}-{month:02d}-01"
    month_end   = f"{year:04d}-{month:02d}-{days_in_month:02d}"
    today_str   = datetime.now().strftime('%Y-%m-%d')

    conn = get_db()
    rows = conn.execute("""
        SELECT m.id, m.customer_id, m.garment_type, m.status,
               m.trial_date, m.delivery_date, m.trial_done_date, m.actual_delivery_date,
               c.name AS customer_name, c.mobile AS customer_mobile
        FROM measurements m
        JOIN customers c ON m.customer_id = c.id
        WHERE (m.status IS NULL OR m.status != 'delivered')
        AND (
            (m.trial_date    BETWEEN ? AND ?)
            OR (m.delivery_date BETWEEN ? AND ?)
        )
        ORDER BY m.trial_date, m.delivery_date
    """, (month_start, month_end, month_start, month_end)).fetchall()
    conn.close()

    from collections import defaultdict
    day_orders = defaultdict(list)

    for row in rows:
        status = row['status'] or 'pending'
        base = {
            'id':            row['id'],
            'customer_id':   row['customer_id'],
            'customer_name': row['customer_name'],
            'customer_mobile': row['customer_mobile'] or '',
            'garment_type':  row['garment_type'],
            'status':        status,
            'slip_no':       f"#{row['id']:04d}",
            'trial_date':    row['trial_date'],
            'delivery_date': row['delivery_date'],
        }
        if row['trial_date'] and month_start <= row['trial_date'] <= month_end:
            o = dict(base)
            o['event_type'] = 'trial'
            o['overdue'] = row['trial_date'] < today_str
            day_orders[row['trial_date']].append(o)
        if row['delivery_date'] and month_start <= row['delivery_date'] <= month_end:
            o = dict(base)
            o['event_type'] = 'delivery'
            o['overdue'] = row['delivery_date'] < today_str
            day_orders[row['delivery_date']].append(o)

    # Build calendar weeks (each day is a date object or None for out-of-month)
    first = date_obj(year, month, 1)
    last  = date_obj(year, month, days_in_month)
    start = first - timedelta(days=first.weekday())
    end   = last  + timedelta(days=(6 - last.weekday()))

    weeks = []
    cur = start
    while cur <= end:
        week = []
        for _ in range(7):
            week.append(cur if cur.month == month else None)
            cur += timedelta(days=1)
        weeks.append(week)

    # Prev / next month
    if month == 1:
        prev_month = f"{year-1:04d}-12"
    else:
        prev_month = f"{year:04d}-{month-1:02d}"
    if month == 12:
        next_month = f"{year+1:04d}-01"
    else:
        next_month = f"{year:04d}-{month+1:02d}"

    month_name = datetime(year, month, 1).strftime('%B %Y')

    return render_template('calendar.html',
        shop=SHOP_NAME,
        year=year, month=month,
        month_name=month_name,
        weeks=weeks,
        day_orders=dict(day_orders),
        prev_month=prev_month,
        next_month=next_month,
        today=today_str,
    )


@app.after_request
def no_cache(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    return response

if __name__ == '__main__':
    init_db()
    print("\n  Tailor App running at: http://localhost:5000\n")
    app.run(host='0.0.0.0', port=5000, debug=False)
