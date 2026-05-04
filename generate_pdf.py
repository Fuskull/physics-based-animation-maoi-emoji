"""Generate PDF report from markdown with screenshots"""
import os

print("=" * 60)
print("PDF Report Generator")
print("=" * 60)

# Check if markdown file exists
md_file = "docs/PHASE2_COMPLETE_REPORT.md"
if os.path.exists(md_file):
    print(f"✓ Found markdown file: {md_file}")
else:
    print(f"✗ Markdown file not found: {md_file}")
    exit(1)

print("\nTo generate PDF, you have several options:")
print()
print("Option 1: Using Pandoc (Recommended)")
print("-" * 60)
print("Install: https://pandoc.org/installing.html")
print("Command:")
print(f'  pandoc {md_file} -o docs/Phase2_Report.pdf --pdf-engine=xelatex')
print()

print("Option 2: Using Markdown to PDF (Python)")
print("-" * 60)
print("Install: pip install markdown-pdf")
print("Command:")
print(f'  markdown-pdf {md_file} -o docs/Phase2_Report.pdf')
print()

print("Option 3: Using grip + wkhtmltopdf")
print("-" * 60)
print("Install: pip install grip")
print("Install: https://wkhtmltopdf.org/downloads.html")
print("Commands:")
print(f'  grip {md_file} --export docs/Phase2_Report.html')
print('  wkhtmltopdf docs/Phase2_Report.html docs/Phase2_Report.pdf')
print()

print("Option 4: Online Converter")
print("-" * 60)
print("1. Open: https://www.markdowntopdf.com/")
print(f"2. Upload: {md_file}")
print("3. Download the generated PDF")
print()

print("Option 5: VS Code Extension")
print("-" * 60)
print("1. Install 'Markdown PDF' extension in VS Code")
print(f"2. Open: {md_file}")
print("3. Right-click → 'Markdown PDF: Export (pdf)'")
print()

print("=" * 60)
print("Note: To add screenshots to the PDF:")
print("1. Take screenshots of the running demos")
print("2. Save them in docs/screenshots/")
print("3. Add image references in the markdown:")
print("   ![Demo Screenshot](screenshots/demo.png)")
print("=" * 60)

# Try to detect available tools
print("\nChecking available tools...")

import subprocess

def check_command(cmd):
    try:
        subprocess.run([cmd, '--version'], capture_output=True, timeout=2)
        return True
    except:
        return False

if check_command('pandoc'):
    print("✓ Pandoc is installed")
    print("\nGenerating PDF with Pandoc...")
    try:
        result = subprocess.run([
            'pandoc', md_file,
            '-o', 'docs/Phase2_Report.pdf',
            '--pdf-engine=xelatex',
            '-V', 'geometry:margin=1in'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ PDF generated successfully: docs/Phase2_Report.pdf")
        else:
            print(f"✗ Error: {result.stderr}")
    except Exception as e:
        print(f"✗ Error: {e}")
else:
    print("✗ Pandoc not found")
    print("\nPlease install one of the tools above to generate PDF")
