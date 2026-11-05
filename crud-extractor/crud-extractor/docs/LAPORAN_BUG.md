# Laporan Bug

Salin blok di bawah untuk setiap bug. Bagian **Akar masalah** wajib ditulis dengan kata-kata
sendiri dan memakai konsep dari *Crafting Interpreters* (sebutkan bab). Bagian ini diuji lisan.

---

## Bug 1: Keyword Huruf Kecil/Campuran Dianggap Identifier dan Tidak Dinormalisasi

**Ditemukan oleh:** Muhammad Iqbal · **Diperbaiki oleh:** Muhammad Iqbal

**Gejala.**
Input SQL seperti `select id from t` menghasilkan token pertama bertipe `TokenType.IDENT` bernilai `'select'`, bukan `TokenType.KEYWORD` bernilai `'SELECT'`.
Menurut SPESIFIKASI.md Bagian 2.2: Keyword tidak peka huruf besar/kecil (`select`, `Select`, dan `SELECT` sama-sama keyword), dan nilai token keyword selalu dinormalisasi ke huruf besar.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
select 1
```

**Akar masalah.**
Mengacu pada *Crafting Interpreters Bab 4 (Scanning)* pada subbab pengenalan kata kunci (*Reserved Words*): ketika pemindai kata (`_word`) selesai membaca urutan alfanumerik, kode lama langsung mengecek keberadaan teks mentah di dalam `KEYWORDS` menggunakan `if text in KEYWORDS:`. Karena himpunan `KEYWORDS` didefinisikan dengan huruf kapital (`SELECT`, `FROM`, dll.), string yang ditulis dengan huruf kecil atau campuran (`select`, `Select`) tidak cocok, sehingga keliru dialirkan ke cabang `else` sebagai `IDENT`. Selain itu, nilai token tidak dinormalisasi ke huruf kapital (`text.upper()`).

**Perbaikan.**
File `crud/lexer.py`, fungsi `_word(self, line: int, col: int)`.
Sebelum pengecekan ke `KEYWORDS`, teks terlebih dahulu dikonversi ke huruf kapital menggunakan `upper = text.upper()`. Jika `upper in KEYWORDS`, buat token `KEYWORD` dengan nilai `upper`. Jika tidak, buat token `IDENT` dengan mempertahankan nilai aslinya `text` (karena nama tabel/kolom nanti dinormalisasi oleh parser sesuai spesifikasi).
*Alternatif yang ditolak:* Mengubah himpunan `KEYWORDS` agar memuat semua variasi huruf besar-kecil secara eksplisit. Alternatif ini ditolak karena mustahil mencakup semua kombinasi case (`sElEcT`, `Select`) dan melanggar prinsip normalisasi token.

**Test regresi.**
`test_regresi_keyword_case_insensitive_dan_ident` di `tests/test_tambahan.py`.

**Peran AI.**
AI membantu mendeteksi kegagalan test `test_keyword_huruf_kecil` dan menyarankan normalisasi uppercase di fungsi `_word()`. Diverifikasi dengan menjalankan `pytest tests/test_lexer.py`.

---

## Bug 2: Operator Perbandingan `<>` Dipecah Menjadi Dua Token Terpisah

**Ditemukan oleh:** Muhammad Iqbal · **Diperbaiki oleh:** Muhammad Iqbal

**Gejala.**
Input SQL yang memuat operator perbandingan tidak-sama-dengan `<>` menghasilkan dua token terpisah: `Token(OP, '<')` diikuti `Token(OP, '>')`.
Menurut SPESIFIKASI.md Bagian 2.5: Operator `<>` adalah satu token `OP`, bukan `<` lalu `>`, dan lexer harus menerapkan prinsip maximal munch.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
a <> b
```

**Akar masalah.**
Mengacu pada *Crafting Interpreters Bab 4 (Scanning)* pada prinsip *Maximal Munch* (pencocokan awalan terpanjang): ketika karakter pembuka `<` ditemukan, lexer harus memeriksa apakah karakter berikutnya dapat membentuk operator multi-karakter yang valid sebelum memutuskan menjadi operator tunggal. Kode lama hanya memeriksa apakah `<` diikuti oleh `=` (menjadi `<=`), tetapi tidak memeriksa apakah `<` diikuti oleh `>` (menjadi `<>`). Akibatnya, `<` langsung diemisikan sebagai token tersendiri, dan karakter `>` terbaca pada putaran pemindaian berikutnya.

**Perbaikan.**
File `crud/lexer.py`, fungsi `_scan_token(self)`.
Pada cabang evaluasi `if ch == "<":`, ditambahkan pemeriksaan lanjutan `elif self._match(">"):` yang menghasilkan `Token(TokenType.OP, "<>", line, col)`.
*Alternatif yang ditolak:* Menambahkan `<>` ke dalam dictionary `_SINGLE` atau daftar string satu karakter. Ditolak karena `<>` terdiri dari 2 karakter dan bukan token tunggal statis.

**Test regresi.**
`test_regresi_operator_maximal_munch_tidak_sama_dengan` di `tests/test_tambahan.py`.

**Peran AI.**
AI membantu menelaah SPESIFIKASI.md bagian 2.5 dan mengidentifikasi bahwa percabangan operator `<` belum mengonsumsi `>`. Diverifikasi dengan test regresi di `tests/test_tambahan.py`.

---

## Bug 3: String Literal Memotong Escape Kutip Tunggal `''`

**Ditemukan oleh:** Muhammad Iqbal · **Diperbaiki oleh:** Muhammad Iqbal

**Gejala.**
Input string dengan escape kutip tunggal ganda seperti `'O''Brien'` memicu pemotongan string yang salah: token pertama bernilai `'O'`, diikuti error atau sisa kata `'Brien'` yang tidak ter-parse dengan benar.
Menurut SPESIFIKASI.md Bagian 2.4: Dua kutip berturut-turut di dalam string (`''`) mewakili satu karakter kutip, sehingga `'O''Brien'` harus menjadi satu token `STRING` bernilai `O'Brien`.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
'O''Brien'
```

**Akar masalah.**
Mengacu pada *Crafting Interpreters Bab 4 (Scanning)* pada penanganan *String Literals*: penanda akhir sebuah string adalah karakter pembatas kutip penutup, kecuali jika karakter tersebut di-escape. Pada sintaks SQL standar, karakter escape untuk kutip tunggal bukanlah backslash (`\`), melainkan dua kutip berturut-turut (`''`). Kode lama pada `_string()` langsung melakukan `break` segera setelah menemukan karakter kutip `'` pertama, tanpa melakukan *lookahead* untuk memeriksa apakah kutip tersebut langsung diikuti oleh kutip kedua.

**Perbaikan.**
File `crud/lexer.py`, fungsi `_string(self, line: int, col: int)`.
Ketika ditemukan karakter `'`, gunakan `if self._match("'"): chars.append("'")` untuk mengonsumsi kutip kedua dan memasukkan satu karakter `'` ke dalam isi buffer string. Jika tidak diikuti kutip kedua, barulah loop dihentikan (`break`) karena merupakan tanda penutup string yang sah.
*Alternatif yang ditolak:* Menggunakan regex replace setelah pembacaan string selesai. Ditolak karena lexer bekerja secara streaming per karakter dan regex tidak dapat membedakan kutip penutup asli dengan kutip escape di batas akhir token secara aman tanpa lookahead.

**Test regresi.**
`test_regresi_string_escape_quote` di `tests/test_tambahan.py`.

**Peran AI.**
AI membantu mendeteksi bug ini dari pembacaan `pemeliharaan.sql` dan mencocokkannya dengan SPESIFIKASI.md bagian 2.4. Diverifikasi dengan test regresi di `tests/test_tambahan.py`.

---
