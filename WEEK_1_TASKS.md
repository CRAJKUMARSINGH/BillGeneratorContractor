# WEEK 1: PWD DATABASE FOUNDATION

**Dates:** March 17-21, 2026  
**Goal:** Create comprehensive PWD BSR database  
**Status:** 🚀 STARTING NOW

---

## 📋 DAILY TASKS

### Day 1 (Monday): Research & Planning
- [x] Review PWD BSR 2024 schedule format
- [x] Identify data sources
- [x] Design database schema
- [ ] Create sample database structure

### Day 2 (Tuesday): Data Collection
- [ ] Extract BSR codes from available documents
- [ ] Collect rates, units, descriptions
- [ ] Organize data by category
- [ ] Validate data accuracy

### Day 3 (Wednesday): Database Implementation
- [ ] Create JSON database file
- [ ] Implement database schema
- [ ] Add 100+ BSR codes
- [ ] Create query functions

### Day 4 (Thursday): Expansion
- [ ] Add 200+ more BSR codes
- [ ] Add rate ranges (min/max)
- [ ] Add category tags
- [ ] Add search functionality

### Day 5 (Friday): Testing & Documentation
- [ ] Test all query functions
- [ ] Add unit tests
- [ ] Document database structure
- [ ] Create usage examples

---

## 🎯 DELIVERABLES

1. **data/pwd_bsr_database.json**
   - 500+ BSR codes
   - Complete with rates, units, descriptions
   - Organized by category

2. **modules/pwd_database.py**
   - Query by BSR code
   - Search by description
   - Filter by rate range
   - Validate BSR codes

3. **tests/test_pwd_database.py**
   - Unit tests for all functions
   - Edge case testing
   - Performance tests

---

## 📊 DATABASE SCHEMA

```json
{
  "version": "2024",
  "last_updated": "2026-03-17",
  "categories": {
    "electrical_wiring": {
      "1.1.1": {
        "description": "Wiring of light point/ fan point/ exhaust fan point/ call bell point - Short point (up to 3 mtr.)",
        "unit": "P. point",
        "rate_2024": 343,
        "rate_range": [300, 400],
        "category": "electrical_wiring",
        "subcategory": "light_points",
        "keywords": ["wiring", "light", "fan", "short"]
      },
      "1.1.2": {
        "description": "Wiring of light point/ fan point/ exhaust fan point/ call bell point - Medium point (up to 6 mtr.)",
        "unit": "P. point",
        "rate_2024": 601,
        "rate_range": [550, 650],
        "category": "electrical_wiring",
        "subcategory": "light_points",
        "keywords": ["wiring", "light", "fan", "medium"]
      }
    }
  }
}
```

---

## 🔧 IMPLEMENTATION STARTED

Let me create the initial database structure now...
