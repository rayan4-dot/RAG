from reportlab.pdfgen import canvas
import os

def create_sample_pdf():
    filepath = os.path.join(os.getcwd(), "OmniRAG_Sample.pdf")
    c = canvas.Canvas(filepath)
    
    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 800, "OmniRAG Test Document")
    
    # Body
    c.setFont("Helvetica", 12)
    c.drawString(50, 770, "1. The secret launch code for the Omni-Project is X-99-OMEGA.")
    c.drawString(50, 750, "2. The lead engineer of the backend is named Alex Mercer.")
    c.drawString(50, 730, "3. OmniRAG was officially deployed on March 25th, 2026.")
    c.drawString(50, 710, "4. The company handbook mandates 28 days of Paid Time Off (PTO) annually.")
    c.drawString(50, 690, "5. The internal server IP for staging is 192.168.4.55.")
    
    c.save()
    print(f"Successfully generated: {filepath}")

if __name__ == "__main__":
    create_sample_pdf()
