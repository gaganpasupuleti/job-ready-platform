"""Clearly identified local PDF fixture. Not a production catalog."""

LOCAL_FIXTURE_KEY = "local-fixtures/jobready-library-fixture.pdf"


def fixture_pdf_bytes() -> bytes:
    page_one = b"BT /F1 18 Tf 36 220 Td (Local fixture page 1) Tj ET"
    page_two = b"BT /F1 18 Tf 36 220 Td (Local fixture page 2) Tj ET"
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Count 2 /Kids [3 0 R 4 0 R] >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 420 520] /Contents 5 0 R /Resources << /Font << /F1 6 0 R >> >> >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 420 520] /Contents 7 0 R /Resources << /Font << /F1 6 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n" % len(page_one) + page_one + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length %d >>\nstream\n" % len(page_two) + page_two + b"\nendstream",
    ]
    content = b"%PDF-1.4\n"
    offsets = [0]
    for number, body in enumerate(objects, start=1):
        offsets.append(len(content))
        content += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(content)
    content += f"xref\n0 {len(offsets)}\n".encode()
    content += b"0000000000 65535 f \n"
    for offset in offsets[1:]:
        content += f"{offset:010d} 00000 n \n".encode()
    content += (
        f"trailer << /Size {len(offsets)} /Root 1 0 R /ID [(jobready-fixture) (jobready-fixture)] >>\nstartxref\n{xref}\n%%EOF\n".encode()
    )
    return content
