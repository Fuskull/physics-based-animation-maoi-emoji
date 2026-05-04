"""Generate PDF with embedded images using markdown2pdf or weasyprint"""
import os
import sys

print("=" * 70)
print("PDF Generator with Screenshots")
print("=" * 70)

md_file = "docs/PHASE2_COMPLETE_REPORT.md"
output_pdf = "docs/Phase2_Report_With_Screenshots.pdf"

# Check markdown exists
if not os.path.exists(md_file):
    print(f"✗ Error: {md_file} not found")
    sys.exit(1)

print(f"✓ Found: {md_file}")

# Check screenshots
screenshots = [
    "docs/screenshots/particles.png",
    "docs/screenshots/rope.png",
    "docs/screenshots/cloth.png",
    "docs/screenshots/pbd.png"
]

for img in screenshots:
    if os.path.exists(img):
        print(f"✓ Found: {img}")
    else:
        print(f"✗ Missing: {img}")

print("\n" + "=" * 70)
print("Attempting to generate PDF...")
print("=" * 70 + "\n")

# Try method 1: markdown-pdf
try:
    import markdown
    from weasyprint import HTML, CSS
    from markdown.extensions import tables, fenced_code
    
    print("Using WeasyPrint method...")
    
    # Read markdown
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Convert to HTML
    html_content = markdown.markdown(
        md_content,
        extensions=['tables', 'fenced_code', 'codehilite']
    )
    
    # Add CSS styling
    html_with_style = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                max-width: 800px;
                margin: 40px auto;
                padding: 20px;
            }}
            h1 {{
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
            }}
            h2 {{
                color: #34495e;
                border-bottom: 2px solid #95a5a6;
                padding-bottom: 5px;
                margin-top: 30px;
            }}
            h3 {{
                color: #7f8c8d;
            }}
            code {{
                background: #f4f4f4;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
            }}
            pre {{
                background: #2c3e50;
                color: #ecf0f1;
                padding: 15px;
                border-radius: 5px;
                overflow-x: auto;
            }}
            pre code {{
                background: none;
                color: #ecf0f1;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 20px 0;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
            }}
            th {{
                background-color: #3498db;
                color: white;
            }}
            tr:nth-child(even) {{
                background-color: #f2f2f2;
            }}
            img {{
                max-width: 100%;
                height: auto;
                display: block;
                margin: 20px auto;
                border: 2px solid #ddd;
                border-radius: 5px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            em {{
                display: block;
                text-align: center;
                color: #7f8c8d;
                font-size: 0.9em;
                margin-top: 10px;
            }}
            blockquote {{
                border-left: 4px solid #3498db;
                padding-left: 20px;
                margin-left: 0;
                color: #555;
            }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    # Generate PDF
    HTML(string=html_with_style, base_url='docs/').write_pdf(output_pdf)
    
    print(f"✓ SUCCESS! PDF generated: {output_pdf}")
    print(f"✓ File size: {os.path.getsize(output_pdf) / 1024:.1f} KB")
    
except ImportError as e:
    print(f"✗ WeasyPrint not installed")
    print(f"\nTo install:")
    print("  pip install weasyprint markdown")
    print("\nOr use alternative methods below...")
    print("\n" + "=" * 70)
    print("Alternative Methods:")
    print("=" * 70)
    
    print("\n1. Using Pandoc (Best for images):")
    print("-" * 70)
    print("Install: https://pandoc.org/installing.html")
    print("Command:")
    print(f"  pandoc {md_file} -o {output_pdf} --pdf-engine=xelatex")
    
    print("\n2. Using VS Code Extension:")
    print("-" * 70)
    print("1. Install 'Markdown PDF' extension")
    print(f"2. Open {md_file}")
    print("3. Right-click → 'Markdown PDF: Export (pdf)'")
    
    print("\n3. Using grip (GitHub style):")
    print("-" * 70)
    print("Install: pip install grip")
    print("Commands:")
    print(f"  grip {md_file} --export temp.html")
    print(f"  wkhtmltopdf temp.html {output_pdf}")
    
except Exception as e:
    print(f"✗ Error: {e}")
    print("\nTrying alternative method...")

print("\n" + "=" * 70)
