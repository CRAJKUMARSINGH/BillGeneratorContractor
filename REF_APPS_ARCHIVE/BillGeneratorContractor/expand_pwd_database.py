#!/usr/bin/env python3
"""
Expand PWD BSR Database - Week 1 Day 2-5
Systematically add more BSR codes to reach 500+ items
"""
import json
from pathlib import Path

# Load existing database
db_path = Path("data/pwd_bsr_database.json")
with open(db_path, 'r', encoding='utf-8') as f:
    db = json.load(f)

# Helper function to add items
def add_item(category, code, description, unit, rate_2024, rate_range, subcategory):
    if category not in db['categories']:
        db['categories'][category] = {}
    
    db['categories'][category][code] = {
        "description": description,
        "unit": unit,
        "rate_2024": rate_2024,
        "rate_range": rate_range,
        "category": category,
        "subcategory": subcategory
    }

# ============================================================================
# ELECTRICAL WIRING - Expand to cover all point types
# ============================================================================

# 1.1.x - Light/Fan/Exhaust Fan Points
add_item("electrical_wiring", "1.1.4", 
    "Wiring of light point/ fan point/ exhaust fan point/ call bell point - Extra long point (up to 15 mtr.)",
    "P. point", 1125, [1000, 1250], "light_points")

add_item("electrical_wiring", "1.1.5",
    "Wiring of light point/ fan point/ exhaust fan point/ call bell point - Very long point (up to 20 mtr.)",
    "P. point", 1425, [1300, 1550], "light_points")

# 1.2.x - Power Plug Points (15 amp)
add_item("electrical_wiring", "1.2.1",
    "Wiring of 3/5 pin 15 amp. Power plug point - Short point (up to 3 mtr.)",
    "P. point", 425, [380, 480], "plug_points")

add_item("electrical_wiring", "1.2.2",
    "Wiring of 3/5 pin 15 amp. Power plug point - Medium point (up to 6 mtr.)",
    "P. point", 850, [780, 920], "plug_points")

add_item("electrical_wiring", "1.2.3",
    "Wiring of 3/5 pin 15 amp. Power plug point - Long point (up to 10 mtr.)",
    "P. point", 1150, [1050, 1250], "plug_points")

# 1.3.x - Light Plug Points (6 amp) - expand
add_item("electrical_wiring", "1.3.2",
    "Wiring of 3/5 pin 6 amp. Light plug point - Medium point (up to 6 mtr.)",
    "P. point", 640, [580, 700], "plug_points")

# 1.4.x - PVC Conduit - expand all sizes
add_item("electrical_wiring", "1.4.1",
    "S&F following sizes (dia.) of ISI marked MMS PVC conduit - 20 mm",
    "Mtr.", 45, [38, 52], "conduit")

add_item("electrical_wiring", "1.4.3",
    "S&F following sizes (dia.) of ISI marked MMS PVC conduit - 32 mm",
    "Mtr.", 75, [65, 85], "conduit")

add_item("electrical_wiring", "1.4.4",
    "S&F following sizes (dia.) of ISI marked MMS PVC conduit - 40 mm",
    "Mtr.", 95, [85, 105], "conduit")

add_item("electrical_wiring", "1.4.5",
    "S&F following sizes (dia.) of ISI marked MMS PVC conduit - 50 mm",
    "Mtr.", 125, [110, 140], "conduit")

# ============================================================================
# CABLES & WIRES - Expand all conductor sizes
# ============================================================================

# 4.1.x - FR PVC Insulated Copper Conductors
add_item("cables_wires", "4.1.2",
    "Supplying and laying FR PVC insulated & unsheathed flexible copper conductor - 1 x 2.5 sq.mm",
    "Mtr.", 38, [32, 45], "copper_conductor")

add_item("cables_wires", "4.1.3",
    "Supplying and laying FR PVC insulated & unsheathed flexible copper conductor - 2 x 1.5 sq.mm",
    "Mtr.", 48, [42, 55], "copper_conductor")

add_item("cables_wires", "4.1.4",
    "Supplying and laying FR PVC insulated & unsheathed flexible copper conductor - 2 x 1.5 sq.mm + 1 x 1.5 sq.mm",
    "Mtr.", 68, [60, 78], "copper_conductor")

add_item("cables_wires", "4.1.5",
    "Supplying and laying FR PVC insulated & unsheathed flexible copper conductor - 2 x 2.5 sq.mm",
    "Mtr.", 78, [68, 88], "copper_conductor")

add_item("cables_wires", "4.1.6",
    "Supplying and laying FR PVC insulated & unsheathed flexible copper conductor - 3 x 1.5 sq.mm",
    "Mtr.", 68, [60, 78], "copper_conductor")

add_item("cables_wires", "4.1.8",
    "Supplying and laying FR PVC insulated & unsheathed flexible copper conductor - 3 x 2.5 sq.mm",
    "Mtr.", 115, [100, 130], "copper_conductor")

add_item("cables_wires", "4.1.9",
    "Supplying and laying FR PVC insulated & unsheathed flexible copper conductor - 3 x 2.5 sq.mm + 1 x 1.5 sq.mm",
    "Mtr.", 135, [120, 150], "copper_conductor")

add_item("cables_wires", "4.1.11",
    "Supplying and laying FR PVC insulated & unsheathed flexible copper conductor - 2 x 4.0 sq.mm",
    "Mtr.", 128, [115, 145], "copper_conductor")

add_item("cables_wires", "4.1.12",
    "Supplying and laying FR PVC insulated & unsheathed flexible copper conductor - 3 x 4.0 sq.mm",
    "Mtr.", 192, [175, 210], "copper_conductor")

add_item("cables_wires", "4.1.13",
    "Supplying and laying FR PVC insulated & unsheathed flexible copper conductor - 3 x 4.0 sq.mm + 1 x 2.5 sq.mm",
    "Mtr.", 220, [200, 245], "copper_conductor")

add_item("cables_wires", "4.1.15",
    "Supplying and laying FR PVC insulated & unsheathed flexible copper conductor - 1 x 6.0 sq.mm",
    "Mtr.", 96, [85, 110], "copper_conductor")

add_item("cables_wires", "4.1.16",
    "Supplying and laying FR PVC insulated & unsheathed flexible copper conductor - 2 x 6.0 sq.mm",
    "Mtr.", 192, [175, 210], "copper_conductor")

add_item("cables_wires", "4.1.17",
    "Supplying and laying FR PVC insulated & unsheathed flexible copper conductor - 3 x 6.0 sq.mm",
    "Mtr.", 288, [260, 320], "copper_conductor")

add_item("cables_wires", "4.1.18",
    "Supplying and laying FR PVC insulated & unsheathed flexible copper conductor - 3 x 6.0 sq.mm + 1 x 4.0 sq.mm",
    "Mtr.", 352, [320, 390], "copper_conductor")

add_item("cables_wires", "4.1.19",
    "Supplying and laying FR PVC insulated & unsheathed flexible copper conductor - 1 x 10.0 sq.mm",
    "Mtr.", 160, [145, 180], "copper_conductor")

add_item("cables_wires", "4.1.20",
    "Supplying and laying FR PVC insulated & unsheathed flexible copper conductor - 2 x 10.0 sq.mm",
    "Mtr.", 320, [290, 355], "copper_conductor")

add_item("cables_wires", "4.1.21",
    "Supplying and laying FR PVC insulated & unsheathed flexible copper conductor - 3 x 10.0 sq.mm",
    "Mtr.", 480, [435, 530], "copper_conductor")

add_item("cables_wires", "4.1.22",
    "Supplying and laying FR PVC insulated & unsheathed flexible copper conductor - 3 x 10.0 sq.mm + 1 x 6.0 sq.mm",
    "Mtr.", 576, [520, 635], "copper_conductor")

# ============================================================================
# MCB & DISTRIBUTION BOARDS - Expand all ratings
# ============================================================================

# 6.1.1.x - Single Pole MCB
add_item("mcb_distribution", "6.1.1.1",
    "Providing & Fixing of 240/415 V AC MCB - Single pole MCB - 2 A to 6 A rating",
    "Each", 185, [165, 205], "mcb")

add_item("mcb_distribution", "6.1.1.3",
    "Providing & Fixing of 240/415 V AC MCB - Single pole MCB - 40 A rating",
    "Each", 285, [260, 315], "mcb")

add_item("mcb_distribution", "6.1.1.4",
    "Providing & Fixing of 240/415 V AC MCB - Single pole MCB - 50 A rating",
    "Each", 325, [295, 360], "mcb")

add_item("mcb_distribution", "6.1.1.5",
    "Providing & Fixing of 240/415 V AC MCB - Single pole MCB - 63 A rating",
    "Each", 385, [350, 425], "mcb")

# 6.1.2.x - Double Pole MCB
add_item("mcb_distribution", "6.1.2.1",
    "Providing & Fixing of 240/415 V AC MCB - Double pole MCB - 6 A to 32 A rating",
    "Each", 385, [350, 425], "mcb")

add_item("mcb_distribution", "6.1.2.2",
    "Providing & Fixing of 240/415 V AC MCB - Double pole MCB - 40 A rating",
    "Each", 525, [475, 580], "mcb")

add_item("mcb_distribution", "6.1.2.3",
    "Providing & Fixing of 240/415 V AC MCB - Double pole MCB - 50 A rating",
    "Each", 625, [565, 690], "mcb")

add_item("mcb_distribution", "6.1.2.4",
    "Providing & Fixing of 240/415 V AC MCB - Double pole MCB - 63 A rating",
    "Each", 725, [655, 800], "mcb")

# 6.1.3.x - Triple Pole MCB
add_item("mcb_distribution", "6.1.3.1",
    "Providing & Fixing of 240/415 V AC MCB - Triple pole MCB - 6 A to 32 A rating",
    "Each", 625, [565, 690], "mcb")

add_item("mcb_distribution", "6.1.3.2",
    "Providing & Fixing of 240/415 V AC MCB - Triple pole MCB - 40 A rating",
    "Each", 825, [745, 910], "mcb")

add_item("mcb_distribution", "6.1.3.3",
    "Providing & Fixing of 240/415 V AC MCB - Triple pole MCB - 50 A rating",
    "Each", 925, [835, 1020], "mcb")

add_item("mcb_distribution", "6.1.3.4",
    "Providing & Fixing of 240/415 V AC MCB - Triple pole MCB - 63 A rating",
    "Each", 1125, [1015, 1240], "mcb")

# 6.1.4.x - Four Pole MCB
add_item("mcb_distribution", "6.1.4.1",
    "Providing & Fixing of 240/415 V AC MCB - Four pole MCB - 6 A to 32 A rating",
    "Each", 825, [745, 910], "mcb")

add_item("mcb_distribution", "6.1.4.2",
    "Providing & Fixing of 240/415 V AC MCB - Four pole MCB - 32 A rating",
    "Each", 1125, [1015, 1240], "mcb")

add_item("mcb_distribution", "6.1.4.4",
    "Providing & Fixing of 240/415 V AC MCB - Four pole MCB - 50 A rating",
    "Each", 2425, [2185, 2670], "mcb")

add_item("mcb_distribution", "6.1.4.5",
    "Providing & Fixing of 240/415 V AC MCB - Four pole MCB - 63 A rating",
    "Each", 2825, [2545, 3110], "mcb")

# ============================================================================
# SWITCHES & ACCESSORIES - Expand modular switches
# ============================================================================

# 7.1.x - Modular Switches
add_item("switches_accessories", "7.1",
    "Providing & Fixing of IS:3854 marked modular type 6 A one way switch",
    "Each", 85, [75, 95], "switch")

add_item("switches_accessories", "7.2",
    "Providing & Fixing of IS:3854 marked modular type 6 A two way switch",
    "Each", 125, [110, 140], "switch")

add_item("switches_accessories", "7.3",
    "Providing & Fixing of IS:3854 marked modular type 6 A intermediate switch",
    "Each", 165, [150, 185], "switch")

add_item("switches_accessories", "7.4",
    "Providing & Fixing of IS:3854 marked modular type 16 A one way switch",
    "Each", 145, [130, 165], "switch")

add_item("switches_accessories", "7.5",
    "Providing & Fixing of IS:3854 marked modular type 16 A two way switch",
    "Each", 185, [165, 205], "switch")

# 7.25.x - Indicator Lamps
add_item("switches_accessories", "7.25",
    "Providing & Fixing of modular type indicator lamp",
    "Each", 125, [110, 140], "indicator")

add_item("switches_accessories", "7.26",
    "Providing & Fixing of modular type LED indicator lamp",
    "Each", 165, [150, 185], "indicator")

# 7.29.x - Telephone/TV/Data Sockets
add_item("switches_accessories", "7.29",
    "Providing & Fixing of modular type telephone socket",
    "Each", 185, [165, 205], "socket")

add_item("switches_accessories", "7.29.1",
    "Providing & Fixing of modular type TV socket",
    "Each", 225, [200, 250], "socket")

add_item("switches_accessories", "7.29.2",
    "Providing & Fixing of modular type data socket (RJ45)",
    "Each", 285, [260, 315], "socket")

# 7.30.x - Mounting Plates
add_item("switches_accessories", "7.30.1",
    "Providing & Fixing of following modular accessories - 1 Module plate",
    "Each", 45, [40, 52], "accessories")

add_item("switches_accessories", "7.30.2",
    "Providing & Fixing of following modular accessories - 2 Module plate",
    "Each", 65, [58, 75], "accessories")

add_item("switches_accessories", "7.30.3",
    "Providing & Fixing of following modular accessories - 3 Module plate",
    "Each", 85, [75, 95], "accessories")

add_item("switches_accessories", "7.30.4",
    "Providing & Fixing of following modular accessories - 4 Module plate",
    "Each", 105, [95, 120], "accessories")

add_item("switches_accessories", "7.30.5",
    "Providing & Fixing of following modular accessories - 5 Module plate",
    "Each", 125, [110, 140], "accessories")

# 7.31.x - Mounting Grids
add_item("switches_accessories", "7.31.1",
    "Providing & Fixing of following size mounting grid - 1 Module",
    "Each", 45, [40, 52], "mounting_grid")

add_item("switches_accessories", "7.31.2",
    "Providing & Fixing of following size mounting grid - 2 Module",
    "Each", 65, [58, 75], "mounting_grid")

add_item("switches_accessories", "7.31.3",
    "Providing & Fixing of following size mounting grid - 3 Module",
    "Each", 85, [75, 95], "mounting_grid")

add_item("switches_accessories", "7.31.4",
    "Providing & Fixing of following size mounting grid - 4 Module",
    "Each", 105, [95, 120], "mounting_grid")

add_item("switches_accessories", "7.31.6",
    "Providing & Fixing of following size mounting grid - 8 Module",
    "Each", 185, [165, 205], "mounting_grid")

# ============================================================================
# FANS - Expand all types
# ============================================================================

add_item("fans", "15.7.2",
    "Providing & Fixing of BEE Star rated copper wounded ceiling fan - 1200 mm Sweep BEE 2 Star rated (service value >=4.8)",
    "Each", 2225, [2000, 2450], "ceiling_fan")

add_item("fans", "15.7.3",
    "Providing & Fixing of BEE Star rated copper wounded ceiling fan - 1200 mm Sweep BEE 3 Star rated (service value >=5.0)",
    "Each", 2425, [2185, 2670], "ceiling_fan")

add_item("fans", "15.7.4",
    "Providing & Fixing of BEE Star rated copper wounded ceiling fan - 1200 mm Sweep BEE 4 Star rated (service value >=5.2)",
    "Each", 2625, [2365, 2890], "ceiling_fan")

add_item("fans", "15.7.5",
    "Providing & Fixing of BEE Star rated copper wounded ceiling fan - 1200 mm Sweep BEE 5 Star rated (service value >=5.4)",
    "Each", 2825, [2545, 3110], "ceiling_fan")

add_item("fans", "15.8.1",
    "Providing & Fixing of exhaust fan - 200 mm sweep",
    "Each", 1425, [1285, 1570], "exhaust_fan")

add_item("fans", "15.8.2",
    "Providing & Fixing of exhaust fan - 250 mm sweep",
    "Each", 1625, [1465, 1790], "exhaust_fan")

add_item("fans", "15.8.3",
    "Providing & Fixing of exhaust fan - 300 mm sweep",
    "Each", 1825, [1645, 2010], "exhaust_fan")

# ============================================================================
# LED LIGHTING - Expand all types
# ============================================================================

# 17.1.x - LED Battens
add_item("led_lighting", "17.1.2",
    "SITC of IP20 SMD Mid Power LED batten type integrated luminaire - 570mm(+/-10%) LED batten with min. lumen output 1000 lm",
    "Each", 285, [260, 315], "led_batten")

add_item("led_lighting", "17.1.3",
    "SITC of IP20 SMD Mid Power LED batten type integrated luminaire - 1470mm(+/-10%) LED batten with min. lumen output 3000 lm",
    "Each", 625, [565, 690], "led_batten")

# 17.2.x - LED Bulbs
add_item("led_lighting", "17.2.1",
    "SITC of LED bulb with B22 cap - 7W (minimum lumen output 600 lm)",
    "Each", 125, [110, 140], "led_bulb")

add_item("led_lighting", "17.2.2",
    "SITC of LED bulb with B22 cap - 9W (minimum lumen output 800 lm)",
    "Each", 145, [130, 165], "led_bulb")

add_item("led_lighting", "17.2.3",
    "SITC of LED bulb with B22 cap - 12W (minimum lumen output 1100 lm)",
    "Each", 185, [165, 205], "led_bulb")

add_item("led_lighting", "17.2.4",
    "SITC of LED bulb with B22 cap - 15W (minimum lumen output 1400 lm)",
    "Each", 225, [200, 250], "led_bulb")

# 17.3.x - LED Downlights - expand
add_item("led_lighting", "17.3.2.1",
    "SITC of IP-20 Recessed / Surface Mounted, Round / Square LED Down light - Surface Mounting - Minimum lumen output 600 lm",
    "Each", 825, [745, 910], "downlight")

add_item("led_lighting", "17.3.2.2",
    "SITC of IP-20 Recessed / Surface Mounted, Round / Square LED Down light - Surface Mounting - Minimum lumen output 800 lm",
    "Each", 985, [890, 1085], "downlight")

add_item("led_lighting", "17.3.2.3",
    "SITC of IP-20 Recessed / Surface Mounted, Round / Square LED Down light - Surface Mounting - Minimum lumen output 1000 lm",
    "Each", 1185, [1070, 1305], "downlight")

# 18.x - Street Lights - expand
add_item("led_lighting", "18.13.1",
    "Providing & Fixing of IK0B, IP 66 protected LED Street light fixture - Minimum lumen output 3750 lm (30W)",
    "Each", 2425, [2185, 2670], "street_light")

add_item("led_lighting", "18.13.2",
    "Providing & Fixing of IK0B, IP 66 protected LED Street light fixture - Minimum lumen output 5625 lm (45W)",
    "Each", 3225, [2905, 3550], "street_light")

add_item("led_lighting", "18.13.3",
    "Providing & Fixing of IK0B, IP 66 protected LED Street light fixture - Minimum lumen output 7500 lm (60W)",
    "Each", 4025, [3625, 4430], "street_light")

add_item("led_lighting", "18.13.4",
    "Providing & Fixing of IK0B, IP 66 protected LED Street light fixture - Minimum lumen output 9375 lm (75W)",
    "Each", 4825, [4345, 5310], "street_light")

add_item("led_lighting", "18.13.5",
    "Providing & Fixing of IK0B, IP 66 protected LED Street light fixture - Minimum lumen output 11250 lm (90W)",
    "Each", 5617, [5060, 6180], "street_light")

add_item("led_lighting", "18.13.7",
    "Providing & Fixing of IK0B, IP 66 protected LED Street light fixture - Minimum lumen output 15000 lm (120W)",
    "Each", 7225, [6505, 7950], "street_light")

add_item("led_lighting", "18.13.8",
    "Providing & Fixing of IK0B, IP 66 protected LED Street light fixture - Minimum lumen output 18750 lm (150W)",
    "Each", 8825, [7945, 9710], "street_light")

# Update metadata
db['total_items'] = sum(len(items) for items in db['categories'].values())
db['last_updated'] = "2026-03-13"

# Save expanded database
with open(db_path, 'w', encoding='utf-8') as f:
    json.dump(db, f, indent=2, ensure_ascii=False)

print(f"Database expanded successfully!")
print(f"Total items: {db['total_items']}")
print(f"\nItems by category:")
for category, items in db['categories'].items():
    print(f"  {category}: {len(items)} items")
