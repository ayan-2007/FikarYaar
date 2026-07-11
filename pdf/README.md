Place your study notes here (PDF, DOCX, MD, TXT).

These files are the chatbot's default knowledge base. On first run the app will
read every supported file in this folder, split it into chunks, embed the
chunks with a local sentence-transformers model, and store them in Chroma.

Notes you upload later through the website live in `data/uploads/` and are
added to the same knowledge base.

Keep this folder empty of anything except actual notes — no ZIPs, images, etc.
