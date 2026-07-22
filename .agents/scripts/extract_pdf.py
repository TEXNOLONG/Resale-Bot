import fitz
import os

pdf_path = "attached_assets/Document_14_1784753571942.pdf"
out_dir = ".agents/outputs/pdf_images"
os.makedirs(out_dir, exist_ok=True)

doc = fitz.open(pdf_path)
print(f"Pages: {doc.page_count}")

# Render each page
for i, page in enumerate(doc):
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    out_path = f"{out_dir}/page_{i+1:02d}.png"
    pix.save(out_path)
    print(f"Saved page {i+1}: {out_path} ({page.rect.width:.0f}x{page.rect.height:.0f}pt)")

# Extract embedded images
print("\nEmbedded images:")
for i, page in enumerate(doc):
    images = page.get_images(full=True)
    for j, img in enumerate(images):
        xref = img[0]
        base_image = doc.extract_image(xref)
        ext = base_image["ext"]
        img_data = base_image["image"]
        out_path = f"{out_dir}/page{i+1:02d}_img{j+1:02d}.{ext}"
        with open(out_path, "wb") as f:
            f.write(img_data)
        print(f"  Page {i+1}, img {j+1}: {out_path} ({len(img_data)} bytes, {base_image['width']}x{base_image['height']})")
