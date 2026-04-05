# SHUBHAM NX — Tailor Shop Management App

A tailor shop management system to track customers, measurements, and billing.

**Stack:** Python 3 / Flask / SQLite / Bootstrap 5.3.3

---

## Run Locally

```bash
pip install -r requirements.txt
python app.py
```

App runs at `http://localhost:5000`

---

## PythonAnywhere Deployment

### 1. Clone the repo

Open a Bash console on PythonAnywhere and run:

```bash
git clone https://github.com/ShubhamNX-9616/tailor-app.git
cd tailor-app
pip3 install --user -r requirements.txt
```

### 2. Add a new web app

- Go to **Web** tab → **Add a new web app**
- Select **Manual Configuration**
- Select **Python 3.10**

### 3. Configure the WSGI file

- In the Web tab, click the **WSGI configuration file** link
- Delete all existing content and paste:

```python
import sys
import os

path = '/home/YOUR_PYTHONANYWHERE_USERNAME/tailor-app'
if path not in sys.path:
    sys.path.append(path)

from app import app as application
```

Replace `YOUR_PYTHONANYWHERE_USERNAME` with your actual PythonAnywhere username.

### 4. Set source code directory

In the Web tab under **Code**:
- Source code: `/home/YOUR_PYTHONANYWHERE_USERNAME/tailor-app`
- Working directory: `/home/YOUR_PYTHONANYWHERE_USERNAME/tailor-app`

### 5. Set static files

In the Web tab under **Static files**:

| URL       | Path                                                  |
|-----------|-------------------------------------------------------|
| `/static/` | `/home/YOUR_PYTHONANYWHERE_USERNAME/tailor-app/static` |

### 6. Reload

Click the **Reload** button at the top of the Web tab.

### 7. Visit your app

```
https://YOUR_PYTHONANYWHERE_USERNAME.pythonanywhere.com
```

---

## Updating the app

SSH into PythonAnywhere Bash console and run:

```bash
cd ~/tailor-app
git pull
```

Then click **Reload** in the Web tab.
