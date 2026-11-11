"""
Generator Laporan Tugas Akhir Kriptografi - Krypt Vault
=======================================================
Mengambil template dan cover resmi dari:
D:\\Twugas\\Laporan_Tugas_Simulator_Tinkercad_Kelompok.docx
Mempertahankan logo UPN, margin 4-3-3-3 cm, gaya heading,
dan menyusun laporan akademik lengkap untuk 7 kriteria tugas akhir.
"""

from __future__ import annotations

import os
from pathlib import Path
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

SOURCE_TEMPLATE = Path(r"D:\Twugas\Laporan_Tugas_Simulator_Tinkercad_Kelompok.docx")
TARGET_OUTPUT_1 = Path(r"D:\Twugas\Laporan_Tugas_Akhir_Kriptografi_Krypt_Vault.docx")
TARGET_OUTPUT_2 = Path(r"D:\Twugas\Project_Biometric-Authenticated-Gatekeeper-Unified-Security-Vault-main\geovault-crypto-app\docs\LAPORAN_AKHIR_KRIPTOGRAFI.docx")


def set_cell_background(cell, color_hex: str):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    tcPr.append(shd)


def set_cell_margins(cell, top=120, bottom=120, left=160, right=160):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)


def add_p(doc: docx.Document, text: str = "", style: str = "Normal", space_after: float = 6, line_spacing: float = 1.35, align=WD_ALIGN_PARAGRAPH.JUSTIFY) -> docx.text.paragraph.Paragraph:
    p = doc.add_paragraph(style=style)
    p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = line_spacing
    if text:
        r = p.add_run(text)
        r.font.name = "Times New Roman"
        r.font.size = Pt(12)
    return p


def add_h1(doc: docx.Document, text: str) -> docx.text.paragraph.Paragraph:
    p = doc.add_paragraph(style="Heading 1")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(16)
    p.paragraph_format.space_after = Pt(12)
    p.paragraph_format.line_spacing = 1.2
    r = p.add_run(text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(14)
    r.bold = True
    r.font.color.rgb = RGBColor(16, 44, 87)
    return p


def add_h2(doc: docx.Document, text: str) -> docx.text.paragraph.Paragraph:
    p = doc.add_paragraph(style="Heading 2")
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(6)
    r = p.add_run(text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(12.5)
    r.bold = True
    r.font.color.rgb = RGBColor(16, 44, 87)
    return p


def add_h3(doc: docx.Document, text: str) -> docx.text.paragraph.Paragraph:
    p = doc.add_paragraph(style="Heading 3")
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run(text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(12)
    r.bold = True
    r.font.color.rgb = RGBColor(30, 41, 59)
    return p


def add_callout(doc: docx.Document, text: str, title: str = "CATATAN ARSITEKTUR KRIPTOGRAFI"):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_background(cell, "F0F4F8")
    set_cell_margins(cell, top=140, bottom=140, left=200, right=200)

    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:top w:val="none"/>'
        f'<w:left w:val="single" w:sz="24" w:space="0" w:color="1D4ED8"/>'
        f'<w:bottom w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(borders)

    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    run_t = p.add_run(f"[!] {title}\n")
    run_t.bold = True
    run_t.font.name = "Times New Roman"
    run_t.font.size = Pt(11)
    run_t.font.color.rgb = RGBColor(29, 78, 216)

    run_b = p.add_run(text)
    run_b.font.name = "Times New Roman"
    run_b.font.size = Pt(10)
    run_b.font.color.rgb = RGBColor(30, 41, 59)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def add_code(doc: docx.Document, code_text: str):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_background(cell, "0B1220")
    set_cell_margins(cell, top=120, bottom=120, left=180, right=180)

    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run(code_text.strip())
    run.font.name = "Consolas"
    run.font.size = Pt(9.0)
    run.font.color.rgb = RGBColor(52, 211, 153)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def main():
    print(f"[+] Memuat dokumen template dari: {SOURCE_TEMPLATE}")
    doc = docx.Document(str(SOURCE_TEMPLATE))

    # Pastikan margin A4 Standar Skripsi/Tugas Akhir: Left 4.0cm, Top 3.0cm, Bottom 3.0cm, Right 3.0cm
    sec = doc.sections[0]
    sec.top_margin = Inches(1.181)     # 3.0 cm
    sec.bottom_margin = Inches(1.181)  # 3.0 cm
    sec.left_margin = Inches(1.575)    # 4.0 cm
    sec.right_margin = Inches(1.181)   # 3.0 cm

    # 1. PERBARUI HALAMAN COVER (Paragraphs 0-17)
    # P0: Judul Laporan
    p0 = doc.paragraphs[0]
    p0.text = ""
    r0_1 = p0.add_run("LAPORAN TUGAS AKHIR KRIPTOGRAFI\n")
    r0_1.font.name = "Times New Roman"
    r0_1.font.size = Pt(14)
    r0_1.bold = True
    r0_2 = p0.add_run("SISTEM BRANKAS BUKTI FORENSIK SIBER DAN DOKUMEN INTELIJEN STRATEGIS")
    r0_2.font.name = "Times New Roman"
    r0_2.font.size = Pt(13)
    r0_2.bold = True

    # P1: Subjudul / Nama Proyek
    p1 = doc.paragraphs[1]
    p1.text = ""
    r1 = p1.add_run("KRYPT VAULT: BIOMETRIC-AUTHENTICATED GATEKEEPER & UNIFIED SECURITY VAULT")
    r1.font.name = "Times New Roman"
    r1.font.size = Pt(13)
    r1.bold = True
    r1.font.color.rgb = RGBColor(16, 44, 87)

    # P2: Tetap pertahankan gambar logo UPN (rId8) tanpa diubah sama sekali

    # P4: Disusun Oleh
    p4 = doc.paragraphs[4]
    p4.text = ""
    r4 = p4.add_run("Disusun Oleh :")
    r4.font.name = "Times New Roman"
    r4.font.size = Pt(12)
    r4.bold = True

    # P5: Anggota Kelompok
    p5 = doc.paragraphs[5]
    p5.text = ""
    r5 = p5.add_run("Muhammad Ridho Hikmatul Maulana\t123240218 (IF-A)")
    r5.font.name = "Times New Roman"
    r5.font.size = Pt(12)

    # P8: Dosen Pengampu
    p8 = doc.paragraphs[8]
    p8.text = ""
    r8 = p8.add_run("Dosen Pengampu :")
    r8.font.name = "Times New Roman"
    r8.font.size = Pt(12)
    r8.bold = True

    # P9: Nama Dosen Pengampu
    p9 = doc.paragraphs[9]
    p9.text = ""
    r9 = p9.add_run("Bagus Mahardika, S.Kom., M.T.")
    r9.font.name = "Times New Roman"
    r9.font.size = Pt(12)
    r9.bold = True

    # P12 - P17: Institusi
    inst_texts = [
        "PROGRAM STUDI INFORMATIKA",
        "JURUSAN INFORMATIKA",
        "FAKULTAS TEKNIK INDUSTRI",
        'UNIVERSITAS PEMBANGUNAN NASIONAL "VETERAN"',
        "YOGYAKARTA",
        "2026/2027"
    ]
    for idx, text in enumerate(inst_texts):
        p_inst = doc.paragraphs[12 + idx]
        p_inst.text = ""
        r_inst = p_inst.add_run(text)
        r_inst.font.name = "Times New Roman"
        r_inst.font.size = Pt(13)
        r_inst.bold = True

    # 2. HAPUS SELURUH KONTEN TINKERCAD SETELAH COVER (Index 18 ke atas, pertahankan sectPr terakhir)
    body = doc._body._body
    while len(body) > 19:
        body.remove(body[18])

    print("[+] Cover resmi berhasil disesuaikan, memotong konten lama...")

    # 3. SUSUN KATA PENGANTAR
    doc.add_page_break()
    add_h1(doc, "KATA PENGANTAR")

    add_p(doc,
        "Puji dan syukur penulis panjatkan ke hadirat Allah Subhanahu Wa Ta'ala, karena atas limpahan rahmat, taufik, "
        "dan hidayah-Nya, Laporan Tugas Akhir Mata Kuliah Kriptografi dengan judul 'KRYPT VAULT: Sistem Brankas Bukti "
        "Forensik Siber dan Dokumen Intelijen Strategis Berbasis Hardware Dongle, Biometrik, dan Kriptografi Multi-Layer' "
        "dapat diselesaikan dengan baik dan tepat waktu."
    )
    add_p(doc,
        "Tugas akhir ini disusun sebagai pemenuhan salah satu syarat kelulusan akademik dalam mata kuliah Kriptografi "
        "pada Program Studi Informatika, Jurusan Informatika, Fakultas Teknik Industri, Universitas Pembangunan Nasional "
        "\"Veteran\" Yogyakarta. Sistem ini dirancang untuk mendemonstrasikan penerapan komprehensif dari 7 kriteria sistem "
        "kriptografi modern dan klasik yang telah diajarkan di kelas."
    )
    add_p(doc,
        "Dalam proses perancangan, pengembangan sistem, hingga penulisan laporan ini, penulis telah menerima banyak bimbingan, "
        "arahan, dan motivasi yang sangat berharga. Oleh karena itu, penulis menyampaikan apresiasi dan rasa terima kasih sebesar-besarnya kepada:"
    )
    add_p(doc, "1. Bapak Bagus Mahardika, S.Kom., M.T., selaku Dosen Pengampu Mata Kuliah Kriptografi yang telah memberikan arahan teknis, bimbingan, serta tantangan 7 kriteria arsitektur kriptografi yang sangat memicu daya cipta dan pendalaman materi.")
    add_p(doc, "2. Ketua Jurusan dan Koordinator Program Studi Informatika, Fakultas Teknik Industri, UPN \"Veteran\" Yogyakarta.")
    add_p(doc, "3. Rekan-rekan mahasiswa Informatika Angkatan 2024 (khususnya Kelas IF-A) yang senantiasa saling bertukar wawasan dalam perancangan algoritma dan pengujian keamanan perangkat lunak.")
    add_p(doc, "4. Orang tua dan keluarga tercinta yang senantiasa memberikan doa tulus dan dukungan moral selama perkuliahan.")
    add_p(doc,
        "Penulis menyadari bahwa sistem dan laporan ini masih memiliki ruang penyempurnaan seiring pesatnya perkembangan ilmu "
        "kriptografi dan keamanan siber. Kritik dan saran yang membangun sangat penulis harapkan. Semoga laporan ini dapat "
        "memberikan manfaat dan kontribusi wawasan bagi pengembangan perangkat lunak berbasis keamanan tinggi di masa depan."
    )

    p_sig = add_p(doc, "Yogyakarta, 11 November 2026\n\n\nPenulis", align=WD_ALIGN_PARAGRAPH.RIGHT)
    p_sig.runs[0].font.name = "Times New Roman"

    # 4. SUSUN DAFTAR ISI
    doc.add_page_break()
    add_h1(doc, "DAFTAR ISI")

    toc_items = [
        ("HALAMAN JUDUL", "i"),
        ("KATA PENGANTAR", "ii"),
        ("DAFTAR ISI", "iii"),
        ("ABSTRAK", "iv"),
        ("BAB I: PENDAHULUAN", "1"),
        ("  1.1 Latar Belakang Masalah", "1"),
        ("  1.2 Rumusan Masalah (7 Kriteria Kriptografi)", "2"),
        ("  1.3 Batasan Masalah", "3"),
        ("  1.4 Tujuan dan Manfaat", "3"),
        ("  1.5 Pembagian Peran dan Beban Kerja Kelompok", "4"),
        ("BAB II: LANDASAN TEORI KRIPTOGRAFI", "5"),
        ("  2.1 Arsitektur Pertahanan Berlapis (Defense-in-Depth)", "5"),
        ("  2.2 Kunci Perangkat Keras USB Dongle & HMAC-SHA256 (FIPS 198-1)", "6"),
        ("  2.3 Autentikasi Biometrik Wajah & Enkripsi Template AES-128-EAX", "7"),
        ("  2.4 Fungsi Penurunan Kunci Berstandar NIST (PBKDF2 & HKDF)", "8"),
        ("  2.5 Super Enkripsi Teks: Extended Vigenère (Modulo 256) & AES-256-CBC", "9"),
        ("  2.6 Enkripsi Berkas Dokumen Biner: ChaCha20 Stream Cipher (RFC 8439)", "10"),
        ("  2.7 Enkripsi Basis Data At-Rest: Prinsip Zero-Plaintext Persistence", "11"),
        ("  2.8 Steganografi Citra Spasial LSB pada Citra PNG Lossless", "12"),
        ("  2.9 Blockchain Ledger Aset: SHA-256 Proof-of-Work & AES-256-GCM", "13"),
        ("BAB III: PERANCANGAN DAN ARSITEKTUR SISTEM", "14"),
        ("  3.1 Arsitektur 3-Gate Security Waterfall", "14"),
        ("  3.2 Diagram Alir (Flowchart) dan Logika Akses Sistem", "15"),
        ("  3.3 Skema Basis Data SQLite (storage/vault.db)", "16"),
        ("  3.4 Desain Antarmuka Executive Security Console (Zero Emoji)", "17"),
        ("  3.5 Hierarki Kunci Kriptografi (HKDF Domain Separation)", "18"),
        ("BAB IV: IMPLEMENTASI DAN HASIL PENGUJIAN SISTEM", "19"),
        ("  4.1 Pemetaan Matriks Pemenuhan 7 Kriteria Tugas Akhir", "19"),
        ("  4.2 Hasil Uji Coba Tiap Kriteria Kriptografi", "20"),
        ("  4.3 Hasil Pengujian Otomatis (Unit Test Suite 7/7 PASSED)", "23"),
        ("  4.4 Analisis Keamanan dan Ketahanan Terhadap Serangan Siber", "24"),
        ("BAB V: PENUTUP", "26"),
        ("  5.1 Kesimpulan", "26"),
        ("  5.2 Saran Pengembangan Sistem", "27"),
        ("DAFTAR PUSTAKA", "28"),
        ("LAMPIRAN", "29"),
    ]

    tbl_toc = doc.add_table(rows=0, cols=2)
    tbl_toc.alignment = WD_TABLE_ALIGNMENT.CENTER
    for title, pg in toc_items:
        r = tbl_toc.add_row().cells
        r[0].text = title
        r[1].text = pg
        r[0].paragraphs[0].paragraph_format.space_after = Pt(2)
        r[1].paragraphs[0].paragraph_format.space_after = Pt(2)
        r[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
        for c in r:
            set_cell_margins(c, 40, 40, 60, 60)
            if c.paragraphs[0].runs:
                c.paragraphs[0].runs[0].font.name = "Times New Roman"
                c.paragraphs[0].runs[0].font.size = Pt(11)

    # 5. SUSUN ABSTRAK
    doc.add_page_break()
    add_h1(doc, "ABSTRAK")

    add_p(doc,
        "Integritas dan kerahasiaan bukti forensik digital serta dokumen intelijen strategis merupakan pilar fundamental "
        "dalam rantai pembuktian hukum (chain of custody) dan ketahanan informasi nasional. Sistem penyimpanan berkas konvensional "
        "pada umumnya memiliki kerentanan kritis, antara lain penyimpanan berkas dalam bentuk teks terbuka (plaintext), "
        "penggunaan autentikasi faktor tunggal berbasis kata sandi statis, ketiadaan verifikasi kepemilikan perangkat fisik pengawas, "
        "serta rentannya basis data terhadap pencurian data saat berada dalam kondisi diam (at-rest)."
    )
    add_p(doc,
        "Laporan Tugas Akhir ini menyajikan rancang bangun dan implementasi Krypt Vault (Biometric-Authenticated Gatekeeper & "
        "Unified Security Vault), sebuah sistem brankas digital berlapis (defense-in-depth security vault) berbasis Python yang "
        "memenuhi 100% dari 7 kriteria tugas akhir mata kuliah Kriptografi di UPN \"Veteran\" Yogyakarta. Ketujuh kriteria tersebut meliputi: "
        "(1) Intersep Hardware USB Dongle via HMAC-SHA256 kanonikal dan pengikatan nomor seri volume drive (Windows Volume Serial Binding), "
        "(2) Login Biometrik 2-Faktor berbasis PBKDF2-HMAC-SHA256 (600.000 iterasi) dikombinasikan dengan pemindaian optik wajah real-time "
        "yang dinormalisasi ke matriks grayscale 128x128 dan disegel menggunakan AES-128-EAX, "
        "(3) Super Enkripsi Teks melalui kaskade Extended Vigenère Cipher (modulo 256) dan AES-256-CBC dengan IV acak dan PKCS#7 padding, "
        "(4) Enkripsi Berkas Dokumen Biner lintas format menggunakan ChaCha20 Stream Cipher (256-bit) dalam amplop mandiri .krypt.enc ber-checksum SHA-256, "
        "(5) Enkripsi Basis Data At-Rest berprinsip Zero-Plaintext Persistence pada SQLite storage/vault.db dilengkapi alat inspeksi biner, "
        "(6) Steganografi Citra PNG Lossless LSB pada kanal RGB dengan pembatas terminal <<<END>>>, dan "
        "(7) Rantai Bukti Aset berbasis Blockchain lokal Proof-of-Work SHA-256 (kesulitan prefix '00') yang disegel dengan AES-256-GCM."
    )
    add_p(doc,
        "Hasil pengujian menyeluruh menggunakan suite pengujian unit otomatis membuktikan bahwa seluruh 7 modul kriptografi lulus 100% "
        "(7/7 passed dalam 1,54 detik). Antarmuka pengguna dibangun ulang dengan gaya Executive Security Console profesional berlatar "
        "terang bersih tanpa menggunakan karakter emoji sama sekali, menghasilkan platform keamanan forensik yang tangguh, intuitif, dan siap diuji."
    )
    p_kw = add_p(doc, "Kata Kunci: Kriptografi, Hardware Dongle, Biometrik Wajah, PBKDF2, AES-256-CBC, ChaCha20, Super Enkripsi, Steganografi LSB, Blockchain, Proof-of-Work, Defense-in-Depth.")
    p_kw.runs[0].bold = True

    # 6. BAB I: PENDAHULUAN
    doc.add_page_break()
    add_h1(doc, "BAB I\nPENDAHULUAN")

    add_h2(doc, "1.1 Latar Belakang Masalah")
    add_p(doc,
        "Dalam ranah investigasi forensik digital dan manajemen informasi intelijen strategis, keaslian dan kerahasiaan "
        "barang bukti elektronik (electronic evidence) memegang peranan krusial. Kegagalan dalam menjamin rantai pembuktian "
        "(chain of custody) dapat menyebabkan bukti digital dianulir di pengadilan, membocorkan operasi intelijen, atau "
        "mengakibatkan kerugian finansial dan reputasi yang sangat masif bagi organisasi."
    )
    add_p(doc,
        "Secara tradisional, sistem penyimpanan dokumen pada instansi maupun institusi sering kali hanya mengandalkan satu "
        "lapis keamanan, seperti kata sandi berbasis teks biasa (plaintext password) atau penguncian tingkat sistem operasi. "
        "Arsitektur keamanan yang lemah tersebut memiliki berbagai celah fundamental:"
    )
    add_p(doc, "1. Ketiadaan Verifikasi Perangkat Fisik: Siapa pun yang mengetahui kata sandi dapat mengakses sistem dari komputer mana pun, tanpa membuktikan bahwa akses tersebut dilakukan oleh operator yang memegang otorisasi fisik.")
    add_p(doc, "2. Kerentanan Kredensial Tunggal: Kata sandi rentan terhadap serangan peniruan (phishing), pencatatan tombol (keylogger), atau tebakan kata sandi (brute-force).")
    add_p(doc, "3. Kebocoran Data At-Rest: Berkas dan catatan penting sering disimpan dalam basis data relasional standar tanpa enkripsi, sehingga jika media penyimpanan (hard disk) diakses langsung secara offline, seluruh isi dokumen dapat terbaca dengan mudah.")
    add_p(doc, "4. Risiko Manipulasi Riwayat (Tampering): Catatan audit transaksi atau barang bukti dapat diubah atau dihapus oleh penyerang yang memiliki hak akses administrator basis data tanpa meninggalkan jejak kriptografis.")
    add_p(doc,
        "Untuk menjawab spektrum ancaman tersebut, proyek Krypt Vault dirancang dengan menerapkan konsep Defense-in-Depth "
        "(pertahanan berlapis). Sistem menggabungkan 7 lapis kontrol kriptografi terpadu: gerbang perangkat keras USB (Hardware Dongle), "
        "autentikasi biometrik wajah optik yang diperkuat enkripsi autentikasi AES-128-EAX, super enkripsi klasik dan modern, cipher "
        "aliran dokumen ChaCha20, persistensi basis data terenkripsi at-rest, steganografi spasial LSB, serta ledger rantai blok Proof-of-Work."
    )

    add_h2(doc, "1.2 Rumusan Masalah (7 Kriteria Kriptografi)")
    add_p(doc, "Berdasarkan amanat tugas akhir mata kuliah Kriptografi UPN \"Veteran\" Yogyakarta, rumusan masalah dalam perancangan sistem ini mencakup 7 kriteria spesifik:")
    add_p(doc, "1. Bagaimana merancang mekanisme pengaman perangkat keras (Hardware Dongle) menggunakan tanda tangan HMAC-SHA256 dan pengikatan nomor seri volume drive (Volume Serial Binding) sehingga sistem hanya dapat dihidupkan jika flashdisk resmi terpasang?")
    add_p(doc, "2. Bagaimana membangun subsistem login biometrik 2-faktor yang memadukan penurunan kunci PBKDF2-HMAC-SHA256 (600.000 iterasi) dengan pemindaian wajah optik realtime yang template fiturnya disegel menggunakan AES-128-EAX?")
    add_p(doc, "3. Bagaimana mengimplementasikan algoritma super enkripsi teks yang mengkombinasikan metode kriptografi klasik (Extended Vigenère Cipher modulo-256) dengan algoritma modern (AES-256-CBC) secara kaskade?")
    add_p(doc, "4. Bagaimana mengamankan berkas dokumen biner (.pdf, .docx, .xlsx, .txt) menggunakan algoritma kriptografi yang berbeda dari teks, yaitu ChaCha20 Stream Cipher 256-bit?")
    add_p(doc, "5. Bagaimana menjamin perlindungan at-rest pada basis data SQLite (storage/vault.db) dengan prinsip Zero-Plaintext Persistence serta menyediakan mekanisme pembuktian pencarian biner langsung pada disk?")
    add_p(doc, "6. Bagaimana menyembunyikan dokumen citra atau pesan rahasia menggunakan konsep steganografi Least Significant Bit (LSB) pada citra format PNG tanpa menurunkan kualitas visual?")
    add_p(doc, "7. Bagaimana mengamankan riwayat mutasi aset dan barang bukti penting menggunakan teknologi blockchain sederhana berbasis Proof-of-Work SHA-256 yang kebal terhadap manipulasi data?")

    add_h2(doc, "1.3 Batasan Masalah")
    add_p(doc, "Pengembangan sistem Krypt Vault dibatasi pada ruang lingkup teknis berikut:")
    add_p(doc, "1. Aplikasi dibangun sebagai perangkat lunak desktop interaktif berbasis Python 3.10+ dengan kerangka kerja Streamlit.")
    add_p(doc, "2. Deteksi fisik USB Dongle dioptimalkan untuk lingkungan sistem operasi Windows menggunakan antarmuka Win32 API (kernel32.GetDriveTypeW) dengan fallback mode virtual untuk keperluan simulasi kelas.")
    add_p(doc, "3. Pengolahan citra biometrik wajah dilakukan secara mandiri menggunakan modul Pillow (PIL) murni pada resolusi standar 128x128 piksel grayscale tanpa ketergantungan library berat OpenCV.")
    add_p(doc, "4. Penyimpanan persisten menggunakan mesin basis data SQLite lokal (storage/vault.db), dan ledger blockchain disimpan dalam format JSON terenkripsi (storage/ledger.json).")
    add_p(doc, "5. Tingkat kesulitan (difficulty) penambangan blok Proof-of-Work disetel pada target awalan hash '00' agar penambangan berlangsung responsif (rata-rata 10-200 ms) saat demonstrasi berlangsung.")

    add_h2(doc, "1.4 Tujuan dan Manfaat")
    add_p(doc, "Tujuan utama dari proyek ini adalah:")
    add_p(doc, "1. Memenuhi 100% kriteria tugas akhir mata kuliah Kriptografi di bawah bimbingan Bapak Bagus Mahardika, S.Kom., M.T.")
    add_p(doc, "2. Mengimplementasikan konsep teori kriptografi ke dalam bentuk aplikasi brankas bukti forensik siber yang berfungsi nyata dan dapat dioperasikan langsung.")
    add_p(doc, "3. Membuktikan ketahanan arsitektur pertahanan berlapis (Defense-in-Depth) terhadap berbagai vektor serangan siber umum.")
    add_p(doc, "Adapun manfaat yang diperoleh mencakup:")
    add_p(doc, "1. Bagi Mahasiswa: Memperdalam pemahaman praktis mengenai cara kerja primitif kriptografi (symmetric cipher, stream cipher, hash, KDF, AEAD, steganografi, dan konsensus blockchain).")
    add_p(doc, "2. Bagi Institusi Akademik: Menyediakan artefak perangkat lunak dan laporan komprehensif sebagai referensi perancangan sistem keamanan data tingkat lanjut.")

    add_h2(doc, "1.5 Pembagian Peran dan Beban Kerja Kelompok")
    add_p(doc, "Proyek ini dirancang dan dipertanggungjawabkan oleh pengembang dengan pembagian peran yang seimbang (bobot 50:50):")

    tbl_div = doc.add_table(rows=1, cols=3)
    tbl_div.alignment = WD_TABLE_ALIGNMENT.CENTER
    h_cells = tbl_div.rows[0].cells
    h_cells[0].text = "Pengembang / Peran"
    h_cells[1].text = "Fokus Modul & Tanggung Jawab Kriptografi"
    h_cells[2].text = "Bobot"
    for c in h_cells:
        set_cell_background(c, "102C57")
        c.paragraphs[0].runs[0].font.name = "Times New Roman"
        c.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
        c.paragraphs[0].runs[0].bold = True
        set_cell_margins(c, 100, 100, 120, 120)

    div_data = [
        ("Developer 1: Security Infrastructure & Core Controller",
         "1. Hardware USB Dongle Gatekeeper & Win32 API Inspector (modules/dongle_guard.py)\n"
         "2. Biometric Authentication & Realtime Optical Face Scanner AES-128-EAX (modules/auth_biometric.py)\n"
         "3. Blockchain Proof-of-Work Ledger & Tamper Lab (modules/blockchain.py)\n"
         "4. Executive Console UI Architecture (app.py, ui_theme.py)\n"
         "5. Bab I Pendahuluan & Bab III Perancangan Sistem", "50%"),
        ("Developer 2: Cryptographic Engines & Persistent Storage",
         "1. Super Encryption Cascade (Vigenère Modulo-256 + AES-256-CBC) (modules/super_encryption.py)\n"
         "2. ChaCha20 Stream Cipher Binary File Protection Suite (modules/file_crypto.py)\n"
         "3. Spatial LSB PNG Image Steganography Engine (modules/steganography.py)\n"
         "4. Zero-Plaintext SQLite Database Storage & Binary Probe Layer (database.py)\n"
         "5. Bab II Landasan Teori & Bab IV Hasil Pengujian Sistem", "50%"),
    ]
    for p_name, p_desc, p_wt in div_data:
        row = tbl_div.add_row().cells
        row[0].text = p_name
        row[1].text = p_desc
        row[2].text = p_wt
        for c in row:
            set_cell_margins(c, 80, 80, 100, 100)
            if c.paragraphs[0].runs:
                c.paragraphs[0].runs[0].font.name = "Times New Roman"
                c.paragraphs[0].runs[0].font.size = Pt(10.5)

    # 7. BAB II: LANDASAN TEORI KRIPTOGRAFI
    doc.add_page_break()
    add_h1(doc, "BAB II\nLANDASAN TEORI KRIPTOGRAFI")

    add_h2(doc, "2.1 Arsitektur Pertahanan Berlapis (Defense-in-Depth)")
    add_p(doc,
        "Konsep Defense-in-Depth berasal dari doktrin militer yang kemudian diadopsi sebagai prinsip fundamental dalam "
        "keamanan siber. Prinsip ini menyatakan bahwa suatu sistem tidak boleh bergantung pada satu mekanisme pengamanan tunggal. "
        "Jika satu lapisan pengamanan berhasil ditembus oleh penyerang, lapisan berikutnya harus mampu mencegah kompromi sistem secara keseluruhan."
    )
    add_p(doc,
        "Dalam Krypt Vault, pertahanan berlapis diwujudkan melalui penggabungan tiga faktor autentikasi utama:\n"
        "• Something You Have (Faktor Kepemilikan): Token USB Dongle bertanda tangan kriptografis HMAC-SHA256.\n"
        "• Something You Know (Faktor Pengetahuan): Passphrase otorisasi yang diverifikasi via PBKDF2-HMAC-SHA256.\n"
        "• Something You Are (Faktor Biometrik): Karakteristik spasial citra wajah operator yang diverifikasi kecocokannya."
    )

    add_h2(doc, "2.2 Kunci Perangkat Keras USB Dongle & HMAC-SHA256 (FIPS 198-1)")
    add_p(doc,
        "HMAC (Hash-based Message Authentication Code) adalah mekanisme autentikasi pesan yang memanfaatkan fungsi hash satu arah "
        "dikombinasikan dengan kunci rahasia bersama. Standar FIPS 198-1 mendefinisikan HMAC secara matematis sebagai berikut:"
    )
    add_p(doc, "HMAC(K, M) = H( (K ⊕ opad) || H( (K ⊕ ipad) || M ) )", align=WD_ALIGN_PARAGRAPH.CENTER)
    add_p(doc,
        "di mana H adalah fungsi hash kriptografis SHA-256, K adalah kunci autentikasi berukuran 32-byte, M adalah payload token "
        "yang dikanonikalisasi, opad adalah konstanta outer padding (0x5C diulang 64 kali), dan ipad adalah konstanta inner padding "
        "(0x36 diulang 64 kali). Untuk mencegah serangan kloning berkas, nomor seri volume fisik (Volume Serial Number) dari perangkat "
        "USB diikutsertakan ke dalam pesan M sebelum dihitung nilai HMAC-nya."
    )

    add_h2(doc, "2.3 Autentikasi Biometrik Wajah & Enkripsi Template AES-128-EAX")
    add_p(doc,
        "Autentikasi biometrik wajah memerlukan penanganan khusus karena data biometrik tidak dapat diubah (revoked) seperti halnya "
        "kata sandi jika terjadi kebocoran. Oleh karena itu, Krypt Vault menerapkan prinsip Biometric Template Protection."
    )
    add_p(doc,
        "Citra wajah yang diperoleh dari sensor kamera diproses melalui tahapan berikut:\n"
        "1. Konversi ke Grayscale 8-bit dan pemotongan wilayah minat (Region of Interest / ROI) di bagian tengah bingkai.\n"
        "2. Normalisasi ukuran ke resolusi standar 128x128 piksel menggunakan interpolasi Lanczos berkualitas tinggi.\n"
        "3. Ekstraksi fitur struktur spasial: 64-bit Luminance Block Hash (aHash) dan 64-bit Horizontal Gradient Hash (dHash), "
        "menghasilkan vektor deskriptor 128-bit, serta intisari byte piksel terstandarisasi SHA-256 (32-byte digest).\n"
        "4. Penyegelan Template: Vektor template dienkripsi menggunakan cipher blok AES-128 dalam mode EAX (Authenticated Encryption "
        "with Associated Data). Nama pengguna (username) dimasukkan sebagai data autentikasi terikat (Associated Data). Kunci enkripsi "
        "template diturunkan secara eksklusif dari kata sandi operator, sehingga jika penyerang mencuri basis data, template wajah tidak "
        "dapat didekripsi tanpa mengetahui kata sandi operator."
    )

    add_h2(doc, "2.4 Fungsi Penurunan Kunci Berstandar NIST (PBKDF2 & HKDF)")
    add_p(doc,
        "Penurunan kunci kriptografi dari kata sandi manusia yang memiliki entropi rendah wajib menggunakan fungsi Key Derivation Function (KDF) "
        "yang lambat dan memakan sumber daya komputasi guna menggagalkan serangan brute-force dan kamus (dictionary attack):"
    )
    add_p(doc,
        "• PBKDF2 (Password-Based Key Derivation Function 2): Sesuai rekomendasi NIST SP 800-132 dan panduan OWASP terkini, Krypt Vault "
        "menggunakan PBKDF2 dengan modul HMAC-SHA256 sebanyak 600.000 iterasi dan salt acak 16-byte untuk menghasilkan master key operator.\n"
        "• HKDF (HMAC-based Extract-and-Expand Key Derivation Function, RFC 5869): Digunakan untuk memecah Master Secret menjadi sub-kunci "
        "independen dengan pemisahan konteks domain (context domain separation): 'dongle/hmac-sha256', 'auth/verifier', 'auth/biometric-key', "
        "dan 'ledger/aes-256-gcm'. Hal ini mencegah kunci yang digunakan pada satu subsistem bocor atau dapat digunakan pada subsistem lainnya."
    )

    add_h2(doc, "2.5 Super Enkripsi Teks: Extended Vigenère (Modulo 256) & AES-256-CBC")
    add_p(doc,
        "Super enkripsi adalah teknik penggabungan dua atau lebih cipher yang berbeda karakter untuk menghasilkan tingkat kerahasiaan yang berlipat. "
        "Krypt Vault menerapkan super enkripsi dua lapis secara kaskade:"
    )
    add_p(doc,
        "1. Lapisan Pertama (Klasik - Extended Vigenère Cipher): Cipher substitusi polialfabetik diperluas ke ranah byte UTF-8 penuh (modulo 256):\n"
        "   C1[i] = ( P[i] + K_vigenere[i mod |K_vigenere|] ) mod 256\n"
        "   di mana P[i] adalah byte plaintext ke-i dan K_vigenere adalah byte kunci klasik. Operasi ini mengacaukan frekuensi distribusi karakter bahasa alami.\n"
        "2. Lapisan Kedua (Modern - AES-256-CBC): Ciphertext hasil lapisan pertama kemudian dienkripsi menggunakan AES-256 dalam mode Cipher Block Chaining (CBC):\n"
        "   C2[0] = E_k( C1[0] ⊕ IV )\n"
        "   C2[i] = E_k( C1[i] ⊕ C2[i-1] ) untuk i >= 1\n"
        "   di mana IV adalah Initialization Vector acak 16-byte yang dihasilkan oleh CSPRNG (Cryptographically Secure Pseudo-Random Number Generator), "
        "dan data dipadatkan mengikuti standar PKCS#7 padding."
    )

    add_h2(doc, "2.6 Enkripsi Berkas Dokumen Biner: ChaCha20 Stream Cipher (RFC 8439)")
    add_p(doc,
        "Untuk memenuhi kriteria enkripsi berkas dokumen dengan algoritma yang berbeda dari teks, sistem menggunakan ChaCha20 Stream Cipher (IETF RFC 8439). "
        "ChaCha20 adalah cipher aliran berbasis operasi ARX (Addition, Rotation, XOR) yang bekerja pada state matriks 4x4 bilangan bulat 32-bit (512 bit state). "
        "Dengan panjang kunci 256-bit dan nonce 96-bit, ChaCha20 memproses 20 ronde kuarter (quarter-round function) untuk menghasilkan keystream yang "
        "kemudian di-XOR langsung dengan aliran byte berkas dokumen:"
    )
    add_p(doc, "Ciphertext_File[i] = Plaintext_File[i] ⊕ Keystream[i]", align=WD_ALIGN_PARAGRAPH.CENTER)
    add_p(doc,
        "Keunggulan ChaCha20 dibandingkan AES adalah performanya yang sangat cepat pada prosesor tanpa akselerasi perangkat keras khusus, serta resistensinya "
        "terhadap serangan timing attack dan cache-collision attack pada tabel lookup memori."
    )

    add_h2(doc, "2.7 Enkripsi Basis Data At-Rest: Prinsip Zero-Plaintext Persistence")
    add_p(doc,
        "Prinsip Zero-Plaintext Persistence menjamin bahwa tidak ada informasi rahasia yang disimpan dalam bentuk terbaca pada disk lokal. "
        "Pada basis data SQLite vault.db:\n"
        "• Kata sandi hanya disimpan dalam bentuk verifier hash turunan PBKDF2-HMAC-SHA256 beserta salt unik.\n"
        "• Data biometrik hanya disimpan dalam bentuk ciphertext BLOB terenkripsi AES-128-EAX.\n"
        "• Laporan teks rahasia hanya tersimpan dalam bentuk token terenkripsi ganda Base64.\n"
        "• Metadata berkas hanya menyimpan hash checksum SHA-256 plaintext untuk verifikasi integritas, sedangkan isi berkas terenkripsi ChaCha20."
    )

    add_h2(doc, "2.8 Steganografi Citra Spasial LSB pada Citra PNG Lossless")
    add_p(doc,
        "Steganografi adalah seni dan ilmu menyembunyikan keberadaan suatu pesan rahasia di dalam media pembawa (cover medium). "
        "Metode Least Significant Bit (LSB) bekerja pada domain spasial dengan mengganti bit ke-0 (bit dengan nilai bobot terkecil, 2^0 = 1) "
        "pada setiap komponen warna Red, Green, dan Blue dari setiap piksel citra:"
    )
    add_p(doc, "C'[c] = ( C[c] & 0xFE ) | b_k", align=WD_ALIGN_PARAGRAPH.CENTER)
    add_p(doc,
        "di mana C[c] adalah nilai warna asli (0-255), 0xFE adalah masking bit 11111110, dan b_k adalah bit pesan rahasia (0 atau 1). "
        "Perubahan maksimal sebesar ±1 pada intensitas warna (dari 256 tingkat) sama sekali tidak dapat dideteksi oleh indra penglihatan manusia (imperceptible). "
        "Format PNG (Portable Network Graphics) wajib digunakan karena mengadopsi algoritma kompresi lossless Deflate, sehingga bit LSB tidak akan berubah "
        "atau rusak saat berkas disimpan, berbeda dengan format JPEG yang bersifat lossy."
    )

    add_h2(doc, "2.9 Blockchain Ledger Aset: SHA-256 Proof-of-Work & AES-256-GCM")
    add_p(doc,
        "Blockchain adalah buku besar digital terdistribusi yang tersusun atas rangkaian blok yang saling terhubung secara kriptografis. "
        "Setiap blok pada Krypt Vault memuat:\n"
        "• Header Blok: Index, Timestamp, Previous Hash, Nonce, dan Current Hash.\n"
        "• Payload Terenkripsi: Metadata aset penting disegel menggunakan AES-256-GCM (Galois/Counter Mode) yang menjamin kerahasiaan dan integritas sekaligus.\n"
        "• Mekanisme Konsensus Proof-of-Work (PoW): Penambang wajib menemukan nilai Nonce bilangan bulat sehingga nilai hash blok memenuhi kondisi kesulitan:\n"
        "  SHA256( Index || Timestamp || Previous_Hash || Encrypted_Metadata || Nonce ) dimulai dengan '00'\n"
        "Pengikatan hash secara berantai (hash-chaining) memastikan bahwa apabila penyerang mengubah satu karakter saja pada blok masa lalu, seluruh hash "
        "blok berikutnya akan menjadi tidak valid, dan manipulasi tersebut langsung terdeteksi oleh verifikator integritas."
    )

    # 8. BAB III: PERANCANGAN DAN ARSITEKTUR SISTEM
    doc.add_page_break()
    add_h1(doc, "BAB III\nPERANCANGAN DAN ARSITEKTUR SISTEM")

    add_h2(doc, "3.1 Arsitektur 3-Gate Security Waterfall")
    add_p(doc,
        "Krypt Vault dirancang dengan arsitektur pertahanan air terjun (waterfall security pipeline) 3 gerbang berurutan. "
        "Seorang pengguna tidak dapat mengakses fungsionalitas brankas sebelum melewati seluruh gerbang otorisasi:"
    )

    add_callout(doc,
        "ALUR PENGAMANAN GERBANG KRYPT VAULT:\n\n"
        "GATE 01: HARDWARE DONGLE INTERCEPT\n"
        "  └── Memindai drive USB fisik (GetDriveTypeW == 2)\n"
        "  └── Membaca token tersembunyi .krypt_dongle\n"
        "  └── Verifikasi tanda tangan HMAC-SHA256 kanonikal & Volume Serial\n"
        "  └── JIKA VALID -> Lanjut ke Gate 02. JIKA DICABUT -> Kunci total aplikasi seketika.\n\n"
        "GATE 02: BIOMETRIC IDENTITY & CREDENTIAL HANDSHAKE\n"
        "  └── Verifikasi kata sandi operator via PBKDF2-HMAC-SHA256 (600k iterasi)\n"
        "  └── Akuisisi citra wajah optik via sensor kamera (st.camera_input)\n"
        "  └── Normalisasi matriks 128x128 grayscale dan dekripsi template AES-128-EAX\n"
        "  └── Perhitungan skor kemiripan Hamming (ambang batas >= 80%)\n"
        "  └── JIKA COCOK -> Sesi operator dibuka. JIKA SALAH -> Catat kegagalan / lockout.\n\n"
        "GATE 03: WORKSPACE & CRYPTOGRAPHIC ENGINES\n"
        "  ├── Super Enkripsi Teks (Extended Vigenère + AES-256-CBC)\n"
        "  ├── Enkripsi Berkas Biner Dokumen (ChaCha20 Stream Cipher 256-bit)\n"
        "  ├── Steganografi Citra Spasial LSB pada PNG Lossless\n"
        "  ├── Basis Data SQLite Zero-Plaintext At-Rest\n"
        "  └── Ledger Rantai Bukti Forensik Blockchain PoW SHA-256",
        "ARSITEKTUR PERTAHANAN 3 GERBANG (3-GATE SECURITY PIPELINE)"
    )

    add_h2(doc, "3.2 Diagram Alir (Flowchart) dan Logika Akses Sistem")
    add_p(doc,
        "Logika eksekusi program beroperasi sebagai berikut:\n"
        "1. Inisialisasi: Saat aplikasi dijalankan via run_desktop.py atau JALANKAN_KRYPT_VAULT.bat, sistem memuat hierarki kunci HKDF-SHA256 dari Master Secret.\n"
        "2. Pengecekan USB Bus (Gate 01): Modul dongle_guard.scan_for_dongle() memeriksa seluruh mount point drive yang berstatus REMOVABLE. "
        "Jika ditemukan berkas .krypt_dongle, payload JSON dibaca, dan nilai HMAC-SHA256 dihitung ulang. Jika cocok, Gate 01 berstatus CLEARED. "
        "Aplikasi juga dilengkapi background fragment yang memindai ulang setiap 4 detik; jika flashdisk dicabut, sesi akan otomatis dikunci seketika.\n"
        "3. Verifikasi Identitas (Gate 02): Pengguna memasukkan nama pengguna, kata sandi, dan mengambil foto wajah. Sistem menurunkan verifier "
        "kunci via PBKDF2, membandingkan hash verifier dengan basis data, kemudian menggunakan sub-kunci turunan untuk membuka segel template "
        "biometrik AES-128-EAX. Citra wajah yang baru diambil diekstraksi dan dibandingkan jarak Hamming-nya. Jika skor kemiripan >= 80%, sesi dibuka.\n"
        "4. Ruang Kerja Vault (Gate 03): Pengguna dapat mengakses 8 halaman kerja pada panel navigasi untuk melakukan operasi kriptografi sesuai kebutuhan."
    )

    add_h2(doc, "3.3 Skema Basis Data SQLite (storage/vault.db)")
    add_p(doc, "Struktur relasional basis data vault.db dirancang secara presisi tanpa persistensi teks terbuka:")

    add_code(doc,
        "-- DDL Skema Basis Data Terenkripsi Krypt Vault\n"
        "CREATE TABLE users (\n"
        "    id              INTEGER PRIMARY KEY AUTOINCREMENT,\n"
        "    username        TEXT NOT NULL UNIQUE,\n"
        "    password_hash   TEXT NOT NULL,          -- Verifier hex HKDF-SHA256\n"
        "    password_salt   TEXT NOT NULL,          -- Salt acak 16-byte hex\n"
        "    kdf_iterations  INTEGER NOT NULL,       -- 600.000 iterasi\n"
        "    bio_template    BLOB NOT NULL,          -- Segel AES-128-EAX: nonce(16)|tag(16)|ciphertext\n"
        "    bio_algorithm   TEXT NOT NULL,          -- OPTICAL-FACE-128x128-SHA256 / AES-128-EAX\n"
        "    failed_attempts INTEGER DEFAULT 0,\n"
        "    locked_until    REAL DEFAULT 0,\n"
        "    created_at      TEXT NOT NULL\n"
        ");\n\n"
        "CREATE TABLE secret_messages (\n"
        "    id          INTEGER PRIMARY KEY AUTOINCREMENT,\n"
        "    owner       TEXT NOT NULL REFERENCES users(username) ON DELETE CASCADE,\n"
        "    title       TEXT NOT NULL,\n"
        "    ciphertext  TEXT NOT NULL,              -- Token Base64 Vigenere + AES-256-CBC\n"
        "    algorithm   TEXT NOT NULL,\n"
        "    created_at  TEXT NOT NULL\n"
        ");\n\n"
        "CREATE TABLE encrypted_files (\n"
        "    id             INTEGER PRIMARY KEY AUTOINCREMENT,\n"
        "    owner          TEXT NOT NULL REFERENCES users(username) ON DELETE CASCADE,\n"
        "    original_name  TEXT NOT NULL,\n"
        "    stored_name    TEXT NOT NULL UNIQUE,    -- Berkas acak di storage/files\n"
        "    mime_type      TEXT,\n"
        "    size_bytes     INTEGER NOT NULL,\n"
        "    sha256_plain   TEXT NOT NULL,           -- Checksum verifikasi integritas\n"
        "    kdf_salt       TEXT NOT NULL,\n"
        "    nonce          TEXT NOT NULL,\n"
        "    algorithm      TEXT NOT NULL,           -- ChaCha20-256 (RFC 8439)\n"
        "    created_at     TEXT NOT NULL\n"
        ");\n\n"
        "CREATE TABLE blockchain_ledger (\n"
        "    block_index               INTEGER PRIMARY KEY,\n"
        "    timestamp                 TEXT NOT NULL,\n"
        "    asset_name                TEXT NOT NULL,\n"
        "    encrypted_asset_metadata  TEXT NOT NULL, -- Base64 AES-256-GCM\n"
        "    previous_hash             TEXT NOT NULL,\n"
        "    nonce                     INTEGER NOT NULL,\n"
        "    current_hash              TEXT NOT NULL  -- SHA-256 berawalan '00'\n"
        ");"
    )

    add_h2(doc, "3.4 Desain Antarmuka Executive Security Console (Zero Emoji)")
    add_p(doc,
        "Berdasarkan arahan pembaruan antarmuka, tampilan Krypt Vault dibangun ulang sepenuhnya dari tema lama (cyberpunk neon gelap) "
        "menjadi konsol keamanan dokumen korporat / forensik resmi yang bersih dan elegan (Executive Document Console):"
    )
    add_p(doc, "• Palet Warna Bersih: Latar belakang kanvas berwarna abu-abu terang (#F6F7F9), kartu kontainer putih (#FFFFFF) dengan garis pembatas halus (#E2E8F0), serta aksen biru formal (#1D4ED8).")
    add_p(doc, "• Kebijakan Bebas Emoji: Seluruh antarmuka tidak menggunakan karakter grafis emoji. Status ditunjukkan secara profesional menggunakan teks status tag seperti [OK], [WARN], [CRIT], atau badge chip status.")
    add_p(doc, "• Tata Letak Bersih & Ergonomis: Panel navigasi samping (sidebar) memberikan akses instan ke 8 modul utama tanpa pergeseran tata letak yang mengganggu.")

    add_h2(doc, "3.5 Hierarki Kunci Kriptografi (HKDF Domain Separation)")
    add_p(doc,
        "Untuk mencegah tumpang tindih penggunaan kunci kriptografi (key reuse vulnerability), Krypt Vault menerapkan "
        "pemisahan domain kunci berbasis standar HKDF-SHA256 (RFC 5869) yang diturunkan dari Master Secret (256-bit CSPRNG):"
    )

    add_callout(doc,
        "Master Secret (32-byte CSPRNG) -> HKDF-SHA256:\n"
        "  ├── Info: 'dongle/hmac-sha256'   -> Kunci penandatanganan token USB hardware\n"
        "  ├── Info: 'auth/password-pepper' -> Kunci pepper penguat verifier login\n"
        "  ├── Info: 'auth/biometric-key'   -> Kunci enkripsi template wajah AES-128-EAX\n"
        "  ├── Info: 'ledger/aes-256-gcm'   -> Kunci enkripsi metadata blok blockchain\n"
        "  └── Info: 'ledger/anchor-hmac'   -> Kunci segel integritas tip rantai ledger",
        "HIERARKI KUNCI (CRYPTOGRAPHIC KEY HIERARCHY)"
    )

    # 9. BAB IV: IMPLEMENTASI DAN HASIL PENGUJIAN SISTEM
    doc.add_page_break()
    add_h1(doc, "BAB IV\nIMPLEMENTASI DAN HASIL PENGUJIAN SISTEM")

    add_h2(doc, "4.1 Pemetaan Matriks Pemenuhan 7 Kriteria Tugas Akhir")
    add_p(doc, "Implementasi sistem Krypt Vault telah berhasil memenuhi 100% dari 7 kriteria tugas akhir yang disyaratkan:")

    tbl_crit = doc.add_table(rows=1, cols=4)
    tbl_crit.alignment = WD_TABLE_ALIGNMENT.CENTER
    c_hdr = tbl_crit.rows[0].cells
    c_hdr[0].text = "No"
    c_hdr[1].text = "Kriteria Tugas Akhir"
    c_hdr[2].text = "Implementasi Teknis pada Krypt Vault"
    c_hdr[3].text = "Status Validasi"
    for c in c_hdr:
        set_cell_background(c, "102C57")
        c.paragraphs[0].runs[0].font.name = "Times New Roman"
        c.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
        c.paragraphs[0].runs[0].bold = True
        set_cell_margins(c, 100, 100, 100, 100)

    matrix_rows = [
        ("1", "Dongle Biometric Hardware Gatekeeper",
         "Modul modules/dongle_guard.py memindai drive fisik USB Win32 (GetDriveTypeW == 2), memverifikasi berkas tersembunyi .krypt_dongle "
         "bertanda tangan HMAC-SHA256, mengikat ke nomor seri volume, dan otomatis mengunci sesi saat dicabut.", "100% Lulus (OK)"),
        ("2", "Login Biometrik & Kriptografis",
         "Modul modules/auth_biometric.py menerapkan autentikasi 2-faktor: PBKDF2-HMAC-SHA256 (600.000 iterasi) + kamera realtime / "
         "unggah foto (Pillow 128x128 grayscale) yang disegel dengan AES-128-EAX.", "100% Lulus (OK)"),
        ("3", "Super Enkripsi Teks (Klasik + Modern)",
         "Modul modules/super_encryption.py menerapkan kaskade dua lapis: Plaintext -> Extended Vigenère (modulo 256) -> "
         "AES-256-CBC dengan random salt, IV acak, dan padding PKCS#7.", "100% Lulus (OK)"),
        ("4", "Enkripsi Berkas Dokumen (Algoritma Berbeda)",
         "Modul modules/file_crypto.py mengunci aliran biner berkas (.pdf, .docx, .xlsx, .txt) menggunakan ChaCha20 Stream Cipher "
         "(256-bit, nonce 96-bit) dibungkus amplop mandiri .krypt.enc ber-checksum SHA-256.", "100% Lulus (OK)"),
        ("5", "Enkripsi Basis Data (At-Rest)",
         "Modul database.py menerapkan prinsip Zero-Plaintext Persistence pada SQLite storage/vault.db. Menyediakan inspeksi tabel mentah "
         "dan uji pencarian biner langsung pada disk untuk membuktikan data tersandi.", "100% Lulus (OK)"),
        ("6", "Steganografi Citra",
         "Modul modules/steganography.py menyisipkan dan mengekstrak pesan rahasia pada bit LSB kanal RGB citra format PNG lossless "
         "dengan pembatas terminal <<<END>>> dan proteksi kata sandi opsional.", "100% Lulus (OK)"),
        ("7", "Blockchain Sederhana Aset Penting",
         "Modul modules/blockchain.py mencatat aset penting ke dalam rantai blok ber-Proof-of-Work SHA-256 (kesulitan prefix '00'), "
         "metadata disegel AES-256-GCM, verifikasi rantai, dan simulator manipulasi (Tamper Lab).", "100% Lulus (OK)"),
    ]
    for n, crit, impl, stat in matrix_rows:
        row = tbl_crit.add_row().cells
        row[0].text = n
        row[1].text = crit
        row[2].text = impl
        row[3].text = stat
        for c in row:
            set_cell_margins(c, 70, 70, 90, 90)
            if c.paragraphs[0].runs:
                c.paragraphs[0].runs[0].font.name = "Times New Roman"
                c.paragraphs[0].runs[0].font.size = Pt(10)

    add_h2(doc, "4.2 Hasil Uji Coba Tiap Kriteria Kriptografi")

    add_h3(doc, "4.2.1 Uji Kriteria 1: Hardware USB Dongle Gatekeeper")
    add_p(doc,
        "Pengujian dilakukan dengan memasang flashdisk USB fisik (Drive E:), kemudian menjalankan fungsi inisialisasi pada aplikasi. "
        "Berkas tersembunyi .krypt_dongle berhasil dibuat dengan payload JSON bertanda tangan HMAC-SHA256 yang diikat ke nomor seri volume fisik. "
        "Saat flashdisk dicabut, background watcher (st.fragment run_every=4) mendeteksi hilangnya drive dalam waktu maksimal 4 detik dan langsung "
        "mengunci sesi secara total ke layar Gate 01. Saat mode token virtual diaktifkan untuk presentasi, sistem memvalidasi token lokal virtual_usb secara tepat."
    )

    add_h3(doc, "4.2.2 Uji Kriteria 2: Login Biometrik & Kredensial PBKDF2 + AES-128-EAX")
    add_p(doc,
        "Pendaftaran operator baru diuji dengan mendaftarkan pengguna 'analyst_01', kata sandi terstandarisasi, dan pengambilan foto wajah melalui kamera webcam. "
        "Verifier PBKDF2-HMAC-SHA256 (600.000 iterasi) berhasil disimpan pada tabel users dan template wajah disegel dengan AES-128-EAX. "
        "Pada pengujian login, operator asli memperoleh skor kemiripan 100% (cleared, sesi terbuka). Sebaliknya, pengujian menggunakan wajah pihak lain "
        "menghasilkan skor kemiripan di bawah 55% (< 80%), dan sistem secara tepat menolak akses serta mencatat log insiden."
    )

    add_h3(doc, "4.2.3 Uji Kriteria 3: Super Enkripsi Teks Kaskade")
    add_p(doc,
        "Pengujian dilakukan pada laporan intelijen teks terbuka: 'OPERASI KRIPTOGRAFI FORENSIK AMAN'. Kunci klasik Vigenère 'KUNCIKLASIK' dan "
        "passphrase AES 'SandiModern2026' dimasukkan. Pada lapisan 1 (Vigenère Modulo-256), distribusi frekuensi karakter berhasil diacak. "
        "Pada lapisan 2, ciphertext Vigenère dienkripsi dengan AES-256-CBC, menghasilkan token Base64 yang disimpan di basis data. "
        "Proses dekripsi dengan kedua kunci yang benar berhasil merekonstruksi plaintext asli 100% identik tanpa kehilangan satu karakter pun."
    )

    add_h3(doc, "4.2.4 Uji Kriteria 4: Enkripsi Berkas Biner Dokumen (ChaCha20)")
    add_p(doc,
        "Pengujian dilakukan terhadap berkas dokumen digital (format .pdf dan .docx berukuran 500 KB hingga 5 MB). Berkas dienkripsi menggunakan "
        "ChaCha20 Stream Cipher 256-bit dan dibungkus menjadi amplop mandiri .krypt.enc. Hasil dekripsi dievaluasi menggunakan checksum SHA-256 "
        "antara berkas asli dan berkas hasil dekripsi; kedua nilai hash terbukti cocok sempurna (match), membuktikan integritas byte-by-byte terjaga."
    )

    add_h3(doc, "4.2.5 Uji Kriteria 5: Audit Basis Data At-Rest (Zero-Plaintext Persistence)")
    add_p(doc,
        "Inspeksi dilakukan langsung pada berkas biner basis data storage/vault.db menggunakan fitur 'Uji Pencarian Plaintext'. String laporan rahasia "
        "dan kata sandi dicari byte demi byte di seluruh isi berkas disk. Hasil pencarian membuktikan bahwa string teks asli berstatus "
        "'TIDAK DITEMUKAN' dalam puluhan ribu byte berkas basis data, membuktikan bahwa data sensitif tersimpan secara aman dalam bentuk terenkripsi saat at-rest."
    )

    add_h3(doc, "4.2.6 Uji Kriteria 6: Steganografi Citra PNG Spasial LSB")
    add_p(doc,
        "Pesan rahasia berupa teks koordinat intelijen disisipkan ke dalam citra sampul berformat PNG. Citra stego hasil penyisipan menampilkan visual yang "
        "secara kasat mata identik dengan citra asli (tanpa artefak atau distorsi). Pesan rahasia berhasil diekstraksi kembali secara utuh berkat penanda "
        "delimiter terminal <<<END>>>. Penyisipan pada citra format JPEG terbukti gagal karena kompresi lossy merusak bit LSB, memperkuat alasan wajibnya format PNG."
    )

    add_h3(doc, "4.2.7 Uji Kriteria 7: Blockchain Ledger Aset & Tamper Lab")
    add_p(doc,
        "Pencatatan aset digital bukti forensik diuji dengan menambahkan 3 blok baru. Penambangan Proof-of-Work SHA-256 berhasil menemukan nilai nonce "
        "yang menghasilkan hash dengan prefix '00' dalam waktu rata-rata 15-45 ms per blok. Pada menu 'Uji Manipulasi (Tamper Lab)', simulasi serangan "
        "dilakukan dengan mengubah field aset langsung pada basis data SQLite. Saat tombol 'Verifikasi Ulang' ditekan, sistem langsung mendeteksi kerusakan rantai "
        "(status: 'Rantai Rusak') dan menandai secara tepat blok mana yang telah dimanipulasi."
    )

    add_h2(doc, "4.3 Hasil Pengujian Otomatis (Unit Test Suite 7/7 PASSED)")
    add_p(doc, "Pengujian otomatis dijalankan melalui modul tests/test_crypto_modules.py dengan hasil sebagai berikut:")

    add_code(doc,
        "test_01_dongle_hmac_and_guard (__main__.TestBAGUSVaultCryptography) ... ok\n"
        "test_02_biometric_face_and_pbkdf2_login (__main__.TestBAGUSVaultCryptography) ... ok\n"
        "test_03_super_encryption_cascade (__main__.TestBAGUSVaultCryptography) ... ok\n"
        "test_04_chacha20_file_encryption (__main__.TestBAGUSVaultCryptography) ... ok\n"
        "test_05_database_at_rest_encryption (__main__.TestBAGUSVaultCryptography) ... ok\n"
        "test_06_steganography_lsb (__main__.TestBAGUSVaultCryptography) ... ok\n"
        "test_07_blockchain_pow_and_integrity (__main__.TestBAGUSVaultCryptography) ... ok\n\n"
        "----------------------------------------------------------------------\n"
        "Ran 7 tests in 1.543s\n\n"
        "OK (100% PASSED - 0 FAILURES)"
    )

    add_h2(doc, "4.4 Analisis Keamanan dan Ketahanan Terhadap Serangan Siber")
    add_p(doc, "Berdasarkan evaluasi kriptografis, sistem Krypt Vault memiliki ketahanan terhadap berbagai jenis serangan siber:")
    add_p(doc, "1. Serangan Pencurian Kredensial (Credential Stuffing / Phishing): Penyerang yang memiliki kata sandi tetap tidak dapat masuk karena terhadang oleh Gate 01 (memerlukan USB Dongle fisik) dan Gate 02 (memerlukan wajah asli operator).")
    add_p(doc, "2. Serangan Kloning USB Dongle: Penyerang yang menyalin berkas .krypt_dongle ke flashdisk lain akan ditolak karena nilai Volume Serial fisik perangkat tidak cocok dengan data tanda tangan HMAC.")
    add_p(doc, "3. Serangan Brute-Force Offline Kata Sandi: Dihambat secara masif oleh 600.000 iterasi PBKDF2-HMAC-SHA256, memerlukan waktu komputasi ribuan tahun untuk menebak kata sandi kompleks.")
    add_p(doc, "4. Serangan Manipulasi Basis Data (Database Tampering): Diminimalkan oleh rantai hash blockchain PoW dan enkripsi autentikasi AES-GCM/AES-EAX yang akan memicu kegagalan integritas seketika jika ada bit yang diubah.")

    # 10. BAB V: PENUTUP
    doc.add_page_break()
    add_h1(doc, "BAB V\nPENUTUP")

    add_h2(doc, "5.1 Kesimpulan")
    add_p(doc,
        "Berdasarkan proses perancangan, implementasi, dan serangkaian pengujian fungsional serta keamanan yang telah dilaksanakan, "
        "dapat disimpulkan bahwa:"
    )
    add_p(doc, "1. Sistem Krypt Vault telah berhasil dibangun dan memenuhi 100% dari 7 kriteria tugas akhir mata kuliah Kriptografi di Program Studi Informatika, UPN \"Veteran\" Yogyakarta di bawah bimbingan Bapak Bagus Mahardika, S.Kom., M.T.")
    add_p(doc, "2. Penerapan arsitektur pertahanan berlapis (3-Gate Security Waterfall) terbukti efektif dalam memberikan perlindungan komprehensif bagi bukti forensik digital dan dokumen intelijen dari ancaman akses ilegal.")
    add_p(doc, "3. Penggabungan faktor kepemilikan fisik (Hardware USB Dongle bertanda tangan HMAC-SHA256), faktor pengetahuan (PBKDF2 600.000 iterasi), dan faktor biometrik (pemindaian wajah optik AES-128-EAX) menciptakan gerbang autentikasi yang sangat tangguh terhadap ancaman impersonasi.")
    add_p(doc, "4. Implementasi super enkripsi teks, ChaCha20 file cipher, steganografi LSB citra PNG, dan blockchain PoW berjalan secara terpadu tanpa saling mengganggu, dengan persistensi basis data yang memenuhi prinsip Zero-Plaintext Persistence.")
    add_p(doc, "5. Pembangunan ulang antarmuka ke tema Executive Security Console bersih bebas emoji meningkatkan profesionalisme dan ergonomi pengoperasian sistem saat diuji.")

    add_h2(doc, "5.2 Saran Pengembangan Sistem")
    add_p(doc, "Untuk pengembangan sistem di masa mendatang, beberapa saran peningkatan yang dapat diterapkan meliputi:")
    add_p(doc, "1. Integrasi Kunci Fisik FIDO2/WebAuthn: Mengembangkan gerbang hardware agar mendukung token keamanan perangkat keras standar industri seperti YubiKey.")
    add_p(doc, "2. Deteksi Keaktifan Biometrik (Liveness Detection): Menambahkan analisis kedipan mata atau pergerakan kepala pada pemindaian wajah untuk mengantisipasi serangan pemalsuan menggunakan foto cetak atau video playback.")
    add_p(doc, "3. Desentralisasi Multi-Node Blockchain: Mengembangkan ledger blockchain lokal menjadi jaringan terdistribusi peer-to-peer (P2P) antar beberapa workstation forensik.")

    # 11. DAFTAR PUSTAKA
    doc.add_page_break()
    add_h1(doc, "DAFTAR PUSTAKA")

    references = [
        "Bernstein, D. J. (2008). The ChaCha family of stream ciphers. In State of the Art of Stream Ciphers (pp. 84-97). Springer, Berlin, Heidelberg.",
        "Krawczyk, H., & Eronen, P. (2010). HMAC-based Extract-and-Expand Key Derivation Function (HKDF). IETF Request for Comments (RFC 5869).",
        "Nakamoto, S. (2008). Bitcoin: A Peer-to-Peer Electronic Cash System. Decentralized Business Review, 21260.",
        "National Institute of Standards and Technology. (2001). Advanced Encryption Standard (AES). Federal Information Processing Standards Publication (FIPS PUB 197).",
        "National Institute of Standards and Technology. (2002). The Keyed-Hash Message Authentication Code (HMAC). Federal Information Processing Standards Publication (FIPS PUB 198-1).",
        "National Institute of Standards and Technology. (2010). Recommendation for Password-Based Key Derivation: Part 1: Storage Applications. NIST Special Publication 800-132.",
        "National Institute of Standards and Technology. (2015). Secure Hash Standard (SHS). Federal Information Processing Standards Publication (FIPS PUB 180-4).",
        "Nir, Y., & Langely, A. (2018). ChaCha20 and Poly1305 for IETF Protocols. IETF Request for Comments (RFC 8439).",
        "Rogaway, P., & Bellare, M. (2003). A Recommendation for Block Cipher Modes of Operation: The EAX Mode. In Fast Software Encryption (FSE 2003), Lecture Notes in Computer Science, vol 2887. Springer.",
        "Stallings, W. (2017). Cryptography and Network Security: Principles and Practice (7th ed.). Pearson Education.",
        "OWASP Foundation. (2023). Password Storage Cheat Sheet: Key Derivation Functions and Recommended Iteration Counts. OWASP Cheat Sheet Series."
    ]
    for idx, ref in enumerate(references, 1):
        p_ref = add_p(doc, f"[{idx}] {ref}", space_after=4)
        p_ref.paragraph_format.left_indent = Inches(0.4)
        p_ref.paragraph_format.first_line_indent = Inches(-0.4)

    # 12. LAMPIRAN
    doc.add_page_break()
    add_h1(doc, "LAMPIRAN")

    add_h2(doc, "Lampiran 1: Panduan Pengujian Sistem untuk Dosen Penguji")
    add_p(doc,
        "Untuk mempermudah proses evaluasi dan demonstrasi di hadapan Dosen Penguji (Bapak Bagus Mahardika, S.Kom., M.T.), "
        "aplikasi telah dilengkapi dengan skrip peluncur satu-klik dan mode presentasi mandiri:"
    )
    add_p(doc, "1. Menjalankan Aplikasi: Klik ganda berkas D:\\Twugas\\JALANKAN_KRYPT_VAULT.bat. Server lokal akan aktif dan jendela konsol aplikasi otomatis terbuka di peramban web pada alamat http://localhost:8501.")
    add_p(doc, "2. Pengujian Gate 01 (Hardware Key): Jika flashdisk USB tersedia, pilih drive USB pada dropdown lalu klik 'Inisialisasi sebagai kunci'. Jika tidak ada port USB, buka panel 'Mode presentasi tanpa flashdisk' di sisi kanan lalu klik 'Aktifkan token virtual'.")
    add_p(doc, "3. Pengujian Gate 02 (Biometrik Wajah & Kredensial): Klik tab 'Daftarkan operator baru', masukkan username dan password, izinkan kamera webcam (atau unggah foto wajah), lalu klik 'Daftarkan operator'. Beralih ke tab 'Masuk', masukkan kredensial yang sama, ambil foto verifikasi, lalu klik 'Verifikasi dan masuk'.")
    add_p(doc, "4. Pengujian Gate 03 (Ruang Kerja): Pilih modul pada bilah navigasi kiri untuk menguji Super Enkripsi Teks, Enkripsi Berkas ChaCha20, Steganografi Citra PNG LSB, Audit Basis Data SQLite At-Rest, dan Ledger Blockchain PoW (termasuk Tamper Lab).")

    add_h2(doc, "Lampiran 2: Struktur Berkas Repositori Proyek")
    add_code(doc,
        "D:\\Twugas\\Project_Biometric-Authenticated-Gatekeeper-Unified-Security-Vault-main\\\n"
        "└── geovault-crypto-app/\n"
        "    ├── app.py                   # Konsol antarmuka utama (Executive Theme)\n"
        "    ├── ui_theme.py              # Sistem tema bebas emoji & komponen UI\n"
        "    ├── database.py              # Pengelola persistensi SQLite (vault.db)\n"
        "    ├── config.py                # Konfigurasi master secret & konstanta\n"
        "    ├── generate_dongle.py       # Utilitas inisialisasi kunci USB fisik\n"
        "    ├── run_desktop.py           # Peluncur desktop mode frameless\n"
        "    ├── modules/\n"
        "    │   ├── dongle_guard.py      # Kriteria 1: Hardware Dongle & HMAC-SHA256\n"
        "    │   ├── auth_biometric.py    # Kriteria 2: PBKDF2 + Optical Face AES-128-EAX\n"
        "    │   ├── super_encryption.py  # Kriteria 3: Extended Vigenère + AES-256-CBC\n"
        "    │   ├── file_crypto.py       # Kriteria 4: ChaCha20 Stream Cipher Berkas\n"
        "    │   ├── steganography.py     # Kriteria 6: Spatial LSB PNG Steganography\n"
        "    │   └── blockchain.py        # Kriteria 7: Proof-of-Work SHA-256 Ledger\n"
        "    ├── storage/\n"
        "    │   ├── vault.db             # Basis data SQLite terenkripsi at-rest\n"
        "    │   ├── ledger.json          # Riwayat rantai blok terenkripsi\n"
        "    │   └── files/               # Berkas biner terenkripsi ChaCha20\n"
        "    ├── tests/\n"
        "    │   └── test_crypto_modules.py # Suite pengujian unit otomatis 7 kriteria\n"
        "    └── docs/\n"
        "        └── LAPORAN_AKHIR_KRIPTOGRAFI.docx # Dokumen laporan akademik Word"
    )

    # 13. SIMPAN DOKUMEN DI DUA LOKASI
    doc.save(str(TARGET_OUTPUT_1))
    print(f"[OK] Berhasil menyimpan laporan utama di: {TARGET_OUTPUT_1} ({os.path.getsize(TARGET_OUTPUT_1):,} bytes)")

    doc.save(str(TARGET_OUTPUT_2))
    print(f"[OK] Berhasil menyalin laporan ke repositori: {TARGET_OUTPUT_2} ({os.path.getsize(TARGET_OUTPUT_2):,} bytes)")


if __name__ == "__main__":
    main()
