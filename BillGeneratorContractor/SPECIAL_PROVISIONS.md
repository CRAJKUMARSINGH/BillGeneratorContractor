# Special Provisions - Smart Cascading OCR Engine

## Overview

This document describes the intelligent OCR system implemented in the BillGenerator Unified application. The system automatically selects the best OCR provider based on output quality, with automatic fallback to alternative providers when results are suboptimal.

## Architecture

### Multi-Provider OCR System

The application supports four production-grade OCR providers with automatic quality-based selection:

1. **Google Cloud Vision API** (Priority 1)
   - Best accuracy for Hindi + English mixed documents
   - Enterprise-grade reliability
   - Requires: Google Cloud credentials or API key

2. **Azure Computer Vision** (Priority 2)
   - Microsoft's enterprise OCR solution
   - Excellent for structured documents
   - Requires: Azure endpoint and API key

3. **PaddleOCR** (Priority 3)
   - Excellent offline multilingual support
   - No API costs, runs locally
   - Requires: `pip install paddleocr`

4. **EasyOCR** (Priority 4)
   - Reliable baseline OCR
   - Works offline, no dependencies
   - Requires: `pip install easyocr`

## Smart Cascading Logic

### Quality Validation Metrics

The system evaluates OCR output quality using a composite score (0.0-1.0) based on:

| Metric | Weight | Description |
|--------|--------|-------------|
| **Confidence Score** | 40% | Provider's reported confidence in text recognition |
| **Word Count** | 20% | Number of words extracted (minimum 20 expected) |
| **Text Coherence** | 20% | Ratio of alphanumeric characters to total characters |
| **Pattern Detection** | 20% | Presence of expected patterns (numbers, keywords, amounts) |

### Pattern Detection Criteria

The system checks for work order-specific patterns:

- **Numbers**: Item codes, quantities (e.g., "1.1.2", "50")
- **Decimal values**: Rates, amounts (e.g., "602.00", "11.22")
- **Keywords**: "work", "contractor", "amount", "item", "quantity", "rate"

### Automatic Fallback Process

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Try Google Cloud Vision API                             │
│    ├─ Extract text                                          │
│    ├─ Calculate quality score                               │
│    └─ If quality ≥ 70% confidence + 5 words → SUCCESS ✓    │
│       Else → Try next provider                              │
├─────────────────────────────────────────────────────────────┤
│ 2. Try Azure Computer Vision                               │
│    ├─ Extract text                                          │
│    ├─ Calculate quality score                               │
│    └─ If quality ≥ 70% confidence + 5 words → SUCCESS ✓    │
│       Else → Try next provider                              │
├─────────────────────────────────────────────────────────────┤
│ 3. Try PaddleOCR                                            │
│    ├─ Extract text                                          │
│    ├─ Calculate quality score                               │
│    └─ If quality ≥ 70% confidence + 5 words → SUCCESS ✓    │
│       Else → Try next provider                              │
├─────────────────────────────────────────────────────────────┤
│ 4. Try EasyOCR                                              │
│    ├─ Extract text                                          │
│    ├─ Calculate quality score                               │
│    └─ If quality ≥ 70% confidence + 5 words → SUCCESS ✓    │
│       Else → Return best result from all attempts           │
└─────────────────────────────────────────────────────────────┘
```

## Advanced Features

### 1. Consensus Mode

Runs multiple OCR providers simultaneously and selects the best result:

```python
result = ocr_engine.extract_with_consensus(image, providers=['google', 'azure', 'paddle'])
```

**Use case**: Critical documents where maximum accuracy is required

### 2. Retry with Preprocessing

Automatically retries OCR with different image preprocessing techniques:

```python
result = ocr_engine.extract_with_retry(image, max_attempts=3, preprocess=True)
```

**Preprocessing methods**:
- Method 1: Grayscale → Gaussian blur → Otsu threshold
- Method 2: Adaptive threshold
- Method 3: Denoise → Sharpen

**Use case**: Poor quality scans, low contrast images, noisy documents

### 3. Quality Thresholds

Configurable quality requirements:

```python
result = ocr_engine.extract_text(
    image, 
    min_confidence=0.8,  # Require 80% confidence
    min_words=10         # Require at least 10 words
)
```

## Configuration

### Environment Variables

Set up OCR providers in `.env`:

```bash
# Google Cloud Vision
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account-key.json
GOOGLE_CLOUD_VISION_API_KEY=your_api_key_here

# Azure Computer Vision
AZURE_COMPUTER_VISION_KEY=your_azure_key_here
AZURE_COMPUTER_VISION_ENDPOINT=https://your-resource.cognitiveservices.azure.com/

# OCR Settings
OCR_LANGUAGE=en+hi
OCR_CONFIDENCE_THRESHOLD=0.7
HWR_PROVIDER=google
```

### Provider Selection

**Automatic (Recommended)**:
```python
ocr_engine = UnifiedOCREngine(language="en+hi")
# Automatically tries providers in priority order
```

**Force Specific Provider**:
```python
ocr_engine = UnifiedOCREngine(language="en+hi", preferred_provider="paddle")
# Always tries PaddleOCR first
```

## Usage Examples

### Basic Usage

```python
from core.processors.document.unified_ocr_engine import get_ocr_engine
import cv2

# Initialize engine
ocr = get_ocr_engine(language="en+hi")

# Load image
image = cv2.imread("work_order.jpg")

# Extract text with automatic fallback
result = ocr.extract_text(image)

print(f"Provider used: {result.provider}")
print(f"Confidence: {result.confidence:.2%}")
print(f"Text: {result.text}")
```

### Structured Data Extraction

```python
# Extract structured work order data
data = ocr.extract_structured_data(image)

print(f"Contractor: {data['contractor']}")
print(f"Work Name: {data['work_name']}")
print(f"WO Number: {data['wo_number']}")
print(f"Amount: {data['wo_amount']}")
print(f"Items: {len(data['items'])}")
```

### High-Accuracy Mode

```python
# Use consensus mode for critical documents
result = ocr.extract_with_consensus(
    image, 
    providers=['google', 'azure', 'paddle']
)

# Or use retry with preprocessing
result = ocr.extract_with_retry(
    image, 
    max_attempts=3, 
    preprocess=True
)
```

## Performance Characteristics

| Provider | Speed | Accuracy | Cost | Offline |
|----------|-------|----------|------|---------|
| Google Cloud Vision | Fast | Excellent | Pay-per-use | No |
| Azure Computer Vision | Fast | Excellent | Pay-per-use | No |
| PaddleOCR | Medium | Very Good | Free | Yes |
| EasyOCR | Slow | Good | Free | Yes |

## Quality Assurance

### Automatic Quality Checks

The system performs these checks on every OCR result:

1. **Minimum confidence threshold**: Default 70%
2. **Minimum word count**: Default 5 words
3. **Text coherence**: At least 60% alphanumeric characters
4. **Pattern presence**: Expected work order patterns detected

### Logging and Diagnostics

Each OCR attempt logs:
- Provider name
- Confidence score
- Word count
- Quality score
- Success/failure status

Example output:
```
🔍 Trying GOOGLE OCR...
   ✓ Confidence: 92.50%
   ✓ Words extracted: 47
   ✓ Quality score: 88.30%
   ✅ GOOGLE passed quality check!
```

## Best Practices

### 1. Provider Setup

- **Production**: Set up Google Cloud Vision or Azure for best accuracy
- **Development**: Use PaddleOCR or EasyOCR for offline testing
- **Hybrid**: Configure multiple providers for automatic fallback

### 2. Image Quality

For best results, ensure:
- Resolution: Minimum 300 DPI
- Format: JPEG or PNG
- Contrast: Clear text on background
- Orientation: Correct (not rotated)

### 3. Language Configuration

- Hindi + English: `language="en+hi"`
- English only: `language="en"`
- Hindi only: `language="hi"`

### 4. Error Handling

Always handle OCR failures gracefully:

```python
try:
    result = ocr.extract_text(image)
    if result.confidence < 0.7:
        # Low confidence - may need manual review
        print("⚠️ Low confidence result")
except RuntimeError as e:
    # All providers failed
    print(f"❌ OCR failed: {e}")
    # Fallback to manual entry
```

## Troubleshooting

### No Providers Available

**Error**: `RuntimeError: No OCR providers available`

**Solution**: Install at least one OCR library:
```bash
pip install easyocr
# or
pip install paddleocr
```

### Low Quality Results

**Symptoms**: Confidence < 70%, missing text, garbled output

**Solutions**:
1. Use retry with preprocessing: `extract_with_retry(image, preprocess=True)`
2. Try consensus mode: `extract_with_consensus(image)`
3. Improve image quality (scan at higher DPI)
4. Set up cloud provider (Google/Azure) for better accuracy

### Provider Authentication Failed

**Google Cloud Vision**:
- Verify `GOOGLE_APPLICATION_CREDENTIALS` path is correct
- Check service account has Vision API enabled

**Azure Computer Vision**:
- Verify `AZURE_COMPUTER_VISION_KEY` is valid
- Check `AZURE_COMPUTER_VISION_ENDPOINT` URL is correct

## Future Enhancements

Planned improvements:

1. **Machine Learning Quality Predictor**: Train model to predict which provider will work best for each image type
2. **Parallel Processing**: Run multiple providers simultaneously for faster consensus
3. **Custom Training**: Fine-tune models on work order-specific vocabulary
4. **Confidence Calibration**: Adjust confidence scores based on historical accuracy
5. **Template Matching**: Use document templates to validate extracted data

## Technical Implementation

### File Location

`core/processors/document/unified_ocr_engine.py`

### Key Classes

- `UnifiedOCREngine`: Main OCR engine with cascading logic
- `OCRResult`: Standardized result format across all providers
- `OCRWord`: Individual word with position and confidence

### Dependencies

```
easyocr>=1.7.0
paddleocr>=2.7.0
google-cloud-vision>=3.4.0
azure-cognitiveservices-vision-computervision>=0.9.0
opencv-python>=4.8.0
numpy>=1.24.0
```

## Support

For issues or questions:
1. Check logs for detailed error messages
2. Verify environment variables are set correctly
3. Test with sample images to isolate issues
4. Review quality scores to understand why providers failed

---

**Document Version**: 1.0  
**Last Updated**: 2026-03-11  
**Author**: BillGenerator Development Team
