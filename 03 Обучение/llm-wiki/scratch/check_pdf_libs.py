import os

try:
    import pdfplumber
    print("pdfplumber found")
except ImportError:
    print("pdfplumber not found")

try:
    import PyPDF2
    print("PyPDF2 found")
except ImportError:
    print("PyPDF2 not found")
