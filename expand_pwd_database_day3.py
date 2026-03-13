#!/usr/bin/env python3
"""
Expand PWD BSR Database - Week 1 Day 3
Add earthing, distribution boards, cable accessories, junction boxes
Target: 200+ items
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
# EARTHING & GROUNDING
# ============================================================================

add_item("earthing_grounding", "8.1",
    "Providing & Fixing of earthing electrode - Plate earthing with GI plate 600x600x6mm",
    "Each", 2825, [2545, 3110], "plate_earthing")

add_item("earthing_grounding", "8.2",
    "Providing & Fixing of earthing electrode - Pipe earthing with GI pipe 40mm dia x 2.5m long",
    "Each", 1825, [1645, 2010], "pipe_earthing")

add_item("earthing_grounding", "8.3",
    "Providing & Fixing of earthing electrode - Rod earthing with copper bonded rod 14mm dia x 3m long",
    "Each", 3225, [2905, 3550], "rod_earthing")

add_item("earthing_grounding", "8.4.1",
    "Providing & laying GI earthing strip - 25x6mm",
    "Mtr.", 185, [165, 205], "earthing_strip")

add_item("earthing_grounding", "8.4.2",
    "Providing & laying GI earthing strip - 25x3mm",
    "Mtr.", 125, [110, 140], "earthing_strip")

add_item("earthing_grounding", "8.5.1",
    "Providing & laying copper earthing strip - 25x6mm",
    "Mtr.", 425, [380, 470], "earthing_strip")

add_item("earthing_grounding", "8.5.2",
    "Providing & laying copper earthing strip - 25x3mm",
    "Mtr.", 285, [260, 315], "earthing_strip")

add_item("earthing_grounding", "8.6",
    "Providing & Fixing of earthing chamber with CI cover 450x450mm",
    "Each", 1425, [1285, 1570], "earthing_chamber")

add_item("earthing_grounding", "8.7",
    "Providing & Fixing of earthing clamp for GI pipe",
    "Each", 125, [110, 140], "earthing_clamp")

add_item("earthing_grounding", "8.8",
    "Providing & Fixing of earthing clamp for copper rod",
    "Each", 185, [165, 205], "earthing_clamp")

add_item("earthing_grounding", "8.9",
    "Providing & Fixing of lightning arrester with earthing",
    "Each", 5625, [5065, 6190], "lightning_arrester")

add_item("earthing_grounding", "8.10",
    "Testing of earthing system and providing test report",
    "Each", 825, [745, 910], "testing")

# ============================================================================
# DISTRIBUTION BOARDS - Expanded
# ============================================================================

add_item("mcb_distribution", "6.10.1.1",
    "Providing & Fixing of Recessed/surface mounting heavy duty distribution board - Metal door (Single phase) - 2 Way (4 Incomer + 6 Outgoing)",
    "Each", 1825, [1645, 2010], "distribution_board")

add_item("mcb_distribution", "6.10.1.2",
    "Providing & Fixing of Recessed/surface mounting heavy duty distribution board - Metal door (Single phase) - 4 Way (4 Incomer + 12 Outgoing)",
    "Each", 2425, [2185, 2670], "distribution_board")

add_item("mcb_distribution", "6.10.1.3",
    "Providing & Fixing of Recessed/surface mounting heavy duty distribution board - Metal door (Single phase) - 6 Way (4 Incomer + 18 Outgoing)",
    "Each", 3025, [2725, 3330], "distribution_board")

add_item("mcb_distribution", "6.10.2.1",
    "Providing & Fixing of Recessed/surface mounting heavy duty distribution board - Metal door (Three phase) - 2 Way (8 Incomer + 6 Outgoing)",
    "Each", 2825, [2545, 3110], "distribution_board")

add_item("mcb_distribution", "6.10.2.2",
    "Providing & Fixing of Recessed/surface mounting heavy duty distribution board - Metal door (Three phase) - 4 Way (8 Incomer + 12 Outgoing)",
    "Each", 3825, [3445, 4210], "distribution_board")

add_item("mcb_distribution", "6.10.3.1",
    "Providing & Fixing of Recessed/surface mounting heavy duty distribution board - Metal door (Three phase) - 4 Way (8 Incomer + 12 Outgoing)",
    "Each", 4225, [3805, 4650], "distribution_board")

add_item("mcb_distribution", "6.10.3.3",
    "Providing & Fixing of Recessed/surface mounting heavy duty distribution board - Metal door (Three phase) - 8 Way (8 Incomer + 24 Outgoing)",
    "Each", 6825, [6145, 7510], "distribution_board")

add_item("mcb_distribution", "6.11.1",
    "Providing & Fixing of RCCB - 2 Pole 30mA 40A",
    "Each", 1225, [1105, 1350], "rccb")

add_item("mcb_distribution", "6.11.2",
    "Providing & Fixing of RCCB - 2 Pole 30mA 63A",
    "Each", 1625, [1465, 1790], "rccb")

add_item("mcb_distribution", "6.11.3",
    "Providing & Fixing of RCCB - 4 Pole 30mA 40A",
    "Each", 2425, [2185, 2670], "rccb")

add_item("mcb_distribution", "6.11.4",
    "Providing & Fixing of RCCB - 4 Pole 30mA 63A",
    "Each", 3025, [2725, 3330], "rccb")

add_item("mcb_distribution", "6.12.1",
    "Providing & Fixing of RCBO - Single Pole 30mA 16A",
    "Each", 825, [745, 910], "rcbo")

add_item("mcb_distribution", "6.12.2",
    "Providing & Fixing of RCBO - Single Pole 30mA 32A",
    "Each", 1025, [925, 1130], "rcbo")

# ============================================================================
# CABLE GLANDS & ACCESSORIES
# ============================================================================

add_item("cable_accessories", "9.1.1",
    "Providing & Fixing of brass cable gland - 20mm",
    "Each", 85, [75, 95], "cable_gland")

add_item("cable_accessories", "9.1.2",
    "Providing & Fixing of brass cable gland - 25mm",
    "Each", 105, [95, 120], "cable_gland")

add_item("cable_accessories", "9.1.3",
    "Providing & Fixing of brass cable gland - 32mm",
    "Each", 145, [130, 165], "cable_gland")

add_item("cable_accessories", "9.1.4",
    "Providing & Fixing of brass cable gland - 40mm",
    "Each", 185, [165, 205], "cable_gland")

add_item("cable_accessories", "9.1.5",
    "Providing & Fixing of brass cable gland - 50mm",
    "Each", 245, [220, 270], "cable_gland")

add_item("cable_accessories", "9.2.1",
    "Providing & Fixing of cable lugs - 2.5 sq.mm",
    "Each", 15, [12, 18], "cable_lug")

add_item("cable_accessories", "9.2.2",
    "Providing & Fixing of cable lugs - 4.0 sq.mm",
    "Each", 18, [15, 22], "cable_lug")

add_item("cable_accessories", "9.2.3",
    "Providing & Fixing of cable lugs - 6.0 sq.mm",
    "Each", 22, [18, 26], "cable_lug")

add_item("cable_accessories", "9.2.4",
    "Providing & Fixing of cable lugs - 10.0 sq.mm",
    "Each", 28, [24, 32], "cable_lug")

add_item("cable_accessories", "9.2.5",
    "Providing & Fixing of cable lugs - 16.0 sq.mm",
    "Each", 38, [32, 45], "cable_lug")

add_item("cable_accessories", "9.3.1",
    "Providing & Fixing of cable ties - 100mm",
    "Each", 2, [1, 3], "cable_tie")

add_item("cable_accessories", "9.3.2",
    "Providing & Fixing of cable ties - 200mm",
    "Each", 3, [2, 4], "cable_tie")

add_item("cable_accessories", "9.3.3",
    "Providing & Fixing of cable ties - 300mm",
    "Each", 5, [4, 6], "cable_tie")

add_item("cable_accessories", "9.4.1",
    "Providing & Fixing of cable marker - Numeric (0-9)",
    "Set", 125, [110, 140], "cable_marker")

add_item("cable_accessories", "9.4.2",
    "Providing & Fixing of cable marker - Alphabetic (A-Z)",
    "Set", 145, [130, 165], "cable_marker")

# ============================================================================
# JUNCTION BOXES & ENCLOSURES
# ============================================================================

add_item("junction_boxes", "10.1.1",
    "Providing & Fixing of PVC junction box - 75x75x40mm",
    "Each", 45, [40, 52], "junction_box")

add_item("junction_boxes", "10.1.2",
    "Providing & Fixing of PVC junction box - 100x100x50mm",
    "Each", 65, [58, 75], "junction_box")

add_item("junction_boxes", "10.1.3",
    "Providing & Fixing of PVC junction box - 150x110x70mm",
    "Each", 95, [85, 110], "junction_box")

add_item("junction_boxes", "10.1.4",
    "Providing & Fixing of PVC junction box - 200x150x80mm",
    "Each", 145, [130, 165], "junction_box")

add_item("junction_boxes", "10.2.1",
    "Providing & Fixing of metal junction box - 100x100x50mm",
    "Each", 185, [165, 205], "junction_box")

add_item("junction_boxes", "10.2.2",
    "Providing & Fixing of metal junction box - 150x150x75mm",
    "Each", 285, [260, 315], "junction_box")

add_item("junction_boxes", "10.2.3",
    "Providing & Fixing of metal junction box - 200x200x100mm",
    "Each", 425, [380, 470], "junction_box")

add_item("junction_boxes", "10.3.1",
    "Providing & Fixing of weatherproof junction box - 150x150x100mm IP65",
    "Each", 525, [475, 580], "weatherproof_box")

add_item("junction_boxes", "10.3.2",
    "Providing & Fixing of weatherproof junction box - 200x200x150mm IP65",
    "Each", 725, [655, 800], "weatherproof_box")

add_item("junction_boxes", "10.3.3",
    "Providing & Fixing of weatherproof junction box - 300x250x150mm IP65",
    "Each", 1025, [925, 1130], "weatherproof_box")

add_item("junction_boxes", "10.4.1",
    "Providing & Fixing of metal enclosure - 300x400x200mm",
    "Each", 2425, [2185, 2670], "enclosure")

add_item("junction_boxes", "10.4.2",
    "Providing & Fixing of metal enclosure - 400x500x200mm",
    "Each", 3225, [2905, 3550], "enclosure")

add_item("junction_boxes", "10.4.3",
    "Providing & Fixing of metal enclosure - 500x600x250mm",
    "Each", 4225, [3805, 4650], "enclosure")

# ============================================================================
# CONDUIT FITTINGS & ACCESSORIES
# ============================================================================

add_item("conduit_fittings", "11.1.1",
    "Providing & Fixing of PVC conduit bend - 20mm",
    "Each", 12, [10, 15], "conduit_bend")

add_item("conduit_fittings", "11.1.2",
    "Providing & Fixing of PVC conduit bend - 25mm",
    "Each", 15, [12, 18], "conduit_bend")

add_item("conduit_fittings", "11.1.3",
    "Providing & Fixing of PVC conduit bend - 32mm",
    "Each", 22, [18, 26], "conduit_bend")

add_item("conduit_fittings", "11.1.4",
    "Providing & Fixing of PVC conduit bend - 40mm",
    "Each", 28, [24, 32], "conduit_bend")

add_item("conduit_fittings", "11.2.1",
    "Providing & Fixing of PVC conduit coupler - 20mm",
    "Each", 8, [6, 10], "conduit_coupler")

add_item("conduit_fittings", "11.2.2",
    "Providing & Fixing of PVC conduit coupler - 25mm",
    "Each", 10, [8, 12], "conduit_coupler")

add_item("conduit_fittings", "11.2.3",
    "Providing & Fixing of PVC conduit coupler - 32mm",
    "Each", 15, [12, 18], "conduit_coupler")

add_item("conduit_fittings", "11.2.4",
    "Providing & Fixing of PVC conduit coupler - 40mm",
    "Each", 18, [15, 22], "conduit_coupler")

add_item("conduit_fittings", "11.3.1",
    "Providing & Fixing of PVC conduit tee - 20mm",
    "Each", 15, [12, 18], "conduit_tee")

add_item("conduit_fittings", "11.3.2",
    "Providing & Fixing of PVC conduit tee - 25mm",
    "Each", 18, [15, 22], "conduit_tee")

add_item("conduit_fittings", "11.3.3",
    "Providing & Fixing of PVC conduit tee - 32mm",
    "Each", 25, [20, 30], "conduit_tee")

add_item("conduit_fittings", "11.4.1",
    "Providing & Fixing of PVC conduit saddle - 20mm",
    "Each", 5, [4, 6], "conduit_saddle")

add_item("conduit_fittings", "11.4.2",
    "Providing & Fixing of PVC conduit saddle - 25mm",
    "Each", 6, [5, 8], "conduit_saddle")

add_item("conduit_fittings", "11.4.3",
    "Providing & Fixing of PVC conduit saddle - 32mm",
    "Each", 8, [6, 10], "conduit_saddle")

# Update metadata
db['total_items'] = sum(len(items) for items in db['categories'].values())
db['last_updated'] = "2026-03-13"

# Save expanded database
with open(db_path, 'w', encoding='utf-8') as f:
    json.dump(db, f, indent=2, ensure_ascii=False)

print(f"Database expanded successfully!")
print(f"Total items: {db['total_items']}")
print(f"\nItems by category:")
for category, items in sorted(db['categories'].items()):
    print(f"  {category}: {len(items)} items")
