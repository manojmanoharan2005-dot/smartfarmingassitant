from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from utils.auth import login_required
from utils.db import save_growing_activity, get_user_growing_activities, update_growing_activity, save_expense
from datetime import datetime, timedelta
import json

growing_bp = Blueprint('growing', __name__)

# Crop cultivation manuals and guidelines
CROP_MANUALS = {
    'rice': {
        'name': 'Rice',
        'icon': '🌾',
        'duration_days': 120,
        'stages': [
            {'name': 'Land Preparation', 'days': 7, 'description': 'Plow and level the field, prepare for flooding'},
            {'name': 'Seed Sowing', 'days': 1, 'description': 'Sow pre-germinated seeds in nursery'},
            {'name': 'Transplanting', 'days': 25, 'description': 'Transplant 25-day old seedlings to main field'},
            {'name': 'Vegetative Growth', 'days': 40, 'description': 'Maintain water level, apply fertilizers'},
            {'name': 'Flowering', 'days': 30, 'description': 'Monitor for pests, ensure adequate water'},
            {'name': 'Grain Filling', 'days': 30, 'description': 'Reduce water, monitor maturity'},
            {'name': 'Harvesting', 'days': 7, 'description': 'Harvest when 80-85% grains are golden yellow'}
        ],
        'tasks': [
            {'week': 1, 'task': 'Land preparation and plowing'},
            {'week': 2, 'task': 'Nursery preparation and seed sowing'},
            {'week': 4, 'task': 'Transplanting seedlings'},
            {'week': 6, 'task': 'First fertilizer application (Nitrogen)'},
            {'week': 8, 'task': 'Weed control and pest monitoring'},
            {'week': 10, 'task': 'Second fertilizer application'},
            {'week': 12, 'task': 'Monitor water levels'},
            {'week': 14, 'task': 'Check for diseases'},
            {'week': 16, 'task': 'Reduce water for grain hardening'},
            {'week': 17, 'task': 'Harvest preparation'}
        ],
        'requirements': {
            'water': 'Keep field flooded 5-10 cm throughout vegetative stage',
            'fertilizer': 'NPK 120:60:60 kg/ha in 2-3 splits',
            'temperature': '20-35°C optimal',
            'soil': 'Clayey loam with good water retention'
        }
    },
    'wheat': {
        'name': 'Wheat',
        'icon': '🌾',
        'duration_days': 130,
        'stages': [
            {'name': 'Land Preparation', 'days': 7, 'description': 'Deep plowing and leveling'},
            {'name': 'Seed Sowing', 'days': 3, 'description': 'Direct sowing with seed drill'},
            {'name': 'Germination', 'days': 10, 'description': 'First irrigation after 21 days'},
            {'name': 'Tillering', 'days': 30, 'description': 'Apply nitrogen fertilizer'},
            {'name': 'Stem Elongation', 'days': 30, 'description': 'Second fertilizer dose'},
            {'name': 'Heading & Flowering', 'days': 25, 'description': 'Critical irrigation period'},
            {'name': 'Grain Filling', 'days': 20, 'description': 'Monitor for diseases'},
            {'name': 'Maturity & Harvest', 'days': 5, 'description': 'Harvest at 80-85% maturity'}
        ],
        'tasks': [
            {'week': 1, 'task': 'Prepare seedbed and sow seeds'},
            {'week': 3, 'task': 'First irrigation (Crown Root Initiation)'},
            {'week': 5, 'task': 'Apply first nitrogen dose'},
            {'week': 7, 'task': 'Second irrigation (Tillering)'},
            {'week': 9, 'task': 'Weed control'},
            {'week': 11, 'task': 'Third irrigation (Jointing)'},
            {'week': 13, 'task': 'Apply second nitrogen dose'},
            {'week': 15, 'task': 'Fourth irrigation (Flowering)'},
            {'week': 17, 'task': 'Fifth irrigation (Milk stage)'},
            {'week': 18, 'task': 'Harvest when grain moisture is 20-25%'}
        ],
        'requirements': {
            'water': '5-6 irrigations, especially at critical stages',
            'fertilizer': 'NPK 120:60:40 kg/ha',
            'temperature': '15-25°C optimal',
            'soil': 'Well-drained loamy soil'
        }
    },
    'maize': {
        'name': 'Maize',
        'icon': '🌽',
        'duration_days': 100,
        'stages': [
            {'name': 'Land Preparation', 'days': 5, 'description': 'Prepare fine seedbed'},
            {'name': 'Sowing', 'days': 2, 'description': 'Direct sowing with proper spacing'},
            {'name': 'Germination', 'days': 7, 'description': 'Ensure adequate moisture'},
            {'name': 'Vegetative Growth', 'days': 35, 'description': 'Weed control and fertilization'},
            {'name': 'Flowering', 'days': 25, 'description': 'Critical water requirement'},
            {'name': 'Grain Filling', 'days': 20, 'description': 'Monitor for pests'},
            {'name': 'Maturity & Harvest', 'days': 6, 'description': 'Harvest when moisture is 20-25%'}
        ],
        'tasks': [
            {'week': 1, 'task': 'Land preparation and sowing'},
            {'week': 2, 'task': 'First irrigation if needed'},
            {'week': 3, 'task': 'Thinning and gap filling'},
            {'week': 4, 'task': 'Apply nitrogen fertilizer'},
            {'week': 6, 'task': 'Weed control'},
            {'week': 8, 'task': 'Second nitrogen application'},
            {'week': 10, 'task': 'Monitor for pests (stem borer)'},
            {'week': 12, 'task': 'Ensure irrigation during flowering'},
            {'week': 14, 'task': 'Check for cob maturity'},
            {'week': 15, 'task': 'Harvest and drying'}
        ],
        'requirements': {
            'water': '4-5 irrigations, critical at flowering',
            'fertilizer': 'NPK 120:60:60 kg/ha',
            'temperature': '20-30°C optimal',
            'soil': 'Well-drained loamy soil, rich in organic matter'
        }
    },
    'cotton': {
        'name': 'Cotton',
        'icon': '🌱',
        'duration_days': 180,
        'stages': [
            {'name': 'Land Preparation', 'days': 10, 'description': 'Deep plowing and ridges'},
            {'name': 'Sowing', 'days': 3, 'description': 'Sow treated seeds'},
            {'name': 'Germination', 'days': 10, 'description': 'Light irrigation'},
            {'name': 'Vegetative Growth', 'days': 60, 'description': 'Square formation'},
            {'name': 'Flowering', 'days': 45, 'description': 'Boll formation period'},
            {'name': 'Boll Development', 'days': 45, 'description': 'Monitor for pests'},
            {'name': 'Harvesting', 'days': 7, 'description': 'Multiple pickings'}
        ],
        'tasks': [
            {'week': 1, 'task': 'Prepare ridges and sow seeds'},
            {'week': 3, 'task': 'Thinning to maintain plant population'},
            {'week': 5, 'task': 'First irrigation and weeding'},
            {'week': 8, 'task': 'Apply nitrogen fertilizer'},
            {'week': 10, 'task': 'Monitor for whitefly and aphids'},
            {'week': 14, 'task': 'Apply plant growth regulators'},
            {'week': 18, 'task': 'Monitor for bollworm'},
            {'week': 22, 'task': 'Prepare for first picking'},
            {'week': 24, 'task': 'Continue multiple pickings'},
            {'week': 26, 'task': 'Final harvest'}
        ],
        'requirements': {
            'water': '6-8 irrigations depending on rainfall',
            'fertilizer': 'NPK 120:60:60 kg/ha',
            'temperature': '21-27°C optimal',
            'soil': 'Deep, well-drained black cotton soil'
        }
    },
    'jute': {
        'name': 'Jute',
        'icon': '🌿',
        'duration_days': 120,
        'stages': [
            {'name': 'Land Preparation', 'days': 7, 'description': 'Plowing and leveling the field'},
            {'name': 'Seed Sowing', 'days': 2, 'description': 'Broadcasting or line sowing'},
            {'name': 'Germination', 'days': 8, 'description': 'Seeds germinate in 4-8 days'},
            {'name': 'Vegetative Growth', 'days': 60, 'description': 'Rapid stem growth period'},
            {'name': 'Flowering', 'days': 25, 'description': 'Yellow flowers appear'},
            {'name': 'Fiber Development', 'days': 15, 'description': 'Maximum fiber content'},
            {'name': 'Harvesting', 'days': 3, 'description': 'Cut at base when flowering'}
        ],
        'tasks': [
            {'week': 1, 'task': 'Land preparation and seed treatment'},
            {'week': 2, 'task': 'Broadcasting seeds uniformly'},
            {'week': 3, 'task': 'Thinning to maintain spacing'},
            {'week': 4, 'task': 'First weeding operation'},
            {'week': 6, 'task': 'Apply nitrogen fertilizer'},
            {'week': 8, 'task': 'Second weeding and earthing up'},
            {'week': 10, 'task': 'Monitor for stem rot disease'},
            {'week': 12, 'task': 'Watch for insect pests'},
            {'week': 15, 'task': 'Check fiber maturity'},
            {'week': 17, 'task': 'Harvest when flowers appear'}
        ],
        'requirements': {
            'water': 'High rainfall needed (1200-1500mm), supplementary irrigation',
            'fertilizer': 'NPK 60:30:30 kg/ha',
            'temperature': '24-37°C optimal, hot and humid climate',
            'soil': 'Deep loamy to clay loam, good water holding capacity'
        }
    },
    'banana': {
        'name': 'Banana',
        'icon': '🍌',
        'duration_days': 300,
        'stages': [
            {'name': 'Land Preparation', 'days': 15, 'description': 'Deep plowing and pit preparation'},
            {'name': 'Planting', 'days': 5, 'description': 'Plant suckers in prepared pits'},
            {'name': 'Establishment', 'days': 60, 'description': 'Root development and early growth'},
            {'name': 'Vegetative Growth', 'days': 120, 'description': 'Leaf production and pseudostem formation'},
            {'name': 'Flowering', 'days': 30, 'description': 'Inflorescence emergence'},
            {'name': 'Fruit Development', 'days': 60, 'description': 'Bunch development and filling'},
            {'name': 'Harvesting', 'days': 10, 'description': 'Harvest at 75% maturity'}
        ],
        'tasks': [
            {'week': 1, 'task': 'Prepare pits and apply organic manure'},
            {'week': 2, 'task': 'Plant healthy suckers'},
            {'week': 4, 'task': 'First irrigation and mulching'},
            {'week': 8, 'task': 'Apply first dose of fertilizer'},
            {'week': 12, 'task': 'Desuckering - remove extra suckers'},
            {'week': 16, 'task': 'Apply second fertilizer dose'},
            {'week': 20, 'task': 'Monitor for Panama disease'},
            {'week': 24, 'task': 'Third fertilizer application'},
            {'week': 28, 'task': 'Watch for bunch emergence'},
            {'week': 32, 'task': 'Support the pseudostem if needed'},
            {'week': 36, 'task': 'Cover bunch with protective bag'},
            {'week': 40, 'task': 'Monitor fruit maturity'},
            {'week': 42, 'task': 'Harvest when fingers are plump'}
        ],
        'requirements': {
            'water': 'Regular irrigation, 50-75mm per week, high water requirement',
            'fertilizer': 'NPK 200:60:200 kg/ha in 6-8 splits',
            'temperature': '26-30°C optimal, tropical climate',
            'soil': 'Deep, rich loam with good drainage, pH 6.5-7.5'
        }
    },
    'apple': {
        'name': 'Apple',
        'icon': '🍎',
        'duration_days': 365,
        'stages': [
            {'name': 'Dormancy', 'days': 90, 'description': 'Winter dormancy period, chilling requirement'},
            {'name': 'Bud Break', 'days': 30, 'description': 'Buds swell and break dormancy'},
            {'name': 'Flowering', 'days': 20, 'description': 'Blossoms open, pollination occurs'},
            {'name': 'Fruit Set', 'days': 30, 'description': 'Small fruits form after pollination'},
            {'name': 'Fruit Development', 'days': 90, 'description': 'Rapid fruit growth and cell division'},
            {'name': 'Fruit Maturation', 'days': 90, 'description': 'Color development and ripening'},
            {'name': 'Harvesting', 'days': 15, 'description': 'Pick when fully mature'}
        ],
        'tasks': [
            {'week': 4, 'task': 'Pruning during dormancy'},
            {'week': 8, 'task': 'Apply dormant oil spray'},
            {'week': 12, 'task': 'Pre-bloom fertilizer application'},
            {'week': 16, 'task': 'Hand pollination if needed'},
            {'week': 20, 'task': 'Fruit thinning to 1 per cluster'},
            {'week': 24, 'task': 'Monitor for pests and diseases'},
            {'week': 28, 'task': 'Summer pruning of water shoots'},
            {'week': 32, 'task': 'Second fertilizer dose'},
            {'week': 36, 'task': 'Monitor fruit size and color'},
            {'week': 40, 'task': 'Test fruit maturity'},
            {'week': 44, 'task': 'Begin harvesting ripe fruits'},
            {'week': 48, 'task': 'Post-harvest pruning'}
        ],
        'requirements': {
            'water': '25-40mm per week, drip irrigation preferred',
            'fertilizer': 'NPK 100:50:100 kg/ha in 2-3 splits',
            'temperature': '15-25°C optimal, requires 1000-1500 chilling hours',
            'soil': 'Well-drained loamy soil, pH 6.0-7.0'
        }
    },
    'blackgram': {
        'name': 'Black Gram',
        'icon': '🫘',
        'duration_days': 75,
        'stages': [
            {'name': 'Land Preparation', 'days': 5, 'description': 'Prepare fine seedbed'},
            {'name': 'Sowing', 'days': 2, 'description': 'Broadcast or line sowing'},
            {'name': 'Germination', 'days': 5, 'description': 'Seedlings emerge'},
            {'name': 'Vegetative Growth', 'days': 25, 'description': 'Leaf and branch development'},
            {'name': 'Flowering', 'days': 15, 'description': 'Yellow flowers appear'},
            {'name': 'Pod Formation', 'days': 20, 'description': 'Pods develop and fill'},
            {'name': 'Harvesting', 'days': 3, 'description': 'Harvest when 80% pods turn black'}
        ],
        'tasks': [
            {'week': 1, 'task': 'Prepare land and apply basal fertilizer'},
            {'week': 2, 'task': 'Sow seeds at 30-40 kg/ha'},
            {'week': 3, 'task': 'First irrigation if needed'},
            {'week': 4, 'task': 'Weeding and thinning'},
            {'week': 6, 'task': 'Monitor for yellow mosaic virus'},
            {'week': 8, 'task': 'Spray for pod borer if needed'},
            {'week': 10, 'task': 'Check pod maturity'},
            {'week': 11, 'task': 'Harvest and dry pods'}
        ],
        'requirements': {
            'water': 'Moderate water, 2-3 irrigations at critical stages',
            'fertilizer': 'NPK 20:40:20 kg/ha at sowing',
            'temperature': '25-35°C optimal, warm season crop',
            'soil': 'Well-drained loam to clay loam, pH 6.5-7.5'
        }
    },
    'chickpea': {
        'name': 'Chickpea',
        'icon': '🫘',
        'duration_days': 110,
        'stages': [
            {'name': 'Land Preparation', 'days': 7, 'description': 'Prepare seedbed with good tilth'},
            {'name': 'Sowing', 'days': 2, 'description': 'Line sowing at proper spacing'},
            {'name': 'Germination', 'days': 7, 'description': 'Seedlings emerge in 5-7 days'},
            {'name': 'Vegetative Growth', 'days': 40, 'description': 'Branching and leaf development'},
            {'name': 'Flowering', 'days': 25, 'description': 'White or purple flowers appear'},
            {'name': 'Pod Development', 'days': 25, 'description': 'Pods form and fill'},
            {'name': 'Harvesting', 'days': 4, 'description': 'Harvest when pods turn brown'}
        ],
        'tasks': [
            {'week': 1, 'task': 'Deep plowing and leveling'},
            {'week': 2, 'task': 'Sow seeds with Rhizobium treatment'},
            {'week': 3, 'task': 'Pre-emergence herbicide application'},
            {'week': 5, 'task': 'First irrigation at branching'},
            {'week': 7, 'task': 'Monitor for wilt disease'},
            {'week': 9, 'task': 'Second irrigation at flowering'},
            {'week': 11, 'task': 'Spray for pod borer'},
            {'week': 13, 'task': 'Third irrigation at pod filling'},
            {'week': 15, 'task': 'Check pod maturity'},
            {'week': 16, 'task': 'Harvest and thresh'}
        ],
        'requirements': {
            'water': '3-4 irrigations at critical stages only',
            'fertilizer': 'NPK 20:40:20 kg/ha, benefits from phosphorus',
            'temperature': '20-30°C optimal, cool season legume',
            'soil': 'Well-drained loamy soil, pH 6.0-7.5'
        }
    },
    'coconut': {
        'name': 'Coconut',
        'icon': '🥥',
        'duration_days': 365,
        'stages': [
            {'name': 'Pit Preparation', 'days': 30, 'description': 'Dig pits and refill with compost'},
            {'name': 'Planting', 'days': 7, 'description': 'Plant 6-12 month old seedlings'},
            {'name': 'Establishment', 'days': 90, 'description': 'Root development and establishment'},
            {'name': 'Vegetative Phase', 'days': 150, 'description': 'Frond production and growth'},
            {'name': 'Flowering', 'days': 40, 'description': 'Inflorescence emergence'},
            {'name': 'Nut Development', 'days': 40, 'description': 'Coconuts develop and mature'},
            {'name': 'Harvesting', 'days': 8, 'description': 'Harvest mature nuts every 45-60 days'}
        ],
        'tasks': [
            {'week': 4, 'task': 'Prepare pits with organic matter'},
            {'week': 5, 'task': 'Plant healthy seedlings'},
            {'week': 8, 'task': 'Regular watering for establishment'},
            {'week': 12, 'task': 'Apply first dose of fertilizer'},
            {'week': 16, 'task': 'Mulching around base'},
            {'week': 20, 'task': 'Control weeds and pests'},
            {'week': 24, 'task': 'Second fertilizer application'},
            {'week': 32, 'task': 'Monitor for rhinoceros beetle'},
            {'week': 36, 'task': 'Third fertilizer dose'},
            {'week': 44, 'task': 'Check for button stage nuts'},
            {'week': 48, 'task': 'Prepare for first harvest'},
            {'week': 52, 'task': 'Harvest mature coconuts'}
        ],
        'requirements': {
            'water': '60-100mm per week, high water requirement',
            'fertilizer': 'NPK 500:320:1200 g per palm per year',
            'temperature': '27-32°C optimal, tropical climate',
            'soil': 'Deep sandy loam, pH 5.5-7.0, good drainage'
        }
    },
    'coffee': {
        'name': 'Coffee',
        'icon': '☕',
        'duration_days': 365,
        'stages': [
            {'name': 'Nursery Phase', 'days': 90, 'description': 'Seedling development'},
            {'name': 'Transplanting', 'days': 7, 'description': 'Move to main field'},
            {'name': 'Establishment', 'days': 120, 'description': 'Root and shoot development'},
            {'name': 'Vegetative Growth', 'days': 60, 'description': 'Primary and secondary branches'},
            {'name': 'Flowering', 'days': 30, 'description': 'White fragrant flowers'},
            {'name': 'Berry Development', 'days': 50, 'description': 'Green berries form'},
            {'name': 'Harvesting', 'days': 8, 'description': 'Pick red ripe cherries'}
        ],
        'tasks': [
            {'week': 4, 'task': 'Prepare pits with organic manure'},
            {'week': 6, 'task': 'Transplant 6-month seedlings'},
            {'week': 8, 'task': 'Provide shade during establishment'},
            {'week': 12, 'task': 'First fertilizer application'},
            {'week': 16, 'task': 'Pruning and training'},
            {'week': 20, 'task': 'Mulching and weed control'},
            {'week': 24, 'task': 'Second fertilizer dose'},
            {'week': 28, 'task': 'Monitor for leaf rust'},
            {'week': 32, 'task': 'Third fertilizer application'},
            {'week': 40, 'task': 'Watch for berry borer'},
            {'week': 48, 'task': 'Check berry ripening'},
            {'week': 52, 'task': 'Selective harvest of ripe berries'}
        ],
        'requirements': {
            'water': '50-75mm per week, consistent moisture',
            'fertilizer': 'NPK 100:40:80 kg/ha in 3-4 splits',
            'temperature': '15-24°C optimal, shade-grown preferred',
            'soil': 'Well-drained loamy soil, pH 6.0-6.5, rich in organic matter'
        }
    },
    'grapes': {
        'name': 'Grapes',
        'icon': '🍇',
        'duration_days': 365,
        'stages': [
            {'name': 'Dormancy', 'days': 90, 'description': 'Winter rest period'},
            {'name': 'Bud Break', 'days': 20, 'description': 'Buds swell and sprout'},
            {'name': 'Flowering', 'days': 15, 'description': 'Small flowers in clusters'},
            {'name': 'Fruit Set', 'days': 30, 'description': 'Berry formation begins'},
            {'name': 'Berry Growth', 'days': 90, 'description': 'Rapid berry enlargement'},
            {'name': 'Veraison', 'days': 60, 'description': 'Color change and ripening'},
            {'name': 'Harvesting', 'days': 60, 'description': 'Pick at optimal sugar content'}
        ],
        'tasks': [
            {'week': 4, 'task': 'Winter pruning of vines'},
            {'week': 8, 'task': 'Apply dormant spray'},
            {'week': 12, 'task': 'Training new shoots'},
            {'week': 16, 'task': 'First fertilizer application'},
            {'week': 20, 'task': 'Bunch thinning if needed'},
            {'week': 24, 'task': 'Monitor for powdery mildew'},
            {'week': 28, 'task': 'Second fertilizer dose'},
            {'week': 32, 'task': 'Canopy management'},
            {'week': 36, 'task': 'Watch for berry ripening'},
            {'week': 40, 'task': 'Test sugar levels'},
            {'week': 44, 'task': 'Begin harvesting'},
            {'week': 48, 'task': 'Post-harvest care'}
        ],
        'requirements': {
            'water': 'Drip irrigation, 25-40mm per week',
            'fertilizer': 'NPK 80:40:80 kg/ha in 3-4 splits',
            'temperature': '15-35°C, requires warm days and cool nights',
            'soil': 'Well-drained sandy loam, pH 6.0-7.0'
        }
    },
    'kidneybeans': {
        'name': 'Kidney Beans',
        'icon': '🫘',
        'duration_days': 90,
        'stages': [
            {'name': 'Land Preparation', 'days': 5, 'description': 'Prepare fine seedbed'},
            {'name': 'Sowing', 'days': 2, 'description': 'Direct seeding in rows'},
            {'name': 'Germination', 'days': 7, 'description': 'Seedlings emerge'},
            {'name': 'Vegetative Growth', 'days': 30, 'description': 'Vine or bush development'},
            {'name': 'Flowering', 'days': 20, 'description': 'Flowers appear'},
            {'name': 'Pod Formation', 'days': 23, 'description': 'Pods develop and fill'},
            {'name': 'Harvesting', 'days': 3, 'description': 'Harvest when pods dry'}
        ],
        'tasks': [
            {'week': 1, 'task': 'Land preparation and basal fertilizer'},
            {'week': 2, 'task': 'Sow seeds at proper spacing'},
            {'week': 3, 'task': 'First irrigation after sowing'},
            {'week': 5, 'task': 'Weeding and earthing up'},
            {'week': 7, 'task': 'Monitor for anthracnose'},
            {'week': 9, 'task': 'Support poles for climbing varieties'},
            {'week': 11, 'task': 'Check pod maturity'},
            {'week': 13, 'task': 'Harvest and dry beans'}
        ],
        'requirements': {
            'water': 'Moderate water, 3-4 irrigations critical',
            'fertilizer': 'NPK 20:40:40 kg/ha at sowing',
            'temperature': '20-25°C optimal, cool season crop',
            'soil': 'Well-drained loamy soil, pH 6.0-7.0'
        }
    },
    'lentil': {
        'name': 'Lentil',
        'icon': '🫘',
        'duration_days': 110,
        'stages': [
            {'name': 'Land Preparation', 'days': 7, 'description': 'Prepare fine tilth seedbed'},
            {'name': 'Sowing', 'days': 2, 'description': 'Line sowing at optimal spacing'},
            {'name': 'Germination', 'days': 7, 'description': 'Seedlings emerge'},
            {'name': 'Vegetative Growth', 'days': 40, 'description': 'Branching and growth'},
            {'name': 'Flowering', 'days': 25, 'description': 'Small white/purple flowers'},
            {'name': 'Pod Development', 'days': 26, 'description': 'Pods form with 1-2 seeds'},
            {'name': 'Harvesting', 'days': 3, 'description': 'Harvest when pods turn brown'}
        ],
        'tasks': [
            {'week': 1, 'task': 'Deep plowing and leveling'},
            {'week': 2, 'task': 'Sow seeds with Rhizobium'},
            {'week': 3, 'task': 'Pre-emergence weed control'},
            {'week': 5, 'task': 'First irrigation at branching'},
            {'week': 7, 'task': 'Monitor for rust disease'},
            {'week': 9, 'task': 'Second irrigation at flowering'},
            {'week': 11, 'task': 'Third irrigation at pod filling'},
            {'week': 13, 'task': 'Monitor pod maturity'},
            {'week': 15, 'task': 'Harvest and thresh'},
            {'week': 16, 'task': 'Clean and store seeds'}
        ],
        'requirements': {
            'water': '2-3 light irrigations at critical stages',
            'fertilizer': 'NPK 20:40:20 kg/ha, low nitrogen requirement',
            'temperature': '18-30°C optimal, cool season pulse',
            'soil': 'Well-drained loam, pH 6.0-8.0'
        }
    },
    'mango': {
        'name': 'Mango',
        'icon': '🥭',
        'duration_days': 365,
        'stages': [
            {'name': 'Dormancy', 'days': 60, 'description': 'Winter vegetative rest'},
            {'name': 'Flowering', 'days': 30, 'description': 'Panicles emerge with flowers'},
            {'name': 'Fruit Set', 'days': 30, 'description': 'Fruitlets develop after pollination'},
            {'name': 'Fruit Development', 'days': 90, 'description': 'Rapid fruit growth'},
            {'name': 'Fruit Maturation', 'days': 60, 'description': 'Fruits mature and ripen'},
            {'name': 'Harvesting', 'days': 30, 'description': 'Pick mature fruits'},
            {'name': 'Post-Harvest Care', 'days': 65, 'description': 'Pruning and fertilization'}
        ],
        'tasks': [
            {'week': 4, 'task': 'Pruning after harvest'},
            {'week': 8, 'task': 'Apply manure and fertilizer'},
            {'week': 12, 'task': 'Spray for hopper control'},
            {'week': 16, 'task': 'Monitor flowering'},
            {'week': 20, 'task': 'Second fertilizer dose'},
            {'week': 24, 'task': 'Fruit thinning if needed'},
            {'week': 28, 'task': 'Monitor for fruit fly'},
            {'week': 32, 'task': 'Third fertilizer application'},
            {'week': 36, 'task': 'Check fruit maturity'},
            {'week': 40, 'task': 'Begin harvesting'},
            {'week': 44, 'task': 'Continue selective harvest'},
            {'week': 48, 'task': 'Post-harvest sanitation'}
        ],
        'requirements': {
            'water': '40-60mm per week during fruit development',
            'fertilizer': 'NPK 1000:500:1000 g per tree per year',
            'temperature': '24-30°C optimal, tropical/subtropical',
            'soil': 'Well-drained deep loam, pH 5.5-7.5'
        }
    },
    'mothbeans': {
        'name': 'Moth Beans',
        'icon': '🫘',
        'duration_days': 70,
        'stages': [
            {'name': 'Land Preparation', 'days': 5, 'description': 'Prepare seedbed'},
            {'name': 'Sowing', 'days': 2, 'description': 'Broadcast or line sowing'},
            {'name': 'Germination', 'days': 5, 'description': 'Seedlings emerge'},
            {'name': 'Vegetative Growth', 'days': 23, 'description': 'Spreading growth habit'},
            {'name': 'Flowering', 'days': 15, 'description': 'Yellow flowers appear'},
            {'name': 'Pod Formation', 'days': 17, 'description': 'Cylindrical pods develop'},
            {'name': 'Harvesting', 'days': 3, 'description': 'Harvest when pods turn brown'}
        ],
        'tasks': [
            {'week': 1, 'task': 'Land preparation and sowing'},
            {'week': 2, 'task': 'Light irrigation after sowing'},
            {'week': 4, 'task': 'Weeding if needed'},
            {'week': 6, 'task': 'Monitor for pests'},
            {'week': 8, 'task': 'Light irrigation at flowering'},
            {'week': 9, 'task': 'Check pod development'},
            {'week': 10, 'task': 'Harvest mature pods'}
        ],
        'requirements': {
            'water': 'Drought tolerant, 1-2 light irrigations',
            'fertilizer': 'Minimal, NPK 15:30:15 kg/ha',
            'temperature': '25-35°C optimal, very heat tolerant',
            'soil': 'Sandy loam, tolerates poor soils, pH 6.5-8.0'
        }
    },
    'mungbean': {
        'name': 'Mung Bean',
        'icon': '🫘',
        'duration_days': 70,
        'stages': [
            {'name': 'Land Preparation', 'days': 5, 'description': 'Prepare fine seedbed'},
            {'name': 'Sowing', 'days': 2, 'description': 'Line sowing at proper spacing'},
            {'name': 'Germination', 'days': 5, 'description': 'Quick emergence'},
            {'name': 'Vegetative Growth', 'days': 23, 'description': 'Bushy growth'},
            {'name': 'Flowering', 'days': 15, 'description': 'Yellow flowers'},
            {'name': 'Pod Formation', 'days': 17, 'description': 'Long cylindrical pods'},
            {'name': 'Harvesting', 'days': 3, 'description': 'Multiple pickings as pods mature'}
        ],
        'tasks': [
            {'week': 1, 'task': 'Land preparation and sowing'},
            {'week': 2, 'task': 'First irrigation if needed'},
            {'week': 3, 'task': 'Weeding and thinning'},
            {'week': 5, 'task': 'Monitor for yellow mosaic virus'},
            {'week': 7, 'task': 'Spray for pod borer if needed'},
            {'week': 9, 'task': 'First harvest of mature pods'},
            {'week': 10, 'task': 'Second picking of pods'}
        ],
        'requirements': {
            'water': 'Light water requirement, 2-3 irrigations',
            'fertilizer': 'NPK 20:40:20 kg/ha, benefits from phosphorus',
            'temperature': '25-35°C optimal, warm season crop',
            'soil': 'Well-drained loamy soil, pH 6.5-7.5'
        }
    },
    'muskmelon': {
        'name': 'Muskmelon',
        'icon': '🍈',
        'duration_days': 90,
        'stages': [
            {'name': 'Land Preparation', 'days': 7, 'description': 'Prepare beds or mounds'},
            {'name': 'Sowing', 'days': 3, 'description': 'Direct seeding or transplanting'},
            {'name': 'Germination', 'days': 7, 'description': 'Seedlings emerge'},
            {'name': 'Vine Growth', 'days': 30, 'description': 'Rapid vine extension'},
            {'name': 'Flowering', 'days': 10, 'description': 'Male and female flowers'},
            {'name': 'Fruit Development', 'days': 30, 'description': 'Melons grow and mature'},
            {'name': 'Harvesting', 'days': 3, 'description': 'Pick when fruits slip from vine'}
        ],
        'tasks': [
            {'week': 1, 'task': 'Prepare raised beds and sow seeds'},
            {'week': 2, 'task': 'Regular light irrigation'},
            {'week': 3, 'task': 'Thinning to 2 plants per hill'},
            {'week': 5, 'task': 'First fertilizer application'},
            {'week': 7, 'task': 'Training vines and mulching'},
            {'week': 9, 'task': 'Hand pollination if needed'},
            {'week': 11, 'task': 'Monitor for fruit fly and aphids'},
            {'week': 12, 'task': 'Check fruit maturity (slip test)'},
            {'week': 13, 'task': 'Harvest ripe melons'}
        ],
        'requirements': {
            'water': 'Regular irrigation, 30-50mm per week',
            'fertilizer': 'NPK 100:50:100 kg/ha in 2-3 splits',
            'temperature': '25-35°C optimal, warm season crop',
            'soil': 'Sandy loam with good drainage, pH 6.0-7.0'
        }
    },
    'orange': {
        'name': 'Orange',
        'icon': '🍊',
        'duration_days': 365,
        'stages': [
            {'name': 'Planting', 'days': 30, 'description': 'Establish grafted saplings'},
            {'name': 'Establishment', 'days': 120, 'description': 'Root and shoot development'},
            {'name': 'Vegetative Growth', 'days': 60, 'description': 'New flush growth'},
            {'name': 'Flowering', 'days': 30, 'description': 'Fragrant white flowers'},
            {'name': 'Fruit Set', 'days': 30, 'description': 'Small fruits develop'},
            {'name': 'Fruit Development', 'days': 80, 'description': 'Fruits grow and mature'},
            {'name': 'Harvesting', 'days': 15, 'description': 'Pick when fully colored'}
        ],
        'tasks': [
            {'week': 4, 'task': 'Prepare pits and plant saplings'},
            {'week': 8, 'task': 'Regular watering for establishment'},
            {'week': 12, 'task': 'First fertilizer application'},
            {'week': 16, 'task': 'Pruning of dead wood'},
            {'week': 20, 'task': 'Second fertilizer dose'},
            {'week': 24, 'task': 'Monitor for citrus psyllid'},
            {'week': 28, 'task': 'Third fertilizer application'},
            {'week': 32, 'task': 'Control fruit drop'},
            {'week': 36, 'task': 'Monitor for citrus canker'},
            {'week': 44, 'task': 'Check fruit color development'},
            {'week': 48, 'task': 'Begin harvesting ripe fruits'},
            {'week': 52, 'task': 'Post-harvest pruning'}
        ],
        'requirements': {
            'water': '40-60mm per week, consistent moisture',
            'fertilizer': 'NPK 500:250:500 g per tree per year',
            'temperature': '20-30°C optimal, subtropical climate',
            'soil': 'Well-drained sandy loam, pH 6.0-7.5'
        }
    },
    'papaya': {
        'name': 'Papaya',
        'icon': '🍈',
        'duration_days': 300,
        'stages': [
            {'name': 'Nursery', 'days': 30, 'description': 'Seedling development'},
            {'name': 'Transplanting', 'days': 7, 'description': 'Move to main field'},
            {'name': 'Establishment', 'days': 60, 'description': 'Root development'},
            {'name': 'Vegetative Growth', 'days': 90, 'description': 'Trunk and canopy formation'},
            {'name': 'Flowering', 'days': 30, 'description': 'First flowers appear'},
            {'name': 'Fruit Development', 'days': 70, 'description': 'Fruits develop and grow'},
            {'name': 'Harvesting', 'days': 13, 'description': 'Continuous harvest for months'}
        ],
        'tasks': [
            {'week': 4, 'task': 'Prepare pits with organic matter'},
            {'week': 5, 'task': 'Transplant 45-day seedlings'},
            {'week': 8, 'task': 'Regular watering and mulching'},
            {'week': 12, 'task': 'First fertilizer application'},
            {'week': 16, 'task': 'Remove male plants'},
            {'week': 20, 'task': 'Second fertilizer dose'},
            {'week': 24, 'task': 'Monitor for papaya ringspot virus'},
            {'week': 28, 'task': 'Third fertilizer application'},
            {'week': 32, 'task': 'Support stem if needed'},
            {'week': 36, 'task': 'Watch for first fruits'},
            {'week': 40, 'task': 'Begin harvesting ripe fruits'},
            {'week': 42, 'task': 'Continue regular harvest'}
        ],
        'requirements': {
            'water': '50-75mm per week, good drainage essential',
            'fertilizer': 'NPK 200:200:400 kg/ha in monthly splits',
            'temperature': '25-35°C optimal, tropical climate',
            'soil': 'Well-drained sandy loam, pH 6.0-7.0'
        }
    },
    'pigeonpeas': {
        'name': 'Pigeon Peas',
        'icon': '🫘',
        'duration_days': 180,
        'stages': [
            {'name': 'Land Preparation', 'days': 7, 'description': 'Prepare seedbed'},
            {'name': 'Sowing', 'days': 2, 'description': 'Line sowing at wide spacing'},
            {'name': 'Germination', 'days': 7, 'description': 'Seedlings emerge'},
            {'name': 'Vegetative Growth', 'days': 90, 'description': 'Bushy growth with deep roots'},
            {'name': 'Flowering', 'days': 30, 'description': 'Yellow flowers appear'},
            {'name': 'Pod Formation', 'days': 40, 'description': 'Pods develop with 2-5 seeds'},
            {'name': 'Harvesting', 'days': 4, 'description': 'Multiple pickings as pods mature'}
        ],
        'tasks': [
            {'week': 1, 'task': 'Land preparation and basal fertilizer'},
            {'week': 2, 'task': 'Sow seeds with Rhizobium'},
            {'week': 4, 'task': 'First weeding'},
            {'week': 8, 'task': 'Earthing up around plants'},
            {'week': 12, 'task': 'Monitor for pod borer'},
            {'week': 16, 'task': 'Second weeding'},
            {'week': 20, 'task': 'Watch for pod fly'},
            {'week': 24, 'task': 'Check pod maturity'},
            {'week': 25, 'task': 'First harvest of mature pods'},
            {'week': 26, 'task': 'Second picking of pods'}
        ],
        'requirements': {
            'water': 'Drought tolerant, 2-3 irrigations at critical stages',
            'fertilizer': 'NPK 20:40:20 kg/ha, low fertilizer requirement',
            'temperature': '20-35°C optimal, adapts to various climates',
            'soil': 'Well-drained loam to clay loam, pH 6.0-7.5'
        }
    },
    'pomegranate': {
        'name': 'Pomegranate',
        'icon': '🍎',
        'duration_days': 365,
        'stages': [
            {'name': 'Planting', 'days': 30, 'description': 'Establish cuttings or saplings'},
            {'name': 'Establishment', 'days': 90, 'description': 'Root and shoot development'},
            {'name': 'Vegetative Growth', 'days': 60, 'description': 'New shoots and leaves'},
            {'name': 'Flowering', 'days': 30, 'description': 'Red-orange flowers'},
            {'name': 'Fruit Set', 'days': 30, 'description': 'Small fruits form'},
            {'name': 'Fruit Development', 'days': 110, 'description': 'Fruits grow and mature'},
            {'name': 'Harvesting', 'days': 15, 'description': 'Pick when fully mature'}
        ],
        'tasks': [
            {'week': 4, 'task': 'Prepare pits and plant saplings'},
            {'week': 8, 'task': 'Regular watering for establishment'},
            {'week': 12, 'task': 'First fertilizer application'},
            {'week': 16, 'task': 'Pruning of suckers'},
            {'week': 20, 'task': 'Second fertilizer dose'},
            {'week': 24, 'task': 'Monitor for fruit borer'},
            {'week': 28, 'task': 'Third fertilizer application'},
            {'week': 32, 'task': 'Control bacterial blight'},
            {'week': 36, 'task': 'Monitor for fruit cracking'},
            {'week': 44, 'task': 'Check fruit maturity (sound test)'},
            {'week': 48, 'task': 'Harvest ripe fruits'},
            {'week': 52, 'task': 'Post-harvest pruning'}
        ],
        'requirements': {
            'water': 'Moderate water, 30-50mm per week',
            'fertilizer': 'NPK 500:250:500 g per plant per year',
            'temperature': '20-35°C optimal, semi-arid climate preferred',
            'soil': 'Well-drained sandy loam, pH 6.5-7.5'
        }
    },
    'watermelon': {
        'name': 'Watermelon',
        'icon': '🍉',
        'duration_days': 85,
        'stages': [
            {'name': 'Land Preparation', 'days': 7, 'description': 'Prepare beds or mounds'},
            {'name': 'Sowing', 'days': 3, 'description': 'Direct seeding in pits'},
            {'name': 'Germination', 'days': 7, 'description': 'Seedlings emerge'},
            {'name': 'Vine Growth', 'days': 25, 'description': 'Rapid vine extension'},
            {'name': 'Flowering', 'days': 10, 'description': 'Male and female flowers'},
            {'name': 'Fruit Development', 'days': 30, 'description': 'Melons grow rapidly'},
            {'name': 'Harvesting', 'days': 3, 'description': 'Pick when tendrils dry near fruit'}
        ],
        'tasks': [
            {'week': 1, 'task': 'Prepare raised beds and sow seeds'},
            {'week': 2, 'task': 'Regular irrigation'},
            {'week': 3, 'task': 'Thinning to 2-3 plants per pit'},
            {'week': 5, 'task': 'First fertilizer application'},
            {'week': 7, 'task': 'Training vines and mulching'},
            {'week': 8, 'task': 'Hand pollination if needed'},
            {'week': 10, 'task': 'Monitor for fruit fly and aphids'},
            {'week': 11, 'task': 'Check fruit maturity (thump test)'},
            {'week': 12, 'task': 'Harvest ripe melons'}
        ],
        'requirements': {
            'water': 'Regular irrigation, 40-60mm per week',
            'fertilizer': 'NPK 100:50:100 kg/ha in 2-3 splits',
            'temperature': '25-35°C optimal, warm season crop',
            'soil': 'Sandy loam with excellent drainage, pH 6.0-7.0'
        }
    }
}

@growing_bp.route('/growing/start/<crop_name>')
@login_required
def start_growing(crop_name):
    """Show crop cultivation manual and setup growing activity"""
    crop_name = crop_name.lower()
    
    if crop_name not in CROP_MANUALS:
        flash(f'Cultivation manual not available for {crop_name}', 'error')
        return redirect(url_for('crop.crop_suggestion'))
    
    manual = CROP_MANUALS[crop_name]
    
    # Calculate suggested dates
    start_date = datetime.now()
    harvest_date = start_date + timedelta(days=manual['duration_days'])
    
    return render_template('start_growing.html',
                         crop=manual,
                         crop_name=crop_name,
                         start_date=start_date,
                         harvest_date=harvest_date,
                         user_name=session.get('user_name', 'Farmer'),
                         current_date=datetime.now().strftime('%B %d, %Y'))

@growing_bp.route('/growing/save', methods=['POST'])
@login_required
def save_growing():
    """Save growing activity to database"""
    try:
        crop_name = request.form.get('crop_name')
        start_date = request.form.get('start_date')
        harvest_date = request.form.get('harvest_date')
        notes = request.form.get('notes', '')
        
        if not all([crop_name, start_date, harvest_date]):
            flash('Please fill all required fields', 'error')
            return redirect(url_for('growing.start_growing', crop_name=crop_name))
        
        # Get crop manual
        manual = CROP_MANUALS.get(crop_name.lower())
        if not manual:
            flash('Invalid crop selected', 'error')
            return redirect(url_for('dashboard.dashboard'))
        
        # Collect task dates from form
        task_dates = {}
        completed_tasks = []
        current_date = datetime.now().date()
        
        for i in range(len(manual['tasks'])):
            task_date = request.form.get(f'task_date_{i}')
            if task_date:
                task_dates[i] = task_date
                # Auto-mark as complete if date has passed
                if datetime.strptime(task_date, '%Y-%m-%d').date() <= current_date:
                    completed_tasks.append(i)
        
        # Create growing activity
        activity = {
            'user_id': session.get('user_id'),
            'crop_name': crop_name.lower(),
            'crop_display_name': manual['name'],
            'start_date': start_date,
            'harvest_date': harvest_date,
            'duration_days': manual['duration_days'],
            'current_stage': len(completed_tasks),
            'status': 'active',
            'tasks': manual['tasks'],
            'task_dates': task_dates,
            'completed_tasks': completed_tasks,
            'notes': notes,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Save to database
        result = save_growing_activity(activity)
        
        if result:
            flash(f'🌱 Started growing {manual["name"]}! Check dashboard for tasks.', 'success')
            return redirect(url_for('dashboard.dashboard'))
        else:
            flash('Failed to save growing activity', 'error')
            return redirect(url_for('growing.start_growing', crop_name=crop_name))
            
    except Exception as e:
        print(f"Error saving growing activity: {e}")
        flash('An error occurred while saving', 'error')
        return redirect(url_for('dashboard.dashboard'))

@growing_bp.route('/growing/activities')
@login_required
def my_activities():
    """Show user's active growing activities"""
    activities = get_user_growing_activities(session.get('user_id'))
    
    return render_template('growing_activities.html',
                         activities=activities,
                         user_name=session.get('user_name', 'Farmer'),
                         current_date=datetime.now().strftime('%B %d, %Y'))

@growing_bp.route('/growing/task/complete', methods=['POST'])
@login_required
def complete_task():
    """Mark a task as completed"""
    try:
        activity_id = request.form.get('activity_id')
        task_index = int(request.form.get('task_index'))
        
        result = update_growing_activity(activity_id, task_index)
        
        if result:
            return jsonify({'success': True, 'message': 'Task completed!'})
        else:
            return jsonify({'success': False, 'message': 'Failed to update task'})
            
    except Exception as e:
        print(f"Error completing task: {e}")
        return jsonify({'success': False, 'message': str(e)})

@growing_bp.route('/growing/delete/<activity_id>', methods=['POST'])
@login_required
def delete_activity(activity_id):
    """Delete a growing activity"""
    try:
        from utils.db import delete_growing_activity
        
        result = delete_growing_activity(activity_id, session.get('user_id'))
        
        if result:
            return jsonify({'success': True, 'message': 'Activity deleted successfully!'})
        else:
            return jsonify({'success': False, 'message': 'Failed to delete activity'})
            
    except Exception as e:
        print(f"Error deleting activity: {e}")
        return jsonify({'success': False, 'message': str(e)})


@growing_bp.route('/growing/update/<activity_id>', methods=['POST'])
@login_required
def update_activity(activity_id):
    """Update a growing activity (stage, notes, tasks)"""
    try:
        data = request.get_json()
        print(f"📝 Update request for activity {activity_id}")
        print(f"📝 Received data: {data}")
        
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'})
        
        # Get current activity to update
        user_id = session.get('user_id')
        print(f"📝 User ID: {user_id}")
        activities = get_user_growing_activities(user_id)
        print(f"📝 Total activities: {len(activities)}")
        
        activity = None
        for act in activities:
            print(f"📝 Checking activity: {act.get('_id')} vs {activity_id}")
            if act.get('_id') == activity_id:
                activity = act
                break
        
        if not activity:
            print(f"❌ Activity {activity_id} not found!")
            return jsonify({'success': False, 'message': 'Activity not found'})
        
        print(f"✅ Found activity: {activity.get('crop_display_name')}")
        
        # Update fields
        update_data = {}
        
        if 'stage' in data:
            update_data['current_stage'] = data['stage']
            # Update progress based on stage
            stages = ['Seed Sowing', 'Germination', 'Seedling', 'Vegetative Growth', 
                      'Flowering', 'Fruit Development', 'Maturity', 'Harvest Ready']
            if data['stage'] in stages:
                stage_index = stages.index(data['stage'])
                update_data['progress'] = int((stage_index + 1) / len(stages) * 100)
        
        if 'notes' in data:
            update_data['notes'] = data['notes']
        
        if 'tasks' in data:
            update_data['completed_tasks'] = data['tasks']
        
        print(f"📝 Update data: {update_data}")
        
        # Save updates
        result = update_growing_activity(activity_id, user_id, update_data)
        
        print(f"📝 Update result: {result}")
        
        if result:
            return jsonify({'success': True, 'message': 'Activity updated successfully!'})
        else:
            return jsonify({'success': False, 'message': 'Failed to update activity'})
            
    except Exception as e:
        print(f"Error updating activity: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)})


@growing_bp.route('/growing/view/<activity_id>')
@login_required
def view_activity(activity_id):
    """View full growing activity details"""
    try:
        user_name = session.get('user_name', 'Guest')
        activities = get_user_growing_activities(session.get('user_id'))
        
        activity = None
        for act in activities:
            if act.get('_id') == activity_id:
                activity = act
                break
        
        if not activity:
            flash('Activity not found', 'error')
            return redirect(url_for('dashboard.dashboard'))
        
        # Get crop manual if available
        crop_key = activity.get('crop', '').lower().replace(' ', '')
        manual = CROP_MANUALS.get(crop_key, {})
        
        return render_template('growing_view.html',
                             user_name=user_name,
                             activity=activity,
                             manual=manual)
    
    except Exception as e:
        print(f"Error viewing activity: {e}")
        flash('Error loading activity details', 'error')
        return redirect(url_for('dashboard.dashboard'))


@growing_bp.route('/api/expenses', methods=['POST'])
@login_required
def save_expense_api():
    """API endpoint to save expense data"""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        # Add user_id and timestamp
        data['user_id'] = session.get('user_id')
        data['created_at'] = datetime.now().isoformat()
        
        # Flatten expenses if they are in a sub-dictionary for the backend logic (report_routes.py expects certain keys)
        # Based on report_routes.py, it expects: seed_cost, fertilizer_cost, pesticide_cost, irrigation_cost, labor_cost, machinery_cost, other_cost
        if 'expenses' in data:
            exp = data['expenses']
            data['seed_cost'] = exp.get('seed', 0)
            data['fertilizer_cost'] = exp.get('fertilizer', 0)
            data['pesticide_cost'] = exp.get('pesticide', 0)
            data['irrigation_cost'] = exp.get('irrigation', 0)
            data['labor_cost'] = exp.get('labor', 0)
            data['machinery_cost'] = exp.get('machinery', 0)
            data['other_cost'] = exp.get('other', 0)
            # Remove the nested object to avoid redundancy
            # del data['expenses']
            
        if 'date' in data:
            data['entry_date'] = data['date'] # backend expects entry_date
        
        # cropType -> crop_type
        if 'cropType' in data:
            data['crop_type'] = data['cropType']
            
        # Mapping frontend camelCase to backend snake_case for revenue calculation
        if 'landArea' in data:
            data['land_area'] = data['landArea']
        if 'expectedYield' in data:
            data['expected_yield'] = data['expectedYield']
        if 'marketPrice' in data:
            data['market_price'] = data['marketPrice']
            
        expense_id = save_expense(data)
        
        if expense_id:
            return jsonify({
                'success': True,
                'message': 'Expense entry saved successfully!',
                'expense_id': str(expense_id)
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to save expense'}), 500
            
    except Exception as e:
        print(f"Error in save_expense_api: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
