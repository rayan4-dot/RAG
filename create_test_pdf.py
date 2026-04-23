from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def create_enterprise_pdf(filename):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # Page 1: Internal Project Overview
    c.setFont("Helvetica-Bold", 24)
    c.drawString(100, height - 80, "OmniCorp: Project OmniRAG v2.0")
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, height - 120, "Internal Confidential - Level 5 Clearance")
    
    c.setFont("Helvetica", 12)
    c.drawString(100, height - 150, "Engineering Lead: Rayan")
    c.drawString(100, height - 165, "Department: Advanced AI & Retrieval Systems")
    
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, height - 200, "1. Executive Summary")
    c.setFont("Helvetica", 12)
    text = [
        "Project OmniRAG is the next generation of AI-driven document intelligence.",
        "It leverages Google Gemini 1.5 Flash for reasoning and ChromaDB for vector memory.",
        "The system is designed to provide instantaneous answers to complex enterprise queries.",
        "The current version (v2.0) introduces containerized deployment via Docker Compose."
    ]
    y = height - 220
    for line in text:
        c.drawString(100, y, line)
        y -= 20
        
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, y - 40, "2. Technical specifications")
    c.setFont("Helvetica", 12)
    y -= 60
    tech_specs = [
        "- Embedding Model: models/gemini-embedding-001",
        "- LLM Provider: Google Generative AI (Gemini Flash)",
        "- Database: ChromaDB (High-Performance Mode)",
        "- Interface: React + Vite + TypeScript (Glassmorphic UI)"
    ]
    for spec in tech_specs:
        c.drawString(100, y, spec)
        y -= 20
        
    # Page 2: Secrets and Launch Details
    c.showPage()
    c.setFont("Helvetica-Bold", 18)
    c.drawString(100, height - 80, "3. Sensitive Operational Data")
    
    c.setFont("Helvetica", 12)
    c.drawString(100, height - 120, "THE SECRET LAUNCH CODE FOR PROJECT OMNIRAG IS: X-99-OMEGA")
    c.drawString(100, height - 140, "Official Launch Window: November 2026")
    c.drawString(100, height - 160, "Primary Server Location: North Atlantic Underwater Data Center (NAUDC-1)")
    
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, height - 200, "4. Emergency Protocols")
    c.setFont("Helvetica", 12)
    protocols = [
        "In case of a hallucination event, initiated 'Safe-T' protocol immediately.",
        "The emergency override password is 'Alpha-7-Bravo'.",
        "Personnel responsible for database maintenance: Dr. Gemini."
    ]
    y = height - 220
    for p in protocols:
        c.drawString(100, y, p)
        y -= 20
        
    c.save()
    print(f"Proprietary enterprise PDF '{filename}' created successfully!")

if __name__ == "__main__":
    create_enterprise_pdf("OmniRAG_Sample.pdf")
