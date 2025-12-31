from datetime import datetime
import os
import json
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB Atlas connection string from environment variable
MONGODB_URI = os.getenv('MONGODB_URI')

# Local file-based storage directory and file paths (used when MongoDB is not available)
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
DATA_DIR = os.path.abspath(DATA_DIR)

USERS_FILE = os.path.join(DATA_DIR, 'users.json')
CROPS_FILE = os.path.join(DATA_DIR, 'crops.json')
FERTILIZERS_FILE = os.path.join(DATA_DIR, 'fertilizers.json')
DISEASES_FILE = os.path.join(DATA_DIR, 'diseases.json')
GROWING_FILE = os.path.join(DATA_DIR, 'growing_activities.json')
EQUIPMENT_FILE = os.path.join(DATA_DIR, 'equipment.json')
NOTIFICATIONS_FILE = os.path.join(DATA_DIR, 'notifications.json')
EXPENSES_FILE = os.path.join(DATA_DIR, 'expenses.json')

client = None
db = None

def init_db(app):
    global client, db
    
    # Create data directory if it doesn't exist
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Initialize JSON files if they don't exist
    for file_path in [USERS_FILE, CROPS_FILE, FERTILIZERS_FILE, DISEASES_FILE, GROWING_FILE, EQUIPMENT_FILE, NOTIFICATIONS_FILE]:
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                if file_path in [EQUIPMENT_FILE, NOTIFICATIONS_FILE]:
                    json.dump([], f)
                else:
                    json.dump({}, f)
    
    print("✅ File-based database initialized successfully!")
    print("📁 Data will be stored in the 'data' directory")
    
    # Try MongoDB Atlas connection as backup (only if URI is configured)
    if MONGODB_URI:
        try:
            print("🔄 Attempting MongoDB Atlas connection...")
            client = MongoClient(MONGODB_URI, 
                               serverSelectionTimeoutMS=30000,
                               connectTimeoutMS=30000,
                               socketTimeoutMS=30000,
                               retryWrites=False)
            
            # Use myVirtualDatabase database
            db = client.myVirtualDatabase
            # Test the connection
            client.admin.command('ping')
            print("✅ Successfully connected to MongoDB Atlas!")
            print(f"📊 Using database: myVirtualDatabase")
            
            # Create indexes for better performance (if supported)
            try:
                db.users.create_index("email", unique=True)
                print("📊 Database indexes created successfully")
            except Exception as e:
                print(f"⚠️ Index creation note: {e}")
                print("   (This is normal for Atlas SQL interface)")
                
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            print("⚠️  Common issues:")
            print("   1. Check if your IP address is whitelisted in MongoDB Atlas")
            print("   2. Verify network connectivity and firewall settings")
            print("   3. Ensure Atlas SQL interface is enabled")
            print("🔧 Using file-based database for development")
            db = MockDatabase()
    else:
        print("🔧 MongoDB disabled - using file-based database")
        db = MockDatabase()

class MockDatabase:
    """Enhanced Mock database for development when MongoDB is not available"""
    def __init__(self):
        self.users_data = {}
        self.crops_data = []
        self.fertilizers_data = []
        self.diseases_data = []
        print("📝 Mock database initialized with enhanced features")
    
    @property
    def users(self):
        return MockCollection('users', self.users_data, is_dict=True)
    
    @property 
    def crops(self):
        return MockCollection('crops', self.crops_data)
        
    @property
    def fertilizers(self):
        return MockCollection('fertilizers', self.fertilizers_data)
        
    @property
    def diseases(self):
        return MockCollection('diseases', self.diseases_data)

class MockCollection:
    def __init__(self, name, data_store, is_dict=False):
        self.name = name
        self.data_store = data_store
        self.is_dict = is_dict
        
    def find_one(self, query):
        if self.is_dict and 'email' in query:
            return self.data_store.get(query['email'])
        elif '_id' in query:
            for item in self.data_store:
                if item.get('_id') == query['_id']:
                    return item
        return None
    
    def insert_one(self, data):
        import uuid
        mock_id = str(uuid.uuid4())
        data['_id'] = mock_id
        
        if self.is_dict and 'email' in data:
            self.data_store[data['email']] = data
        else:
            self.data_store.append(data)
            
        return type('MockResult', (), {'inserted_id': mock_id})()
    
    def find(self, query):
        if 'user_id' in query:
            return [item for item in self.data_store if item.get('user_id') == query['user_id']]
        return list(self.data_store) if not self.is_dict else list(self.data_store.values())
    
    def delete_one(self, query):
        if '_id' in query:
            self.data_store = [item for item in self.data_store if item.get('_id') != query['_id']]
            return type('MockResult', (), {'deleted_count': 1})()
        return type('MockResult', (), {'deleted_count': 0})()
    
    def create_index(self, field, unique=False):
        print(f"Mock index created for {field} (unique: {unique})")

def get_db():
    return db

# User model functions
def create_user(name, email, password, phone, state, district):
    users = db.users
    user_data = {
        'name': name,
        'email': email,
        'password': password,
        'phone': phone,
        'state': state,
        'district': district,
        'created_at': datetime.utcnow(),
        'saved_crops': [],
        'saved_fertilizers': [],
        'disease_history': []
    }
    result = users.insert_one(user_data)
    print(f"👤 User created: {name} ({email})")
    return result

def find_user_by_email(email):
    if hasattr(db, 'users'):
        users = db.users
        user = users.find_one({'email': email})
    else:
        # Handle mock database
        user = db.users.find_one({'email': email}) if db else None
    
    if user:
        print(f"🔍 User found: {email}")
    return user

def find_user_by_phone(phone):
    """Find user by phone number"""
    if hasattr(db, 'users'):
        users = db.users
        # Get all users and search for phone
        all_users = users.find({})
        for user in all_users:
            if user.get('phone') == phone:
                print(f"🔍 User found with phone: {phone}")
                return user
    return None

def update_user_password(email, new_password):
    """Update user password by email"""
    try:
        # Load users from file
        with open(USERS_FILE, 'r') as f:
            users_db = json.load(f)
        
        # Find and update user
        for user_id, user in users_db.items():
            if user.get('email') == email:
                user['password'] = new_password
                # Save back to file
                with open(USERS_FILE, 'w') as f:
                    json.dump(users_db, f, indent=2, default=str)
                print(f"🔐 Password updated for user: {email}")
                return True
        
        print(f"⚠️ User not found: {email}")
        return False
    except Exception as e:
        print(f"❌ Error updating password: {e}")
        return False

def find_user_by_id(user_id):
    try:
        if hasattr(db, 'users') and db:
            users = db.users
            
            # Try with ObjectId first (for MongoDB)
            try:
                from bson.objectid import ObjectId
                user = users.find_one(
                    {'_id': ObjectId(user_id)}, 
                    {'password': 0}  # Exclude password field
                )
                if user:
                    return user
            except:
                pass
            
            # Try with string ID (for file-based storage)
            user = users.find_one({'_id': user_id})
            if user:
                # Remove password from result
                user_copy = user.copy()
                user_copy.pop('password', None)
                return user_copy
                
    except Exception as e:
        print(f"Error fetching user by ID: {e}")
    
    # If user not found, return None
    return None

# Mock functions for development
def save_crop_recommendation(user_id, crop_data, timeline_data):
    print(f"🌱 Crop recommendation saved for user {user_id}: {crop_data['crop_name']}")
    return type('MockResult', (), {'inserted_id': 'mock_crop_id'})()

def get_user_crops(user_id):
    # Return some mock data for testing
    return [
        {
            '_id': 'crop1',
            'crop_name': 'Rice',
            'probability': 0.89,
            'sowing_date': '2024-01-15',
            'status': 'monitoring'
        }
    ]

def delete_crop(crop_id):
    print(f"🗑️ Crop deleted: {crop_id}")
    return type('MockResult', (), {'deleted_count': 1})()

def save_fertilizer_recommendation(user_id, fertilizer_data):
    """Save fertilizer recommendation to file"""
    import uuid
    try:
        # Load existing fertilizers
        with open(FERTILIZERS_FILE, 'r') as f:
            fertilizer_db = json.load(f)
        
        # Generate unique ID
        fertilizer_id = str(uuid.uuid4())
        fertilizer_data['_id'] = fertilizer_id
        fertilizer_data['user_id'] = user_id
        fertilizer_data['saved_at'] = datetime.utcnow().isoformat()
        
        # Save fertilizer
        if user_id not in fertilizer_db:
            fertilizer_db[user_id] = []
        
        fertilizer_db[user_id].append(fertilizer_data)
        
        # Write back to file
        with open(FERTILIZERS_FILE, 'w') as f:
            json.dump(fertilizer_db, f, indent=2)
        
        print(f"🧪 Fertilizer recommendation saved for user {user_id}: {fertilizer_data.get('name')}")
        return type('MockResult', (), {'inserted_id': fertilizer_id})()
    except Exception as e:
        print(f"Error saving fertilizer: {e}")
        return None

def get_user_fertilizers(user_id):
    """Get user's saved fertilizers from file"""
    import uuid
    try:
        with open(FERTILIZERS_FILE, 'r') as f:
            fertilizer_db = json.load(f)
        
        # Get user's fertilizers
        user_fertilizers = fertilizer_db.get(user_id, [])
        
        # Add _id to fertilizers that don't have one
        needs_save = False
        for fert in user_fertilizers:
            if '_id' not in fert:
                fert['_id'] = str(uuid.uuid4())
                needs_save = True
        
        # Save back if we added any IDs
        if needs_save:
            fertilizer_db[user_id] = user_fertilizers
            with open(FERTILIZERS_FILE, 'w') as f:
                json.dump(fertilizer_db, f, indent=2)
        
        return user_fertilizers
    except Exception as e:
        print(f"Error loading fertilizers: {e}")
        return []

def delete_fertilizer_recommendation(fertilizer_id, user_id):
    """Delete a fertilizer recommendation from file"""
    try:
        # Load existing fertilizers
        with open(FERTILIZERS_FILE, 'r') as f:
            fertilizer_db = json.load(f)
        
        # Get user's fertilizers
        user_fertilizers = fertilizer_db.get(user_id, [])
        
        # Find and remove the fertilizer
        initial_count = len(user_fertilizers)
        user_fertilizers = [f for f in user_fertilizers if f.get('_id') != fertilizer_id]
        
        if len(user_fertilizers) < initial_count:
            # Fertilizer was found and removed
            fertilizer_db[user_id] = user_fertilizers
            
            # Write back to file
            with open(FERTILIZERS_FILE, 'w') as f:
                json.dump(fertilizer_db, f, indent=2)
            
            print(f"🗑️ Successfully deleted fertilizer {fertilizer_id} for user {user_id}")
            return True
        else:
            print(f"⚠️ Fertilizer {fertilizer_id} not found for user {user_id}")
            return False
            
    except Exception as e:
        print(f"Error deleting fertilizer: {e}")
        return False

def save_disease_detection(user_id, disease_data):
    print(f"🦠 Disease detection saved for user {user_id}: {disease_data['disease_name']}")
    return type('MockResult', (), {'inserted_id': 'mock_disease_id'})()

def get_user_diseases(user_id):
    # Return some mock data for testing
    return [
        {
            '_id': 'disease1',
            'disease_name': 'Tomato Blight',
            'plant_type': 'Tomato',
            'confidence': 0.87,
            'detected_at': datetime.utcnow()
        }
    ]

def save_growing_activity(activity_data):
    """Save a growing activity to database"""
    import uuid
    try:
        # Load existing activities
        with open(GROWING_FILE, 'r') as f:
            growing_data = json.load(f)
        
        # Generate unique ID
        activity_id = str(uuid.uuid4())
        activity_data['_id'] = activity_id
        
        # Save activity
        user_id = activity_data.get('user_id')
        if user_id not in growing_data:
            growing_data[user_id] = []
        
        growing_data[user_id].append(activity_data)
        
        # Write back to file
        with open(GROWING_FILE, 'w') as f:
            json.dump(growing_data, f, indent=2)
        
        print(f"🌱 Growing activity saved: {activity_data.get('crop_display_name')} [ID: {activity_id}]")
        return type('MockResult', (), {'inserted_id': activity_id})()
    except Exception as e:
        print(f"Error saving growing activity: {e}")
        return None

def get_user_growing_activities(user_id, status='active'):
    """Get user's growing activities"""
    import uuid
    try:
        with open(GROWING_FILE, 'r') as f:
            growing_data = json.load(f)
        
        # Get user's activities
        user_activities = growing_data.get(user_id, [])
        
        # Add _id to activities that don't have one
        needs_save = False
        for activity in user_activities:
            if '_id' not in activity:
                activity['_id'] = str(uuid.uuid4())
                needs_save = True
        
        # Save back if we added any IDs
        if needs_save:
            growing_data[user_id] = user_activities
            with open(GROWING_FILE, 'w') as f:
                json.dump(growing_data, f, indent=2)
        
        # Filter by status if specified
        if status:
            user_activities = [a for a in user_activities if a.get('status') == status]
        
        return user_activities
    except Exception as e:
        print(f"Error loading growing activities: {e}")
        return []

def update_growing_activity(activity_id, user_id, update_data):
    """Update growing activity with new data (stage, notes, tasks)"""
    try:
        print(f"💾 DB: Updating activity {activity_id} for user {user_id}")
        print(f"💾 DB: Update data: {update_data}")
        
        # Load existing activities
        with open(GROWING_FILE, 'r') as f:
            growing_data = json.load(f)
        
        print(f"💾 DB: Loaded data for {len(growing_data)} users")
        
        # Get user's activities
        user_activities = growing_data.get(user_id, [])
        print(f"💾 DB: User has {len(user_activities)} activities")
        
        # Find and update the activity
        activity_found = False
        for i, activity in enumerate(user_activities):
            print(f"💾 DB: Checking activity {i}: {activity.get('_id')} == {activity_id}?")
            if activity.get('_id') == activity_id or activity.get('id') == activity_id:
                print(f"💾 DB: Match found! Updating...")
                # Update the activity fields
                if 'current_stage' in update_data:
                    print(f"💾 DB: Updating stage: {activity.get('current_stage')} -> {update_data['current_stage']}")
                    user_activities[i]['current_stage'] = update_data['current_stage']
                if 'progress' in update_data:
                    print(f"💾 DB: Updating progress: {activity.get('progress')} -> {update_data['progress']}")
                    user_activities[i]['progress'] = update_data['progress']
                if 'notes' in update_data:
                    print(f"💾 DB: Updating notes")
                    user_activities[i]['notes'] = update_data['notes']
                if 'completed_tasks' in update_data:
                    print(f"💾 DB: Updating tasks")
                    user_activities[i]['completed_tasks'] = update_data['completed_tasks']
                
                user_activities[i]['updated_at'] = datetime.now().isoformat()
                activity_found = True
                break
        
        if activity_found:
            growing_data[user_id] = user_activities
            
            # Write back to file
            with open(GROWING_FILE, 'w') as f:
                json.dump(growing_data, f, indent=2)
            
            print(f"✅ Successfully updated activity {activity_id} for user {user_id}")
            print(f"💾 DB: File saved to {GROWING_FILE}")
            return True
        else:
            print(f"⚠️ Activity {activity_id} not found for user {user_id}")
            return False
            
    except Exception as e:
        print(f"Error updating activity: {e}")
        import traceback
        traceback.print_exc()
        return False

def delete_growing_activity(activity_id, user_id):
    """Delete a growing activity"""
    try:
        # Load existing activities
        with open(GROWING_FILE, 'r') as f:
            growing_data = json.load(f)
        
        # Get user's activities
        user_activities = growing_data.get(user_id, [])
        
        # Find and remove the activity
        initial_count = len(user_activities)
        user_activities = [a for a in user_activities if a.get('_id') != activity_id]
        
        if len(user_activities) < initial_count:
            # Activity was found and removed
            growing_data[user_id] = user_activities
            
            # Write back to file
            with open(GROWING_FILE, 'w') as f:
                json.dump(growing_data, f, indent=2)
            
            print(f"🗑️ Successfully deleted activity {activity_id} for user {user_id}")
            return True
        else:
            print(f"⚠️ Activity {activity_id} not found for user {user_id}")
            return False
            
    except Exception as e:
        print(f"Error deleting activity: {e}")
        return False

def get_dashboard_notifications(user_id):
    """Get notifications for dashboard"""
    from datetime import datetime, timedelta
    notifications = []
    
    # Get active growing activities
    activities = get_user_growing_activities(user_id)
    
    for activity in activities:
        # Check for upcoming tasks
        start_date = datetime.fromisoformat(activity['created_at'])
        days_passed = (datetime.now() - start_date).days
        weeks_passed = days_passed // 7
        
        # Find pending tasks for current week
        for task in activity['tasks']:
            if task['week'] == weeks_passed + 1:
                notifications.append({
                    'type': 'task',
                    'crop': activity['crop_display_name'],
                    'message': f"Week {task['week']} task: {task['task']}",
                    'priority': 'high',
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
        
        # Check if harvest is near (within 7 days)
        harvest_date = datetime.strptime(activity['harvest_date'], '%Y-%m-%d')
        days_to_harvest = (harvest_date - datetime.now()).days
        
        if 0 <= days_to_harvest <= 7:
            notifications.append({
                'type': 'harvest',
                'crop': activity['crop_display_name'],
                'message': f"Harvest ready in {days_to_harvest} days!",
                'priority': 'high',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
    
    # Add persistent notifications
    persistent = get_persistent_notifications(user_id)
    notifications.extend(persistent)
    
    return notifications

def add_notification(user_id, type, message, priority='medium', title=None, data=None):
    """Save a user notification to file"""
    try:
        notifications = []
        if os.path.exists(NOTIFICATIONS_FILE):
            with open(NOTIFICATIONS_FILE, 'r') as f:
                notifications = json.load(f)
        
        # Determine title if not provided
        if not title:
            if type == 'equipment' or type == 'rental_request':
                title = 'Equipment Rental'
            elif type == 'system':
                title = 'System Alert'
            else:
                title = 'Notification'

        new_notif = {
            'id': str(datetime.now().timestamp()),
            'user_id': str(user_id),
            'type': type,
            'title': title,
            'message': message,
            'priority': priority,
            'created_at': datetime.now().isoformat(),
            'read': False,
            'data': data or {}
        }
        notifications.append(new_notif)
        
        with open(NOTIFICATIONS_FILE, 'w') as f:
            json.dump(notifications, f, indent=2)
        return True
    except Exception as e:
        print(f"Error adding notification: {e}")
        return False
        
def delete_notification(notification_id):
    """Delete a notification by ID"""
    try:
        if not os.path.exists(NOTIFICATIONS_FILE):
            return False
            
        with open(NOTIFICATIONS_FILE, 'r') as f:
            notifications = json.load(f)
            
        initial_len = len(notifications)
        notifications = [n for n in notifications if n.get('id') != notification_id]
        
        if len(notifications) < initial_len:
            with open(NOTIFICATIONS_FILE, 'w') as f:
                json.dump(notifications, f, indent=2)
            return True
        return False
    except Exception as e:
        print(f"Error deleting notification: {e}")
        return False

def update_equipment(equipment_id, update_data):
    """Update generic equipment fields"""
    try:
        with open(EQUIPMENT_FILE, 'r') as f:
            equipment = json.load(f)
        
        updated = False
        for item in equipment:
            if item.get('_id') == equipment_id:
                item.update(update_data)
                item['updated_at'] = datetime.now().isoformat()
                updated = True
                break
        
        if updated:
            with open(EQUIPMENT_FILE, 'w') as f:
                json.dump(equipment, f, indent=2)
            return True
        return False
    except Exception as e:
        print(f"Error updating equipment: {e}")
        return False
    except Exception as e:
        print(f"Error adding notification: {e}")
        return False

def get_persistent_notifications(user_id):
    """Retrieve saved notifications for a user"""
    try:
        if not os.path.exists(NOTIFICATIONS_FILE):
            return []
        with open(NOTIFICATIONS_FILE, 'r') as f:
            all_notifs = json.load(f)
            return [n for n in all_notifs if n.get('user_id') == str(user_id)]
    except Exception as e:
        print(f"Error loading notifications: {e}")
        return []

def get_all_equipment():
    """Get all listed equipment"""
    try:
        if not os.path.exists(EQUIPMENT_FILE):
            return []
        with open(EQUIPMENT_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading equipment: {e}")
        return []

def save_equipment(equipment_data):
    """Save a new equipment listing"""
    import uuid
    try:
        equipment = get_all_equipment()
        
        # Generate unique ID and basic fields
        equipment_id = str(uuid.uuid4())
        equipment_data['_id'] = equipment_id
        equipment_data['created_at'] = datetime.utcnow().isoformat()
        equipment_data['status'] = 'available'
        
        equipment.append(equipment_data)
        
        with open(EQUIPMENT_FILE, 'w') as f:
            json.dump(equipment, f, indent=2)
            
        print(f"🚜 Equipment listed: {equipment_data.get('name')} [ID: {equipment_id}]")
        return equipment_id
    except Exception as e:
        print(f"Error saving equipment: {e}")
        return None

def update_equipment_status(equipment_id, status):
    """Update equipment status (available, rented, etc.)"""
    try:
        equipment = get_all_equipment()
        for item in equipment:
            if item.get('_id') == equipment_id:
                item['status'] = status
                item['updated_at'] = datetime.utcnow().isoformat()
                break
        
        with open(EQUIPMENT_FILE, 'w') as f:
            json.dump(equipment, f, indent=2)
        return True
    except Exception as e:
        print(f"Error updating equipment status: {e}")
        return False

def save_expense(expense_data):
    """Save a new expense entry (supports both MongoDB and JSON file fallback)"""
    global db
    try:
        if db is not None:
            # Check if ObjectId is needed for user_id
            from bson import ObjectId
            if 'user_id' in expense_data and isinstance(expense_data['user_id'], str):
                try:
                    expense_data['user_id'] = ObjectId(expense_data['user_id'])
                except:
                    pass
            
            result = db.expenses.insert_one(expense_data)
            return str(result.inserted_id)
        else:
            # File fallback
            import uuid
            expense_id = str(uuid.uuid4())
            expense_data['_id'] = expense_id
            
            expenses = []
            if os.path.exists(EXPENSES_FILE):
                with open(EXPENSES_FILE, 'r') as f:
                    try:
                        expenses = json.load(f)
                    except:
                        expenses = []
            
            expenses.append(expense_data)
            with open(EXPENSES_FILE, 'w') as f:
                json.dump(expenses, f, indent=2)
            
            return expense_id
    except Exception as e:
        print(f"Error saving expense: {e}")
        return None

def get_user_expenses(user_id):
    """Get all expenses for a user (supports both MongoDB and JSON file fallback)"""
    global db
    try:
        if db is not None:
            from bson import ObjectId
            query = {'user_id': ObjectId(user_id) if isinstance(user_id, str) else user_id}
            return list(db.expenses.find(query).sort('entry_date', -1))
        else:
            # File fallback
            if os.path.exists(EXPENSES_FILE):
                with open(EXPENSES_FILE, 'r') as f:
                    try:
                        all_expenses = json.load(f)
                        return [exp for exp in all_expenses if str(exp.get('user_id')) == str(user_id)]
                    except:
                        return []
            return []
    except Exception as e:
        print(f"Error fetching expenses: {e}")
        return []
