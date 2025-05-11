import os
import argparse
from pdfminer.high_level import extract_text
from docx import Document

def convert_pdf_to_txt(pdf_path, txt_path):
    """Convert PDF file to text file"""
    try:
        text = extract_text(pdf_path)
        # Clean and preserve Arabic text
        text = text.replace('\n', ' ').strip()
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"Successfully converted {pdf_path} to {txt_path}")
    except Exception as e:
        print(f"Error converting {pdf_path}: {str(e)}")

def convert_docx_to_txt(docx_path, txt_path):
    """Convert DOCX file to text file"""
    try:
        doc = Document(docx_path)
        text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"Successfully converted {docx_path} to {txt_path}")
    except Exception as e:
        print(f"Error converting {docx_path}: {str(e)}")

def process_file(input_path, output_dir):
    """Process a single file based on its extension"""
    if not os.path.exists(input_path):
        print(f"File not found: {input_path}")
        return
    
    filename = os.path.basename(input_path)
    name, ext = os.path.splitext(filename)
    output_path = os.path.join(output_dir, f"{name}.txt")
    
    if ext.lower() == '.pdf':
        convert_pdf_to_txt(input_path, output_path)
    elif ext.lower() == '.docx':
        convert_docx_to_txt(input_path, output_path)

if __name__ == "__main__":
    # Example usage: python ConvertDocuments.py input.pdf output_dir
    parser = argparse.ArgumentParser(description="Convert PDF and DOCX files to text files")
    parser.add_argument("input", type=str, help="Input file path")
    parser.add_argument("output_dir", type=str, help="Output directory for text files")
    args = parser.parse_args()
    for root, dirs, files in os.walk(args.input):
        for file in files:
            input_path = os.path.join(root, file)
            process_file(input_path, args.output_dir)
