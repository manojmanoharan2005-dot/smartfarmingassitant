from flask import Blueprint, render_template, session, request, jsonify
from utils.auth import login_required
import requests
import random
import json
import os
from datetime import datetime, timedelta
from math import radians, cos, sin, asin, sqrt

market_bp = Blueprint('market', __name__)

# Data.gov.in API configuration
API_KEY = "579b464db66ec23bdd000001cdd3946e44ce4aad7209ff7b23ac571b"
API_BASE_URL = "https://api.data.gov.in/resource/35985678-0d79-46b4-9ed6-6f13308a1d24"

# Market data file path
MARKET_DATA_FILE = 'data/market_prices.json'

# District coordinates file path
DISTRICT_COORDS_FILE = 'data/district_coordinates.json'

# States and districts file path
STATES_DISTRICTS_FILE = 'states_districts.json'

def load_states_districts():
    """Load all Indian states and districts from JSON file"""
    try:
        if os.path.exists(STATES_DISTRICTS_FILE):
            with open(STATES_DISTRICTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"Error loading states_districts.json: {str(e)}")
        return {}

def load_district_coordinates():
    """Load district coordinates mapping"""
    try:
        if os.path.exists(DISTRICT_COORDS_FILE):
            with open(DISTRICT_COORDS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"Error loading district coordinates: {str(e)}")
        return {}

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates in km using Haversine formula"""
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    km = 6371 * c
    return km

def load_daily_market_data():
    """Load market data from daily scheduled updates"""
    try:
        if os.path.exists(MARKET_DATA_FILE):
            with open(MARKET_DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('data', []), data.get('last_updated')
        return [], None
    except Exception as e:
        print(f"Error loading market data: {str(e)}")
        return [], None

def format_scheduled_data_for_display(scheduled_data):
    """Format the scheduled AI-generated data for display"""
    market_data = []
    for record in scheduled_data:
        try:
            current_price = record.get('modal_price', 0)
            min_price = record.get('min_price', current_price)
            max_price = record.get('max_price', current_price)
            
            # Calculate change and prediction
            change_percent = random.uniform(-5, 10)
            prediction_7d = current_price * (1 + random.uniform(0.05, 0.15))
            trend = 'Bullish' if change_percent > 0 else 'Bearish'
            
            # Calculate kg prices (1 quintal = 100 kg)
            current_price_kg = current_price / 100
            min_price_kg = min_price / 100
            max_price_kg = max_price / 100
            prediction_7d_kg = prediction_7d / 100
            
            market_data.append({
                'commodity': record.get('commodity', 'Unknown'),
                'mandi': record.get('market', 'Unknown Market'),
                'state': record.get('state', 'Tamil Nadu'),
                'district': record.get('district', ''),
                'current_price': int(current_price),
                'current_price_kg': round(current_price_kg, 2),
                'unit': record.get('unit', 'Quintal'),
                'change': f"{'+' if change_percent > 0 else ''}{change_percent:.1f}%",
                'trend': trend,
                'prediction_7d': int(prediction_7d),
                'prediction_7d_kg': round(prediction_7d_kg, 2),
                'confidence': random.randint(80, 95),
                'min_price': int(min_price),
                'max_price': int(max_price),
                'min_price_kg': round(min_price_kg, 2),
                'max_price_kg': round(max_price_kg, 2),
                'arrival': record.get('arrival', 'N/A'),
                'arrival_date': record.get('price_date', datetime.now().strftime('%Y-%m-%d'))
            })
        except Exception as e:
            print(f"Error formatting record: {e}")
            continue
    
    return market_data

def fetch_mandi_prices(state=None, limit=None):
    """Fetch mandi prices - first try scheduled data, then fallback to API"""
    try:
        # First, try to load from scheduled daily updates
        scheduled_data, last_updated = load_daily_market_data()
        
        if scheduled_data:
            print(f"📊 Using scheduled market data from: {last_updated}")
            formatted_data = format_scheduled_data_for_display(scheduled_data)
            
            # Filter by state if requested
            if state and state != 'All States':
                formatted_data = [d for d in formatted_data if d['state'] == state]
            
            # Return all data (no limit) so district filtering works correctly
            return formatted_data
        
        # Fallback to API if no scheduled data
        print("⚠️ No scheduled data found, falling back to API")
        return fetch_mandi_prices_from_api(state, limit)
        
    except Exception as e:
        print(f"Error in fetch_mandi_prices: {str(e)}")
        return fetch_mandi_prices_from_api(state, limit)

def fetch_mandi_prices_from_api(state=None, limit=20):
    """Original API fetch method as fallback"""
    try:
        params = {
            'api-key': API_KEY,
            'format': 'json',
            'limit': 100,  # Fetch more records to filter
            'offset': 0
        }
        
        # Add state filter if provided - this API supports filters[State]
        if state and state != 'All States':
            params['filters[State]'] = state
        
        response = requests.get(API_BASE_URL, params=params, timeout=10)
        print(f"API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            records = data.get('records', [])
            print(f"Total records fetched: {len(records)}")
            
            # If no records found after filtering, return empty
            if len(records) == 0:
                print(f"No records found for state: {state}")
                return []
            
            # Process and format the data
            market_data = []
            for record in records[:limit]:  # Take requested number of records
                try:
                    # API field names may vary - check modal_price, Modal_Price, or Price
                    modal_price = record.get('Modal_Price') or record.get('modal_price') or record.get('Price', '0')
                    if modal_price == '' or modal_price is None:
                        continue
                    current_price = float(modal_price)
                    
                    if current_price == 0:
                        continue
                    
                    # Simulate price change and prediction for demo
                    change_percent = random.uniform(-5, 10)
                    prediction_7d = current_price * (1 + random.uniform(0.05, 0.15))
                    trend = 'Bullish' if change_percent > 0 else 'Bearish'
                    
                    min_price_val = record.get('Min_Price') or record.get('min_price') or modal_price
                    max_price_val = record.get('Max_Price') or record.get('max_price') or modal_price
                    
                    # Calculate kg prices (1 quintal = 100 kg)
                    current_price_kg = current_price / 100
                    prediction_7d_kg = prediction_7d / 100
                    min_price_kg = float(min_price_val) / 100 if min_price_val else current_price_kg
                    max_price_kg = float(max_price_val) / 100 if max_price_val else current_price_kg
                    
                    market_data.append({
                        'commodity': record.get('Commodity') or record.get('commodity', 'Unknown'),
                        'mandi': record.get('Market_Name') or record.get('market', 'Unknown Mandi'),
                        'state': record.get('State') or record.get('state', ''),
                        'district': record.get('District') or record.get('district', ''),
                        'current_price': int(current_price),
                        'current_price_kg': round(current_price_kg, 2),
                        'unit': 'per quintal',
                        'change': f"{'+' if change_percent > 0 else ''}{change_percent:.1f}%",
                        'trend': trend,
                        'prediction_7d': int(prediction_7d),
                        'prediction_7d_kg': round(prediction_7d_kg, 2),
                        'confidence': random.randint(75, 95),
                        'min_price': int(float(min_price_val)) if min_price_val else int(current_price),
                        'max_price': int(float(max_price_val)) if max_price_val else int(current_price),
                        'min_price_kg': round(min_price_kg, 2),
                        'max_price_kg': round(max_price_kg, 2),
                        'arrival_date': record.get('Arrival_Date') or record.get('arrival_date', 'N/A')
                    })
                except (ValueError, TypeError) as e:
                    print(f"Error processing record: {e}, Record: {record}")
                    continue
            
            print(f"Successfully processed {len(market_data)} market records")
            return market_data if len(market_data) > 0 else []
        else:
            print(f"API returned status code: {response.status_code}")
            return []
            
    except requests.exceptions.RequestException as e:
        print(f"API Request Error: {e}")
        return []
    except Exception as e:
        print(f"Error fetching market data: {e}")
        import traceback
        traceback.print_exc()
        return []

@market_bp.route('/market-watch')
@login_required
def market_watch():
    from datetime import datetime
    user_name = session.get('user_name', 'Guest')
    user_state = session.get('user_state', None)
    
    # Load all states and districts from JSON file
    states_districts = load_states_districts()
    all_states = sorted(list(states_districts.keys()))
    
    # Get state, district, and commodity filters from query params
    selected_state = request.args.get('state', user_state if user_state else 'All States')
    selected_district = request.args.get('district', 'All Districts')
    selected_commodity = request.args.get('commodity', 'All')
    commodity_search = request.args.get('commodity_search', '').strip()
    
    # If commodity_search is provided, use it for filtering
    if commodity_search:
        selected_commodity = commodity_search
    
    print(f"Fetching market data for state: {selected_state}, district: {selected_district}, commodity: {selected_commodity}")
    
    # Fetch real-time market data (no limit to show all commodities)
    market_data = fetch_mandi_prices(state=selected_state if selected_state != 'All States' else None, limit=None)
    
    # Ensure market_data is always a list, never None
    if market_data is None:
        market_data = []
    
    # Get districts for the selected state
    if selected_state != 'All States' and selected_state in states_districts:
        districts = sorted(states_districts[selected_state])
    else:
        # Get unique districts from market data
        districts = set()
        for item in market_data:
            if item.get('district'):
                districts.add(item['district'])
        districts = sorted(list(districts))
    
    # Filter by district if selected
    if selected_district != 'All Districts' and selected_district:
        market_data = [item for item in market_data if item.get('district') == selected_district]
    
    # Filter by commodity if selected (supports partial matching for search)
    if selected_commodity and selected_commodity != 'All':
        # Case-insensitive partial match for search functionality
        market_data = [item for item in market_data if selected_commodity.lower() in item.get('commodity', '').lower()]
    
    # Categorize into vegetables and fruits - MUST match generate_market_data.py exactly
    vegetables_list = [
        "Potato", "Tomato", "Onion", "Carrot", "Cabbage", "Cauliflower",
        "Spinach", "Brinjal (Eggplant)", "Lady's Finger (Okra)", "Beetroot",
        "Radish", "Capsicum", "Pumpkin", "Bottle Gourd", "Bitter Gourd",
        "Ridge Gourd", "Green Peas", "Beans", "Mushroom", "Corn"
    ]
    
    fruits_list = [
        "Apple", "Banana", "Mango", "Orange", "Grapes", "Papaya",
        "Pineapple", "Guava", "Watermelon", "Muskmelon", "Pomegranate",
        "Strawberry", "Cherry", "Kiwi", "Lemon", "Pear", "Peach",
        "Plum", "Coconut", "Custard Apple"
    ]
    
    vegetables = [item for item in market_data if item.get('commodity') in vegetables_list]
    fruits = [item for item in market_data if item.get('commodity') in fruits_list]
    
    # Format current date
    current_date = datetime.now().strftime('%B %d, %Y')
    
    # Calculate statistics for the new UI
    total_records = len(market_data) if market_data else 28400
    total_states = len(all_states)
    
    # Count bullish and bearish trends
    bullish_count = 0
    bearish_count = 0
    for item in market_data:
        change_val = item.get('change', 0)
        if isinstance(change_val, str):
            change_val = float(change_val.replace('%', '').replace('+', ''))
        if change_val >= 0:
            bullish_count += 1
        else:
            bearish_count += 1
    
    # Format market data for new template (add 'change' as number and price fields)
    for item in market_data:
        change_val = item.get('change', 0)
        if isinstance(change_val, str):
            item['change'] = float(change_val.replace('%', '').replace('+', ''))
        # Ensure price fields exist for template
        if 'modal_price' not in item and 'current_price' in item:
            item['modal_price'] = item['current_price']
        if 'min_price' not in item and 'current_price' in item:
            item['min_price'] = int(item['current_price'] * 0.9)
        if 'max_price' not in item and 'current_price' in item:
            item['max_price'] = int(item['current_price'] * 1.1)
    
    return render_template('market_watch.html', 
                         user_name=user_name,
                         market_data=market_data,
                         vegetables=vegetables,
                         fruits=fruits,
                         states=all_states,
                         states_districts=states_districts,
                         selected_state=selected_state,
                         districts=districts,
                         selected_district=selected_district,
                         selected_commodity=selected_commodity,
                         current_date=current_date,
                         total_records=total_records,
                         total_states=total_states,
                         bullish_count=bullish_count,
                         bearish_count=bearish_count,
                         vegetable_count=len(vegetables_list),
                         fruit_count=len(fruits_list))

@market_bp.route('/api/refresh-prices')
@login_required
def refresh_prices():
    """API endpoint to refresh market prices"""
    state = request.args.get('state', None)
    market_data = fetch_mandi_prices(state=state if state != 'All States' else None)
    
    # Ensure market_data is always a list
    if market_data is None:
        market_data = []
    
    return jsonify({
        'success': True,
        'data': market_data
    })

@market_bp.route('/api/nearby-mandis')
@login_required
def nearby_mandis():
    """API endpoint to find nearby mandis based on user location"""
    try:
        user_lat = float(request.args.get('lat'))
        user_lon = float(request.args.get('lon'))
        radius = float(request.args.get('radius', 50))  # Default 50km radius
        
        # Use scheduled data instead of making API call to avoid rate limiting
        scheduled_data, last_updated = load_daily_market_data()
        
        if not scheduled_data:
            return jsonify({
                'success': False,
                'error': 'No market data available'
            }), 400
        
        # Load district coordinates
        district_coords = load_district_coordinates()
        
        nearby_markets = []
        
        # Calculate actual distances based on district/city locations
        for record in scheduled_data:
            try:
                current_price = record.get('modal_price', 0)
                
                if current_price == 0:
                    continue
                
                # Get district and state
                district = record.get('district', '')
                state = record.get('state', '')
                market = record.get('market', '')
                
                # Try to find coordinates for the district or extract city from market name
                coords = None
                
                # First try: match district in coordinates
                if state in district_coords and district in district_coords[state]:
                    coords = district_coords[state][district]
                # Second try: check if market name contains a known city
                elif state in district_coords:
                    for city_name in district_coords[state].keys():
                        if city_name.lower() in market.lower():
                            coords = district_coords[state][city_name]
                            break
                
                # If no coordinates found, skip this market
                if not coords:
                    continue
                
                # Calculate actual distance
                distance = calculate_distance(user_lat, user_lon, coords['lat'], coords['lon'])
                
                # Only include markets within the radius
                if distance > radius:
                    continue
                
                # Calculate kg price
                current_price_kg = current_price / 100
                
                nearby_markets.append({
                    'commodity': record.get('commodity', 'Unknown'),
                    'mandi': record.get('market', 'Unknown Mandi'),
                    'state': state,
                    'district': district,
                    'current_price': int(current_price),
                    'current_price_kg': round(current_price_kg, 2),
                    'distance': round(distance, 1),
                    'arrival_date': record.get('price_date', 'N/A')
                })
            except (ValueError, TypeError) as e:
                print(f"Error processing record: {e}")
                continue
        
        # Sort by distance
        nearby_markets.sort(key=lambda x: x['distance'])
        
        # If no nearby markets found within radius, show a helpful message
        if len(nearby_markets) == 0:
            return jsonify({
                'success': True,
                'data': [],
                'count': 0,
                'message': f'No mandis found within {radius}km. Try increasing the search radius.'
            })
        
        return jsonify({
            'success': True,
            'data': nearby_markets[:15],  # Return top 15 nearest
            'count': len(nearby_markets)
        })
    
    except Exception as e:
        print(f"Error in nearby_mandis: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
@market_bp.route('/api/price-trend/<commodity>')
@login_required
def price_trend(commodity):
    """API endpoint to get price trend data for a commodity"""
    state = request.args.get('state', None)
    district = request.args.get('district', None)
    days = int(request.args.get('days', 7))
    
    # Load scheduled data
    scheduled_data, _ = load_daily_market_data()
    
    if not scheduled_data:
        return jsonify({
            'success': False,
            'error': 'No market data available'
        }), 400
    
    # Filter data for the commodity
    commodity_data = [item for item in scheduled_data if item.get('commodity') == commodity]
    
    if not commodity_data:
        return jsonify({
            'success': False,
            'error': f'No trend data found for {commodity}'
        }), 404

    # Keep track of what level of data we're using
    data_level = 'national'
    
    # Try to filter by district first
    if district and district != 'All Districts':
        district_data = [item for item in commodity_data if item.get('district') == district]
        if district_data:
            commodity_data = district_data
            data_level = 'district'
        else:
            # Fallback to state if district not found
            if state and state != 'All States':
                state_data = [item for item in commodity_data if item.get('state') == state]
                if state_data:
                    commodity_data = state_data
                    data_level = 'state'
    elif state and state != 'All States':
        state_data = [item for item in commodity_data if item.get('state') == state]
        if state_data:
            commodity_data = state_data
            data_level = 'state'
        
    # Group by date and calculate average modal price
    # In a real app, this would query a historical database
    # Here, we simulate some historical data based on the current variations if not enough dates exist
    
    # Get unique dates from the data
    dates_found = sorted(list(set([item.get('price_date') for item in commodity_data if item.get('price_date')])))
    
    trend_data = []
    
    # If we have multiple dates, use them
    if len(dates_found) > 1:
        for date_str in dates_found[-days:]:
            date_items = [item for item in commodity_data if item.get('price_date') == date_str]
            if date_items:
                avg_modal = sum([item.get('modal_price', 0) for item in date_items]) / len(date_items)
                avg_min = sum([item.get('min_price', 0) for item in date_items]) / len(date_items)
                avg_max = sum([item.get('max_price', 0) for item in date_items]) / len(date_items)
                
                trend_data.append({
                    'date': date_str,
                    'modal_price': int(avg_modal),
                    'min_price': int(avg_min),
                    'max_price': int(avg_max)
                })
    else:
        # Simulate 7 days of historical data if only one date or no dated data exists
        # This is for demo purposes to show a nice chart
        base_item = commodity_data[0]
        base_price = base_item.get('modal_price', 2500)
        base_date = datetime.now()
        
        for i in range(days-1, -1, -1):
            date_obj = base_date - timedelta(days=i)
            # Add some random variation (-3% to +5%)
            variation = 1 + (random.uniform(-0.03, 0.05) * (days - i) / days)
            sim_price = int(base_price * variation)
            
            trend_data.append({
                'date': date_obj.strftime('%Y-%m-%d'),
                'modal_price': sim_price,
                'min_price': int(sim_price * 0.9),
                'max_price': int(sim_price * 1.1)
            })
            
    # Calculate trend analysis
    first_price = trend_data[0]['modal_price']
    last_price = trend_data[-1]['modal_price']
    change_percent = ((last_price - first_price) / first_price) * 100
    
    direction = 'Rising' if change_percent > 2 else 'Falling' if change_percent < -2 else 'Stable'
    recommendation = 'Wait' if direction == 'Rising' else 'Sell Now' if direction == 'Falling' else 'Sell Now'
    
    return jsonify({
        'success': True,
        'commodity': commodity,
        'data_level': data_level,
        'trend_data': trend_data,
        'analysis': {
            'direction': direction,
            'change_percent': round(change_percent, 1),
            'recommendation': recommendation,
            'confidence': random.randint(75, 92)
        }
    })
