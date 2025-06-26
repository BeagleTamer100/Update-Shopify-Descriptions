# Shopify Product Description Updater

A Python tool for automatically updating Shopify product descriptions using OpenAI's GPT models. This tool can process CSV exports from Shopify and generate enhanced product descriptions.

## Features

- **AI-Powered Descriptions**: Uses OpenAI GPT models to generate compelling product descriptions
- **Batch Processing**: Handles large CSV files with progress tracking and resume capability
- **Multiple Update Modes**: 
  - Full description replacement
  - Append to existing descriptions
  - Update specific fields only
- **Progress Tracking**: Saves progress to allow resuming interrupted operations
- **Export Options**: Export updated products to new CSV files
- **Error Handling**: Robust error handling with detailed logging

## Requirements

- Python 3.7+
- OpenAI API key
- Shopify CSV export file

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd update-shopify-descriptions
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your OpenAI API key:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Usage

### Basic Usage

```python
from openai_enhanced_updater import OpenAIEnhancedUpdater

# Initialize the updater
updater = OpenAIEnhancedUpdater("products_export.csv", "your-openai-api-key")

# Update all products
updater.update_all_products()

# Export results
updater.export_results("updated_products.csv")
```

### Command Line Usage

```bash
# Update all products in a CSV file
python openai_enhanced_updater.py products_export.csv

# Export partial results from interrupted process
python export_partial_results.py products_export.csv
```

### Configuration Options

The updater supports various configuration options:

- **Update Mode**: Choose between replacing descriptions or appending to existing ones
- **Batch Size**: Control how many products are processed in each batch
- **Field Selection**: Specify which fields to update (title, description, etc.)
- **Language**: Set the language for generated descriptions

## File Structure

```
├── openai_enhanced_updater.py      # Main updater class
├── export_partial_results.py       # Export partial results utility
├── requirements.txt                # Python dependencies
├── README.md                      # This file
├── .gitignore                     # Git ignore rules
├── not ai version/                # Non-AI version of the updater
│   ├── enhanced_product_updater.py
│   ├── enhanced_updater.py
│   └── update_product_descriptions.py
└── test_*.py                      # Test scripts
```

## CSV Format

The tool expects a CSV file exported from Shopify with the following columns:
- `Handle` (required): Product handle/URL
- `Title` (optional): Product title
- `Body (HTML)` (optional): Current product description
- `Vendor` (optional): Product vendor
- `Product Category` (optional): Product category
- `Type` (optional): Product type

## Examples

### Test Scripts

The repository includes several test scripts for different scenarios:

- `test_openai_1_product.py`: Test with a single product
- `test_openai_3_products.py`: Test with 3 products
- `test_openai_5_products.py`: Test with 5 products
- `test_openai_sample.py`: Test with sample data

### Sample Usage

```python
# Test with a small sample
updater = OpenAIEnhancedUpdater("test_sample.csv", api_key)
updater.update_all_products()
updater.export_results("updated_sample.csv")
```

## Error Handling

The tool includes comprehensive error handling:

- **API Rate Limits**: Automatic retry with exponential backoff
- **Network Issues**: Retry logic for failed requests
- **Invalid Data**: Graceful handling of malformed CSV data
- **Progress Recovery**: Resume from where you left off

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions, please open an issue on GitHub. 