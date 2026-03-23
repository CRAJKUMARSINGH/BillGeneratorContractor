#!/usr/bin/env python3
"""
Confidence Scoring Module - Week 2 Day 5
Multi-factor confidence calculation for extracted items
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dataclasses import dataclass
from typing import Dict, List
from modules.validators import validate_item, ValidationResult
from modules.pwd_database import PWDDatabase


@dataclass
class ConfidenceScore:
    """Confidence score breakdown"""
    overall: float  # 0.0 to 1.0
    code_confidence: float
    rate_confidence: float
    unit_confidence: float
    validation_result: ValidationResult
    
    @property
    def level(self) -> str:
        """Get confidence level"""
        if self.overall >= 0.95:
            return "VERY_HIGH"
        elif self.overall >= 0.85:
            return "HIGH"
        elif self.overall >= 0.70:
            return "MEDIUM"
        elif self.overall >= 0.50:
            return "LOW"
        else:
            return "VERY_LOW"
    
    @property
    def action(self) -> str:
        """Get recommended action"""
        if self.overall >= 0.95:
            return "AUTO_ACCEPT"
        elif self.overall >= 0.85:
            return "QUICK_REVIEW"
        elif self.overall >= 0.70:
            return "REVIEW"
        else:
            return "DETAILED_REVIEW"


class ConfidenceScorer:
    """Calculate confidence scores for extracted items"""
    
    def __init__(self, db: PWDDatabase = None):
        self.db = db or PWDDatabase()
    
    def score_item(self, item: Dict) -> ConfidenceScore:
        """Calculate confidence score for an item"""
        # Validate the item
        validation_result = validate_item(item, self.db)
        
        # Extract individual confidences
        code_confidence = self._get_code_confidence(validation_result)
        rate_confidence = self._get_rate_confidence(validation_result)
        unit_confidence = self._get_unit_confidence(validation_result)
        
        # Calculate overall confidence (weighted average)
        # Code: 50%, Rate: 30%, Unit: 20%
        overall = (
            code_confidence * 0.5 +
            rate_confidence * 0.3 +
            unit_confidence * 0.2
        )
        
        return ConfidenceScore(
            overall=overall,
            code_confidence=code_confidence,
            rate_confidence=rate_confidence,
            unit_confidence=unit_confidence,
            validation_result=validation_result
        )
    
    def _get_code_confidence(self, result: ValidationResult) -> float:
        """Extract code confidence from validation result"""
        code_messages = [m for m in result.messages if m.field == 'code']
        if not code_messages:
            return 0.5  # No code validation
        
        # Check for errors
        code_errors = [m for m in code_messages if m.level.value == 'error']
        if code_errors:
            return 0.0
        
        # Check for warnings
        code_warnings = [m for m in code_messages if m.level.value == 'warning']
        if code_warnings:
            return 0.6
        
        return 1.0
    
    def _get_rate_confidence(self, result: ValidationResult) -> float:
        """Extract rate confidence from validation result"""
        rate_messages = [m for m in result.messages if m.field == 'rate']
        if not rate_messages:
            return 0.5  # No rate validation
        
        # Check for errors
        rate_errors = [m for m in rate_messages if m.level.value == 'error']
        if rate_errors:
            return 0.3
        
        # Check for warnings
        rate_warnings = [m for m in rate_messages if m.level.value == 'warning']
        if rate_warnings:
            return 0.5
        
        return 1.0
    
    def _get_unit_confidence(self, result: ValidationResult) -> float:
        """Extract unit confidence from validation result"""
        unit_messages = [m for m in result.messages if m.field == 'unit']
        if not unit_messages:
            return 0.5  # No unit validation
        
        # Check for errors
        unit_errors = [m for m in unit_messages if m.level.value == 'error']
        if unit_errors:
            return 0.0
        
        # Check for warnings
        unit_warnings = [m for m in unit_messages if m.level.value == 'warning']
        if unit_warnings:
            return 0.7
        
        return 1.0
    
    def score_items(self, items: List[Dict]) -> List[ConfidenceScore]:
        """Score multiple items"""
        return [self.score_item(item) for item in items]
    
    def generate_report(self, items: List[Dict]) -> Dict:
        """Generate confidence report for items"""
        scores = self.score_items(items)
        
        # Calculate statistics
        total = len(scores)
        very_high = sum(1 for s in scores if s.level == "VERY_HIGH")
        high = sum(1 for s in scores if s.level == "HIGH")
        medium = sum(1 for s in scores if s.level == "MEDIUM")
        low = sum(1 for s in scores if s.level == "LOW")
        very_low = sum(1 for s in scores if s.level == "VERY_LOW")
        
        avg_confidence = sum(s.overall for s in scores) / total if total > 0 else 0
        
        # Count actions
        auto_accept = sum(1 for s in scores if s.action == "AUTO_ACCEPT")
        quick_review = sum(1 for s in scores if s.action == "QUICK_REVIEW")
        review = sum(1 for s in scores if s.action == "REVIEW")
        detailed_review = sum(1 for s in scores if s.action == "DETAILED_REVIEW")
        
        return {
            'total_items': total,
            'average_confidence': avg_confidence,
            'confidence_levels': {
                'very_high': {'count': very_high, 'percentage': very_high/total*100 if total > 0 else 0},
                'high': {'count': high, 'percentage': high/total*100 if total > 0 else 0},
                'medium': {'count': medium, 'percentage': medium/total*100 if total > 0 else 0},
                'low': {'count': low, 'percentage': low/total*100 if total > 0 else 0},
                'very_low': {'count': very_low, 'percentage': very_low/total*100 if total > 0 else 0},
            },
            'recommended_actions': {
                'auto_accept': {'count': auto_accept, 'percentage': auto_accept/total*100 if total > 0 else 0},
                'quick_review': {'count': quick_review, 'percentage': quick_review/total*100 if total > 0 else 0},
                'review': {'count': review, 'percentage': review/total*100 if total > 0 else 0},
                'detailed_review': {'count': detailed_review, 'percentage': detailed_review/total*100 if total > 0 else 0},
            },
            'scores': scores
        }


if __name__ == '__main__':
    # Test the confidence scorer
    print("\n" + "="*80)
    print("CONFIDENCE SCORING TEST - WEEK 2 DAY 5")
    print("="*80)
    
    # Test items with varying quality
    test_items = [
        {'code': '1.1.2', 'unit': 'P. point', 'rate': 601, 'quantity': 10},  # Perfect
        {'code': '4.1.7', 'unit': 'Mtr.', 'rate': 106, 'quantity': 50},  # Perfect
        {'code': '18.13.6', 'unit': 'Each', 'rate': 5617, 'quantity': 5},  # Perfect
        {'code': '1.1.2', 'unit': 'point', 'rate': 601, 'quantity': 10},  # Unit variation
        {'code': '1.1.2', 'unit': 'P. point', 'rate': 650, 'quantity': 10},  # Rate at edge
        {'code': '1.1.2', 'unit': 'P. point', 'rate': 800, 'quantity': 10},  # Rate outside
        {'code': '99.99', 'unit': 'Each', 'rate': 100, 'quantity': 1},  # Invalid code
    ]
    
    scorer = ConfidenceScorer()
    
    print("\nIndividual Item Scores:")
    print("-" * 80)
    
    for i, item in enumerate(test_items, 1):
        score = scorer.score_item(item)
        print(f"\n{i}. {item['code']} - Rs. {item['rate']} - {item['unit']}")
        print(f"   Overall: {score.overall:.2f} ({score.level})")
        print(f"   Code: {score.code_confidence:.2f}, Rate: {score.rate_confidence:.2f}, Unit: {score.unit_confidence:.2f}")
        print(f"   Action: {score.action}")
        
        if score.validation_result.errors:
            print(f"   Errors: {len(score.validation_result.errors)}")
            for err in score.validation_result.errors:
                print(f"     - {err.message}")
    
    # Generate report
    print("\n" + "="*80)
    print("CONFIDENCE REPORT")
    print("="*80)
    
    report = scorer.generate_report(test_items)
    
    print(f"\nTotal Items: {report['total_items']}")
    print(f"Average Confidence: {report['average_confidence']:.2f}")
    
    print(f"\nConfidence Levels:")
    for level, data in report['confidence_levels'].items():
        print(f"  {level.upper():12s}: {data['count']:2d} items ({data['percentage']:5.1f}%)")
    
    print(f"\nRecommended Actions:")
    for action, data in report['recommended_actions'].items():
        print(f"  {action.upper():16s}: {data['count']:2d} items ({data['percentage']:5.1f}%)")
    
    print("\n" + "="*80)
    print("CONFIDENCE SCORING: OPERATIONAL")
    print("="*80 + "\n")
