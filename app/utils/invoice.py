from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os


PHARMACY_NAME = "Pharmacie Moustapha"
PHARMACY_PHONE = "+224 623 64 68 08"
PHARMACY_ADDRESS = "Kipé - Conakry - Guinée"


def generate_invoice(sale, items, filename):
    os.makedirs("invoices", exist_ok=True)
    filepath = f"invoices/{filename}"

    c = canvas.Canvas(filepath, pagesize=letter)
    

    y = 750
    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, y, PHARMACY_NAME)

    y -= 20
    c.setFont("Helvetica", 10)
    c.drawString(200, y, PHARMACY_ADDRESS)

    y -= 15
    c.drawString(200, y, PHARMACY_PHONE)

    y -= 40
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, f"Facture N°: {sale.id}")

    y -= 20
    c.setFont("Helvetica", 10)
   # c.drawString(50, y, f"Date: {sale.created_at}")
    c.drawString(50, y, f"Date: {sale.created_at.strftime('%d/%m/%Y %H:%M')}")

    y -= 40

    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "Produit")
    c.drawString(250, y, "Quantité")
    c.drawString(350, y, "Prix U")
    c.drawString(450, y, "Total")

    y -= 20
    c.setFont("Helvetica", 10)

    total = 0

    for item in items:
        product_name = item.product.name if item.product else f"ID {item.product_id}"

        c.drawString(50, y, product_name)
        c.drawString(260, y, str(item.quantity))
        c.drawString(350, y, str(item.unit_price))
        c.drawString(450, y, str(item.total_price))

        total += item.total_price
        y -= 20

    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(350, y, "TOTAL :")
    c.drawString(450, y, f"{total} GNF")

    c.save()

    return filepath
