# Log Penggunaan AI

Catat setiap penggunaan AI atau coding agent yang memengaruhi kode atau laporan.

| No | Siapa | Prompt / tugas (ringkas) | Hasil: diterima, diubah, atau ditolak | Alasan | Cara verifikasi |
| --- | --- | --- | --- | --- | --- |
| 1 | Muhammad Iqbal | Analisis bug pada lexer (case-sensitivity keyword, operator <>, escape string, dan TODO T3 komentar blok) | Diterima | Saran perbaikan langsung mengacu pada SPESIFIKASI.md bagian 2 dan buku Crafting Interpreters Bab 4 | Menjalankan `pytest tests/test_lexer.py` dan membuat test regresi di `tests/test_tambahan.py` (semua lulus 100%) |
| 2 | Muhamad Akmal Rizqillah | Berikan penjelasan dan analisis parser.py serta tahapan pengerjaan | Diterima | Analisis memetakan fungsi parser ke grammar SPESIFIKASI.md bagian 3 dan 6, termasuk menemukan kekurangan pada error recovery, presedensi OR/AND, dan LEFT OUTER JOIN | Menjalankan `pytest tests/test_parser.py` (12 lulus) dan menambahkan test regresi di `tests/test_tambahan.py` (lulus semua) |
| 3 | Muhamad Akmal Rizqillah | Analisis bug pada resolver (scope, pencarian tanpa qualifier, T2) | Diterima | Gejala dan akar masalah sesuai `SPESIFIKASI.md` bagian 4 | SQL minimal pada kode lama dan baru, `pytest` resolver, test regresi gagal di kode awal dan lulus di perbaikan |

**Refleksi (3-5 kalimat).** Di bagian mana AI paling membantu? Di mana AI keliru atau
menyesatkan, dan bagaimana kalian mengetahuinya?
AI sangat membantu dalam membedah spesifikasi dengan cepat untuk menemukan bug tersembunyi seperti operator `<>` dan escape quote `''` yang belum teruji pada `test_lexer.py` bawaan. AI juga mempercepat pemetaan konsep buku *Crafting Interpreters* Bab 4 ke implementasi Python. Verifikasi tetap dilakukan secara empiris dengan mengeksekusi test suite pytest dan memastikan tidak ada perubahan pada API publik.
AI paling membantu dalam membandingkan parser.py dengan SPESIFIKASI.md dan menemukan bug yang tidak terdeteksi oleh test bawaan, yaitu error recovery yang membuang seluruh input (bukan sampai ;), presedensi OR/AND yang disamakan, dan LEFT OUTER JOIN yang belum didukung, selain TODO T1 (INSERT ... SELECT). AI juga membantu memetakan fungsi parser ke aturan grammar sehingga alur parsing lebih mudah dipahami. Hasilnya dapat diketahui bahwa benar dengan menjalankan pytest tests/test_parser.py (12 lulus).
AI paling membantu untuk orientasi, mencari kemungkinan bug, serta menganalisis bug tersebut juga. Tetapi harus mencocokkan semuanya dengan SPESIFIKASI.md, karena penjelasan AI bisa meleset. Diminta untuk melakukan test regresi kembali menggunakan kode awal dan terbukti gagal.