# Log Penggunaan AI

Catat setiap penggunaan AI atau coding agent yang memengaruhi kode atau laporan.

| No | Siapa | Prompt / tugas (ringkas) | Hasil: diterima, diubah, atau ditolak | Alasan | Cara verifikasi |
| --- | --- | --- | --- | --- | --- |
| 1 | Muhammad Iqbal | Analisis bug pada lexer (case-sensitivity keyword, operator <>, escape string, dan TODO T3 komentar blok) | Diterima | Saran perbaikan langsung mengacu pada SPESIFIKASI.md bagian 2 dan buku Crafting Interpreters Bab 4 | Menjalankan `pytest tests/test_lexer.py` dan membuat test regresi di `tests/test_tambahan.py` (semua lulus 100%) |

**Refleksi (3-5 kalimat).** Di bagian mana AI paling membantu? Di mana AI keliru atau
menyesatkan, dan bagaimana kalian mengetahuinya?
AI sangat membantu dalam membedah spesifikasi dengan cepat untuk menemukan bug tersembunyi seperti operator `<>` dan escape quote `''` yang belum teruji pada `test_lexer.py` bawaan. AI juga mempercepat pemetaan konsep buku *Crafting Interpreters* Bab 4 ke implementasi Python. Verifikasi tetap dilakukan secara empiris dengan mengeksekusi test suite pytest dan memastikan tidak ada perubahan pada API publik.
