from flask import (
    Flask, render_template, request, redirect,
    session, abort, url_for, send_from_directory, flash
)
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import check_password_hash, generate_password_hash
import os
import datetime
from ai_matcher import final_match

app = Flask(__name__)
app.secret_key = "super-secret-key"

# ---------- MIDDLEWARE: BLOCK CHECK & SESSION INVALIDATION ----------
@app.before_request
def check_user_status():
    # Define exempt paths that don't need status checks
    exempt_paths = ['/login', '/logout', '/account-blocked', '/request-unblock', '/static', '/auth/check-status']
    
    # Skip if path starts with exempt prefix (simple string check)
    for path in exempt_paths:
        if request.path.startswith(path) or request.path == "/":
            return

    # If user is logged in, check status
    if "user_id" in session:
        db = get_db()
        if db is None:
            return
            
        user = db.users.find_one({"_id": ObjectId(session["user_id"])})
        
        # DEBUG LOGGING
        print(f"Middleware Check: UserID={session['user_id']} | Found={bool(user)} | Active={user.get('is_active') if user else 'N/A'}")

        if not user:
            # User in session but not in DB? specific edge case. Log them out.
            session.clear()
            return redirect("/login")
        
        # If user is blocked (is_active=False)
        if not user.get("is_active", True):
            print(">> BLOCKING USER - REDIRECTING <<")
            # Force clear any residual 'next' redirects
            return redirect("/account-blocked")

        # Session Version Check
        db_version = user.get("session_version", 0)
        session_ver = session.get("session_version", 0)
        
        if db_version != session_ver:
             print(f"Session Version Mismatch: DB={db_version} vs Session={session_ver} - Logging Out")
             session.clear()
             return redirect("/login")

# ---------- STATUS POLLER ----------
@app.route("/auth/check-status")
def check_status():
    if "user_id" not in session:
        return {"status": "unauthorized"}, 401
        
    db = get_db()
    user = db.users.find_one({"_id": ObjectId(session["user_id"])})
    
    if not user:
        return {"status": "invalid_session"}, 401
        
    if not user.get("is_active", True):
        return {"status": "inactive"}
        
    # Check session version
    if user.get("session_version", 0) != session.get("session_version", 0):
         return {"status": "invalid_session"}
         
    return {"status": "active"}

# ---------- PREVENT CACHING ----------
@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

# ---------- UPLOAD CONFIG ----------
os.makedirs("uploads/lost", exist_ok=True)
os.makedirs("uploads/found", exist_ok=True)
os.makedirs("uploads/profile", exist_ok=True)

# ---------- MONGODB CONNECTION ----------
MONGO_URI = "mongodb+srv://devsquaddatabase:DEVSQUAD@devsquad239.jdlqcko.mongodb.net/?appName=devsquad239"
DB_NAME = "lost_found_ai"

import certifi

def get_db():
    try:
        # Added tlsAllowInvalidCertificates=True to help with some network/firewall configurations
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000, tlsCAFile=certifi.where(), tlsAllowInvalidCertificates=True)
        return client[DB_NAME]
    except Exception as e:
        print(f"Database Connection Error: {e}")
        return None

# Check connection immediately
try:
    print("Connecting to MongoDB...")
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000, tlsCAFile=certifi.where(), tlsAllowInvalidCertificates=True)
    client.server_info() # Trigger connection
    print("SUCCESS: Connected to MongoDB Atlas!")
except Exception as e:
    print(f"\nCRITICAL ERROR: Could not connect to MongoDB.\nDetails: {e}\n\nPOSSIBLE CAUSES:\n1. YOUR IP IS NOT WHITELISTED IN MONGODB ATLAS (Most Likely)\n2. Firewall/VPN is blocking the connection.\n")

# ---------- SUPER ADMIN AUTO-CREATION ----------
SEED_ADMINS = [
    {"name": "ADULA MAHENDHAR", "email": "yadavmahendhar65@gmail.com", "password": "Mahi@2004"},
    {"name": "MOHAMMED YASEEN", "email": "yaseenashu18@gmail.com", "password": "Ysn@1874"},
    {"name": "MILKURI VAMSHI KRISHNA", "email": "krishnapatel000813@gmail.com", "password": "White666@2005"},
    {"name": "BURRA RIKSHITH", "email": "burrarikshith@gmail.com", "password": "Bikky@0027"}
]

def init_super_admin():
    db = get_db()
    if db is None:
        return

    users_col = db.users
    
    for admin in SEED_ADMINS:
        existing_user = users_col.find_one({"email": admin["email"]})
        if not existing_user:
            password_hash = generate_password_hash(admin["password"])
            super_admin_data = {
                "name": admin["name"],
                "email": admin["email"],
                "password": password_hash,
                "role": "super_admin",
                "is_active": True,
                "profile_completed": True,
                "college": "System",
                "study": "Administration",
                "phone": "0000000000",
                "profile_photo": None,
                "created_at": datetime.datetime.utcnow()
            }
            users_col.insert_one(super_admin_data)
            print(f"Seeded Super Admin: {admin['email']}")

# Initialize user on startup
init_super_admin()

# ---------- HELPER FUNCTIONS ----------
def get_user_by_id(user_id_str):
    if not user_id_str:
        return None
    db = get_db()
    try:
        return db.users.find_one({"_id": ObjectId(user_id_str)})
    except:
        return None

# ---------- SERVE UPLOADS ----------
@app.route("/uploads/<path:filename>")
def uploaded_files(filename):
    return send_from_directory("uploads", filename)

# ---------- LOGIN ----------
@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        db = get_db()
        # Find user regardless of active status
        user = db.users.find_one({"email": email})

        if user and check_password_hash(user["password"], password):
            session["user_id"] = str(user["_id"])
            session["role"] = user["role"]
            session["session_version"] = user.get("session_version", 0)

            # If blocked, redirect to blocked page immediately
            if not user.get("is_active", True):
                return redirect("/account-blocked")

            if user["role"] == "super_admin":
                return redirect("/superadmin/dashboard")
            elif user["role"] == "admin":
                return redirect("/admin/dashboard")
            else:
                return redirect("/user/dashboard")

        return "Invalid credentials"

    return render_template("login.html")

# ---------- SIGNUP ----------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        db = get_db()
        
        # Check if email exists
        if db.users.find_one({"email": email}):
            return "Email already registered"

        try:
            db.users.insert_one({
                "name": name,
                "email": email,
                "password": password,
                "role": "user",
                "is_active": True,
                "profile_completed": False,
                "created_at": datetime.datetime.utcnow()
            })
        except Exception as e:
            return f"Signup error: {e}"

        return redirect("/login")

    return render_template("signup.html")

# ---------- SUPER ADMIN DASHBOARD ----------
@app.route("/superadmin/dashboard")
def superadmin_dashboard():
    if session.get("role") != "super_admin":
        abort(403)
    return render_template("superadmin_dashboard.html")

# ---------- USER PROFILE ----------
@app.route("/user/profile", methods=["GET", "POST"])
def user_profile():
    if session.get("role") != "user":
        abort(403)

    db = get_db()
    user_id = session["user_id"]

    if request.method == "POST":
        college = request.form["college"]
        study = request.form["study"]
        phone = request.form["phone"]
        photo = request.files.get("photo")

        update_data = {
            "college": college,
            "study": study,
            "phone": phone,
            "profile_completed": True
        }

        if photo and photo.filename:
            # Generate unique filename to prevent caching
            timestamp = int(datetime.datetime.utcnow().timestamp())
            filename = f"{user_id}_{timestamp}_{photo.filename}"
            photo_path = f"uploads/profile/{filename}"
            photo.save(photo_path)
            update_data["profile_photo"] = photo_path

        db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )

        return redirect("/user/dashboard")

    user = db.users.find_one({"_id": ObjectId(user_id)})
    # Add id alias for templates expecting 'id' or '_id'
    if user:
        user['id'] = str(user['_id'])
        
    return render_template("user_profile.html", user=user)

# ---------- USER DASHBOARD ----------
@app.route("/user/dashboard")
def user_dashboard():
    if session.get("role") != "user":
        abort(403)

    db = get_db()
    user = db.users.find_one({"_id": ObjectId(session["user_id"])})
    if user:
        user['id'] = str(user['_id'])

    # LEADERBOARD LOGIC
    # aggregated counts of 'matched' or 'resolved' found items
    pipeline = [
        {"$match": {"status": {"$in": ["matched", "resolved"]}}},
        {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ]
    formatted_leaderboard = []
    
    try:
        leaderboard_data = list(db.found_items.aggregate(pipeline))
        
        for entry in leaderboard_data:
            finder = db.users.find_one({"_id": entry["_id"]})
            if finder:
                formatted_leaderboard.append({
                    "name": finder["name"],
                    "count": entry["count"],
                    "photo": finder.get("profile_photo")
                })
    except Exception as e:
        print(f"Leaderboard Error: {e}")

    return render_template("user_dashboard.html", user=user, leaderboard=formatted_leaderboard)

# ---------- USER HISTORY ----------
@app.route("/user/history")
def user_history():
    if session.get("role") != "user":
        abort(403)

    db = get_db()
    user = db.users.find_one({"_id": ObjectId(session["user_id"])})
    if user:
        user['id'] = str(user['_id'])

    # Fetch User History
    lost_items = list(db.lost_items.find({"user_id": ObjectId(session["user_id"])}).sort("created_at", -1))
    found_items = list(db.found_items.find({"user_id": ObjectId(session["user_id"])}).sort("created_at", -1))
    
    # Simple Match Check (for indicators)
    # Note: This is a basic check. In production, store match status in DB.
    # We check if this user's lost item matches ANY found item in the system (and vice versa)
    all_lost = list(db.lost_items.find())
    all_found = list(db.found_items.find())

    for item in lost_items:
        item['has_match'] = False
        item['id'] = str(item['_id'])
        if item.get('status') == 'lost': # Only check active items
             for found in all_found:
                 if final_match(item, found)['final_score'] >= 0.5:
                     item['has_match'] = True
                     break
    
    for item in found_items:
        item['has_match'] = False
        item['id'] = str(item['_id'])
        if item.get('status') == 'found':
             for lost in all_lost:
                 if final_match(lost, item)['final_score'] >= 0.5:
                     item['has_match'] = True
                     break

    return render_template("user_history.html", user=user, lost_items=lost_items, found_items=found_items)

# ---------- ACTIONS: RESOLVE ----------
@app.route("/user/item/resolve/<item_type>/<item_id>")
def resolve_item(item_type, item_id):
    if session.get("role") != "user":
        abort(403)

    db = get_db()
    collection = db.lost_items if item_type == 'lost' else db.found_items
    
    # Ownership Check
    item = collection.find_one({"_id": ObjectId(item_id), "user_id": ObjectId(session["user_id"])})
    if not item:
        flash("Item not found.")
        return redirect("/user/history")
    
    new_status = 'resolved'
    collection.update_one({"_id": ObjectId(item_id)}, {"$set": {"status": new_status}})
    flash("Item marked as resolved.")
    return redirect("/user/history")

# ---------- GENERIC PROFILE HANDLER ----------
def handle_profile_update(role, template_name, redirect_url):
    if session.get("role") != role:
        abort(403)

    db = get_db()
    user_id = session["user_id"]

    if request.method == "POST":
        college = request.form.get("college", "")
        study = request.form.get("study", "")
        phone = request.form.get("phone", "")
        photo = request.files.get("photo")

        update_data = {
            "college": college,
            "study": study,
            "phone": phone,
            "profile_completed": True
        }

        if photo and photo.filename:
            # Generate unique filename to prevent caching
            timestamp = int(datetime.datetime.utcnow().timestamp())
            filename = f"{user_id}_{timestamp}_{photo.filename}"
            photo_path = f"uploads/profile/{filename}"
            photo.save(photo_path)
            update_data["profile_photo"] = photo_path

        db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        return redirect(redirect_url)

    user = db.users.find_one({"_id": ObjectId(user_id)})
    if user:
        user['user_id'] = str(user['_id']) # For templates using user.user_id
        user['id'] = str(user['_id'])

    return render_template(template_name, user=user)

# ---------- ADMIN PROFILE ----------
@app.route("/admin/profile", methods=["GET", "POST"])
def admin_profile():
    return handle_profile_update("admin", "admin_profile.html", "/admin/dashboard")

# ---------- SUPER ADMIN PROFILE ----------
@app.route("/superadmin/profile", methods=["GET", "POST"])
def super_admin_profile():
    return handle_profile_update("super_admin", "superadmin_profile.html", "/superadmin/dashboard")


# ---------- PROFILE CHECK ----------
def profile_complete():
    db = get_db()
    user = db.users.find_one({"_id": ObjectId(session["user_id"])})
    return user.get("profile_completed", False) if user else False

# ---------- REPORT LOST ----------
@app.route("/user/report-lost", methods=["GET", "POST"])
def report_lost():
    if session.get("role") != "user":
        abort(403)

    if not profile_complete():
        return redirect("/user/profile")

    if request.method == "POST":
        item_name = request.form.get("item_name")
        description = request.form.get("description")
        location = request.form.get("location")
        date = request.form.get("date")
        images = request.files.getlist("image")

        # Validation
        if not item_name or not description or not location or not date:
            flash("Please fill in all required fields.")
            return redirect(request.url)

        saved_image_paths = []
        for image in images:
             if image and image.filename and len(saved_image_paths) < 5:
                # Generate unique filename
                timestamp = int(datetime.datetime.utcnow().timestamp())
                filename = f"{session['user_id']}_{timestamp}_{image.filename}"
                image_path = f"uploads/lost/{filename}"
                image.save(image_path)
                saved_image_paths.append(image_path)
        
        # Backward compatibility: use first image as 'image_path'
        primary_image_path = saved_image_paths[0] if saved_image_paths else None

        if not primary_image_path:
             flash("At least one image is required.")
             return redirect(request.url)

        db = get_db()
        db.lost_items.insert_one({
            "user_id": ObjectId(session["user_id"]),
            "item_name": item_name,
            "description": description,
            "location": location,
            "date": date,
            "image_path": primary_image_path, # Main image for AI/Admin
            "additional_images": saved_image_paths, # All images
            "status": "lost",
            "created_at": datetime.datetime.utcnow()
        })
        return redirect("/user/dashboard")

    return render_template("report_lost.html")

# ---------- REPORT FOUND ----------
@app.route("/user/report-found", methods=["GET", "POST"])
def report_found():
    if session.get("role") != "user":
        abort(403)

    if not profile_complete():
        return redirect("/user/profile")

    if request.method == "POST":
        item_name = request.form.get("item_name")
        description = request.form.get("description")
        location = request.form.get("location")
        date = request.form.get("date")
        images = request.files.getlist("image")

        # Validation
        if not item_name or not description or not location or not date:
            flash("Please fill in all required fields.")
            return redirect(request.url)

        saved_image_paths = []
        for image in images:
             if image and image.filename and len(saved_image_paths) < 5:
                # Generate unique filename
                timestamp = int(datetime.datetime.utcnow().timestamp())
                filename = f"{session['user_id']}_{timestamp}_{image.filename}"
                image_path = f"uploads/found/{filename}"
                image.save(image_path)
                saved_image_paths.append(image_path)
        
        # Backward compatibility
        primary_image_path = saved_image_paths[0] if saved_image_paths else None

        if not primary_image_path:
             flash("At least one image is required.")
             return redirect(request.url)

        db = get_db()
        db.found_items.insert_one({
            "user_id": ObjectId(session["user_id"]),
            "item_name": item_name,
            "description": description,
            "location": location,
            "date": date,
            "image_path": primary_image_path, # Main image
            "additional_images": saved_image_paths, # All images
            "status": "found",
            "created_at": datetime.datetime.utcnow()
        })
        return redirect("/user/dashboard")

    return render_template("report_found.html")

# ---------- ADMIN SETTINGS ----------
@app.route("/admin/settings")
def admin_settings():
    if session.get("role") not in ["admin", "super_admin"]:
        abort(403)
    return render_template("admin_settings.html")

# ---------- ADMIN DASHBOARD & MATCHING ----------
@app.route("/admin/dashboard")
def admin_dashboard():
    if session.get("role") not in ["admin", "super_admin"]:
        abort(403)

    db = get_db()
    
    # Fetch all items
    lost_items = list(db.lost_items.find({"status": "lost"}))
    found_items = list(db.found_items.find({"status": "found"}))

    # Add id aliases for template compatibility
    for item in lost_items:
        item['lost_id'] = str(item['_id'])
    for item in found_items:
        item['found_id'] = str(item['_id'])

    matches = []
    for lost in lost_items:
        for found in found_items:
            if lost.get("image_path") and found.get("image_path"):
                score = final_match(lost, found)
                if score["final_score"] >= 0.5:
                    matches.append({
                        "lost": lost,
                        "found": found,
                        "score": score
                    })

    return render_template(
        "admin_dashboard.html",
        lost_items=lost_items,
        found_items=found_items,
        matches=matches
    )

# ---------- ADMIN: APPROVE MATCH ----------
@app.route("/admin/approve-match/<lost_id>/<found_id>")
def approve_match(lost_id, found_id):
    if session.get("role") not in ["admin", "super_admin"]:
        abort(403)
        
    db = get_db()
    
    # 1. Update Status
    db.lost_items.update_one({"_id": ObjectId(lost_id)}, {"$set": {"status": "matched"}})
    db.found_items.update_one({"_id": ObjectId(found_id)}, {"$set": {"status": "matched"}})
    
    # 2. Get User IDs
    lost_item = db.lost_items.find_one({"_id": ObjectId(lost_id)})
    found_item = db.found_items.find_one({"_id": ObjectId(found_id)})
    
    if lost_item and found_item:
        # 3. Create Chat Room
        chat_data = {
            "lost_item_id": ObjectId(lost_id),
            "found_item_id": ObjectId(found_id),
            "lost_user_id": lost_item["user_id"],
            "found_user_id": found_item["user_id"],
            "item_name": lost_item["item_name"], # Common name
            "status": "active",
            "created_at": datetime.datetime.utcnow(),
            "messages": [
                {
                    "sender": "system",
                    "text": "Match approved! You can now chat to arrange the return.",
                    "timestamp": datetime.datetime.utcnow()
                }
            ]
        }
        db.chats.insert_one(chat_data)
        
    flash("Match confirmed! Users have been notified.")
    return redirect("/admin/dashboard")

# ---------- CHAT SYSTEM ----------
@app.route("/user/chats")
def my_chats():
    if session.get("role") != "user":
        abort(403)
        
    db = get_db()
    current_user_id = ObjectId(session["user_id"])
    
    # Find chats where user is either lost_user or found_user
    chats = list(db.chats.find({
        "$or": [
            {"lost_user_id": current_user_id},
            {"found_user_id": current_user_id}
        ]
    }).sort("created_at", -1))
    
    for chat in chats:
        chat['id'] = str(chat['_id'])
        # Determine role for display
        if chat["lost_user_id"] == current_user_id:
            chat["role_desc"] = "Reporter (Lost)"
        else:
            chat["role_desc"] = "Finder (Found)"
            
    return render_template("user_chats.html", chats=chats)

@app.route("/user/chat/<chat_id>", methods=["GET", "POST"])
def view_chat(chat_id):
    if session.get("role") != "user":
        abort(403)
        
    db = get_db()
    chat = db.chats.find_one({"_id": ObjectId(chat_id)})
    
    if not chat:
        return "Chat not found", 404
        
    # Verify Access
    current_user_id = ObjectId(session["user_id"])
    if current_user_id not in [chat["lost_user_id"], chat["found_user_id"]]:
        abort(403)
        
    if request.method == "POST":
        text = request.form.get("message")
        if text:
            msg = {
                "sender_id": current_user_id,
                "text": text,
                "timestamp": datetime.datetime.utcnow()
            }
            db.chats.update_one(
                {"_id": ObjectId(chat_id)},
                {"$push": {"messages": msg}}
            )
            return redirect(f"/user/chat/{chat_id}")
            
    # Prepare messages for template
    for msg in chat["messages"]:
        if msg.get("sender") == "system":
            msg["is_me"] = False
            msg["is_system"] = True
        else:
            msg["is_system"] = False
            msg["is_me"] = (msg["sender_id"] == current_user_id)
            
    return render_template("chat_room.html", chat=chat, current_user_id=current_user_id)
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------- ADMIN : USERS MANAGEMENT ----------
@app.route("/admin/users")
def admin_users():
    if session.get("role") not in ["admin", "super_admin"]:
        abort(403)

    db = get_db()
    users = list(db.users.find())
    
    # Process users for template
    for u in users:
        u['user_id'] = str(u['_id'])
    
    return render_template("admin_users.html", users=users)

# ---------- ACTIVATE USER ----------
@app.route("/admin/user/activate/<user_id>")
def activate_user(user_id):
    if session.get("role") not in ["admin", "super_admin"]:
        abort(403)

    db = get_db()
    target_user = db.users.find_one({"_id": ObjectId(user_id)})
    
    if not target_user:
        return "User not found", 404

    # Permission Check
    if session["role"] == "admin" and target_user["role"] == "super_admin":
        return "Access Denied: Admins cannot activate Super Admins", 403

    db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"is_active": True}})
    
    # Log Action
    db.admin_actions.insert_one({
        "admin_id": ObjectId(session["user_id"]),
        "target_user_id": ObjectId(user_id),
        "action": "activate",
        "reason": "Manual Activation",
        "timestamp": datetime.datetime.utcnow()
    })

    flash(f"User {target_user.get('name', 'User')} has been activated.")
    return redirect("/admin/users")


# ---------- DEACTIVATE USER ----------
# ---------- DEACTIVATE USER ----------
@app.route("/admin/user/deactivate/<user_id>", methods=["POST"])
def deactivate_user(user_id):
    if session.get("role") not in ["admin", "super_admin"]:
        abort(403)

    db = get_db()
    target_user = db.users.find_one({"_id": ObjectId(user_id)})
    
    if not target_user:
        return "User not found", 404

    # Permission Check
    if session["role"] == "admin" and target_user["role"] == "super_admin":
        return "Access Denied: Admins cannot deactivate Super Admins", 403

    reason = request.form.get("reason", "No reason provided")
    
    update_data = {
        "is_active": False,
        "blocked_at": datetime.datetime.utcnow(),
        "block_reason": reason,
    }
    
    # Increment session version to force logout
    current_version = target_user.get("session_version", 0)
    update_data["session_version"] = current_version + 1

    db.users.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})
    
    # Log Action
    db.admin_actions.insert_one({
        "admin_id": ObjectId(session["user_id"]),
        "target_user_id": ObjectId(user_id),
        "action": "deactivate",
        "reason": reason,
        "timestamp": datetime.datetime.utcnow()
    })
    
    # Confirm action
    flash(f"User {target_user.get('name', 'User')} has been deactivated. They will be logged out immediately.")
    return redirect("/admin/users")

# ---------- BLOCKED USER ROUTES ----------
@app.route("/account-blocked")
def account_blocked():
    # If user is somehow active, send them back to dashboard
    if "user_id" in session:
        db = get_db()
        user = db.users.find_one({"_id": ObjectId(session["user_id"])})
        if user and user.get("is_active", True):
            return redirect("/user/dashboard")
    return render_template("account_blocked.html")

@app.route("/request-unblock", methods=["POST"])
def request_unblock():
    if "user_id" not in session:
        return redirect("/login")

    reason = request.form.get("reason")
    proof = request.files.get("proof")
    
    proof_path = None
    if proof and proof.filename:
        # Secure filename with timestamp
        timestamp = int(datetime.datetime.utcnow().timestamp())
        filename = f"proof_{session['user_id']}_{timestamp}_{proof.filename}"
        proof_path = f"uploads/profile/{filename}" # Store in uploads/profile for now or create new folder
        proof.save(proof_path)

    db = get_db()
    
    # Rate limit check (optional simple check: pending request exists?)
    existing_request = db.unblock_requests.find_one({
        "user_id": ObjectId(session["user_id"]),
        "status": "pending"
    })
    
    if existing_request:
        flash("You already have a pending request.")
        return redirect("/account-blocked")

    db.unblock_requests.insert_one({
        "user_id": ObjectId(session["user_id"]),
        "reason": reason,
        "proof_path": proof_path,
        "status": "pending",
        "created_at": datetime.datetime.utcnow()
    })
    
    flash("Unblock request submitted successfully.")
    return redirect("/account-blocked")

# ---------- SUPER ADMIN : UNBLOCK REQUESTS ----------
@app.route("/superadmin/unblock-requests")
def view_unblock_requests():
    if session.get("role") != "super_admin":
        abort(403)

    db = get_db()
    
    # Aggregate to join with user details
    pipeline = [
        {"$sort": {"created_at": -1}},
        {"$lookup": {
            "from": "users",
            "localField": "user_id",
            "foreignField": "_id",
            "as": "user_info"
        }},
        {"$unwind": "$user_info"}
    ]
    
    requests = list(db.unblock_requests.aggregate(pipeline))
    
    # Format IDs for template
    for req in requests:
        req['id'] = str(req['_id'])
        req['user_id'] = str(req['user_id'])
        
    return render_template("superadmin_requests.html", requests=requests)

@app.route("/superadmin/request/<request_id>/<action>", methods=["POST"])
def process_unblock_request(request_id, action):
    if session.get("role") != "super_admin":
        abort(403)
        
    db = get_db()
    req = db.unblock_requests.find_one({"_id": ObjectId(request_id)})
    
    if not req:
        return "Request not found", 404
        
    if action == "approve":
        # 1. Activate User
        db.users.update_one({"_id": req["user_id"]}, {"$set": {"is_active": True}})
        # 2. Update Request Status
        db.unblock_requests.update_one({"_id": ObjectId(request_id)}, {"$set": {"status": "approved"}})
        flash("User unblocked successfully.")
        
    elif action == "reject":
        # Update Request Status
        db.unblock_requests.update_one({"_id": ObjectId(request_id)}, {"$set": {"status": "rejected"}})
        flash("Unblock request rejected.")
        
    return redirect("/superadmin/unblock-requests")

# ---------- CREATE ADMIN (Super Admin Only) ----------
@app.route("/superadmin/create-admin", methods=["GET", "POST"])
def create_admin():
    if session.get("role") != "super_admin":
        abort(403)

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        db = get_db()
        if db.users.find_one({"email": email}):
             return "Email already exists"

        db.users.insert_one({
            "name": name,
            "email": email,
            "password": password,
            "role": "admin",
            "is_active": True,
            "profile_completed": True,
            "college": "Admin Dept",
            "study": "Administration",
            "phone": "0000000000",
            "created_at": datetime.datetime.utcnow()
        })
        return redirect("/superadmin/dashboard")

    return render_template("create_admin.html")

# ---------- ERROR ----------
@app.errorhandler(403)
def forbidden(e):
    return "403 Forbidden – Access Denied", 403

# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True)
