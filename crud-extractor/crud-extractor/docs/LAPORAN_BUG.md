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

## Bug 4: INSERT ... SELECT Ditolak oleh Parser (TODO T1)

**Ditemukan oleh: Muhamad Akmal Rizqillah** · **Diperbaiki oleh: Muhamad Akmal Rizqillah**

**Gejala.**
Menjalankan `INSERT INTO a SELECT id FROM b` ditolak parser dengan pesan “Baris 1, kolom 15: `INSERT ... SELECT` belum didukung, ditemukan ‘SELECT’”, dan tidak ada statement yang terbentuk. Padahal di SPESIFIKASI.md bagian 3, insert_stmt boleh diikuti VALUES atau select_stmt, dan bagian 5 menetapkan tabel tujuan sebagai C dan tabel sumber sebagai R.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
INSERT INTO a SELECT id FROM b
```

**Akar masalah.**
Di Bab 6, setiap aturan grammar kita terjemahkan jadi satu fungsi, dan kalau aturannya punya pilihan (A | B, notasinya dari Bab 5), fungsinya harus melihat token berikutnya untuk memilih cabang. Aturan insert_stmt punya dua cabang: `VALUES` ... atau `select_stmt. _insert()` yang lama cuma mengerjakan cabang `VALUES`. Begitu ketemu `SELECT`, dia langsung melempar ParseError. Padahal `_select()` sudah ada dan tinggal dipanggil. Jadi grammar-nya tidak salah, hanya kodenya belum mencakup semua cabang aturan itu.

**Perbaikan.**
Di `crud/parser.py`, fungsi `_insert`, cabang yang tadinya melempar error kami ganti. Sekarang kalau token berikutnya `SELECT`, parser memanggil `self._select()` dan hasilnya dimasukkan ke field query pada `ast.Insert`, sedangkan values diisi list kosong. Alternatif yang ditolak: menulis fungsi parser baru khusus `INSERT ... SELECT`. Ditolak karena isinya akan menggandakan `_select()` dan menyulitkan perawatan kalau aturan `SELECT` berubah.

**Test regresi.**
`test_regresi_insert_select_didukung` di `tests/test_tambahan.py`.

**Peran AI.**
AI membantu untuk menjelaskan dan menganalisis TODO1 berdasarkan `SPESIFIKASI.md` bagian 3 dan 5. Hasilnya diperiksa dengan pytest `tests/test_parser.py` (termasuk test_insert_select yang sebelumnya gagal) dan test regresi di atas.

---

## Bug 5: Error Recovery Membuang Seluruh Sisa Input

**Ditemukan oleh: Muhamad Akmal Rizqillah** · **Diperbaiki oleh: Muhamad Akmal Rizqillah**

**Gejala.**
Pada input `SELECT FROM; SELECT id FROM t`, parser memang melaporkan satu error, tapi jumlah statement yang berhasil hanya 0. Statement kedua yang valid ikut lenyap. Menurut `SPESIFIKASI.md` bagian 6, parser harus membuang token sampai dan termasuk ; berikutnya lalu lanjut, sehingga hasil yang benar adalah 1 error dan 1 statement.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
SELECT FROM; SELECT id FROM t
```

**Akar masalah.**
Waktu parser ketemu error, dia tidak boleh berhenti total, karena kita ingin semua error terlaporkan sekaligus. Di Bab 6 caranya disebut panic mode: token dibuang sampai titik aman, lalu parsing lanjut (sinkronisasi). Untuk SQL, titik amannya adalah ;. `_synchronize()` yang lama tidak pernah mengecek token apa pun, cuma memanggil `_advance()` sampai EOF. Akibatnya tidak ada titik berhenti, dan statement valid sesudah error ikut hilang.

**Perbaikan.**
Di `crud/parser.py`, fungsi `_synchronize` sekarang memeriksa setiap token yang dibuang. Begitu yang dibuang bertipe SEMICOLON, fungsi langsung selesai dan `parse_script` meneruskan ke statement berikutnya. Alternatif yang ditolak: berhenti di keyword awal statement seperti `SELECT` atau `INSERT`. Ditolak karena `SELECT` juga muncul di dalam subquery, sehingga parser bisa berhenti di tengah statement yang masih rusak. Selain itu spesifikasi menyebut ; sebagai batasnya.

**Test regresi.**
`test_regresi_error_recovery_sampai_titik_koma` di `tests/test_tambahan.py`.

**Peran AI.**
AI membandingkan `_synchronize()` dengan `SPESIFIKASI.md` bagian 6 dan melihat bahwa ; tidak pernah dikenali. Diverifikasi dengan test regresi di atas (1 error, 2 statement valid pada input uji).

---

## Bug 6: AND dan OR Memiliki Presedensi yang Sama

**Ditemukan oleh: Muhamad Akmal Rizqillah** · **Diperbaiki oleh: Muhamad Akmal Rizqillah**

**Gejala.**
Ekspresi a = 1 OR b = 2 AND c = 3 terbentuk sebagai (a = 1 OR b = 2) AND c = 3: node paling luar AND, anak kirinya OR. Tabel presedensi di `SPESIFIKASI.md` bagian 3.1 menaruh AND di atas OR, jadi bentuk yang benar adalah a = 1 OR (b = 2 AND c = 3) dengan OR di luar.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
SELECT a FROM t WHERE a = 1 OR b = 2 AND c = 3
```

**Akar masalah.**
Di recursive descent, presedensi ditentukan oleh susunan fungsi (Bab 6): operator yang lebih lemah ditaruh di fungsi lebih atas, dan operandnya diambil dari fungsi di bawahnya. Operator yang lebih kuat jadi terikat lebih dulu. `_logical()` yang lama memasukkan AND dan OR ke satu loop, jadi keduanya setara dan dibaca dari kiri ke kanan. Karena OR muncul duluan, dia membungkus a = 1 dan b = 2 sebelum AND sempat mengikat b = 2 dengan c = 3. Seharusnya dipisah jadi dua tingkat: OR di atas, AND di bawahnya.

**Perbaikan.**
Di `crud/parser.py, _logical()` kami ubah supaya hanya menangani OR dan mengambil operandnya dari fungsi baru `_and()`. Fungsi `_and()` menangani AND dan mengambil operandnya dari `_not()`. Dengan susunan ini AND selalu berada lebih dalam di pohon daripada OR. Alternatif yang ditolak: precedence climbing dengan tabel presedensi. Ditolak karena bagian parser lainnya sudah memakai pola satu fungsi per tingkat, jadi mengganti metode hanya untuk satu tingkat akan membuat gaya kodenya tidak seragam.

**Test regresi.**
`test_regresi_presedensi_and_lebih_tinggi_dari_or` di `tests/test_tambahan.py`.

**Peran AI.**
AI membandingkan `_logical()` dengan tabel presedensi di `SPESIFIKASI.md` bagian 3.1 dan menunjukkan bahwa AND dan OR dicampur. Diverifikasi dengan test regresi di atas yang memeriksa `where.op == "OR"` dan `where.right.op == "AND"`.

---

## Bug 7: LEFT OUTER JOIN Ditolak oleh Parser

**Ditemukan oleh: Muhamad Akmal Rizqillah** · **Diperbaiki oleh: Muhamad Akmal Rizqillah**

**Gejala.**
Query `SELECT a FROM t LEFT OUTER JOIN u ON u.x = t.x` gagal dengan pesan “Baris 1, kolom 22: diharapkan `JOIN`, ditemukan `‘OUTER’`”, dan statement-nya tidak dihitung. Grammar di `SPESIFIKASI.md` bagian 3 menulis "LEFT" [ "OUTER" ], artinya kata OUTER setelah LEFT boleh ada.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
SELECT a FROM t LEFT OUTER JOIN u ON u.x = t.x
```

**Akar masalah.**
Di grammar, [ ... ] berarti bagian itu opsional. Saat dijadikan kode (Bab 6), artinya “kalau token berikutnya cocok, konsumsi, kalau tidak, lanjut saja”. `_join()` yang lama langsung memanggil `_expect_kw("JOIN")` sesudah `LEFT`, jadi `OUTER` tidak pernah diberi kesempatan. Bagian opsional di grammar tidak ikut diterjemahkan ke kode, sehingga input yang sebenarnya sah ditolak.

**Perbaikan.**
Di `crud/parser.py`, fungsi `_join`, tepat setelah `LEFT` terbaca, ditambahkan `self._match_kw("OUTER")`, yang mengambil `OUTER` hanya kalau memang ada. Jenis join tetap dicatat sebagai `"LEFT"`. Alternatif yang ditolak: mengubah jenis join menjadi `"LEFT OUTER"`. Ditolak karena field Join.kind dipakai bagian lain, dan secara makna `LEFT JOIN` sama dengan `LEFT OUTER JOIN`.

**Test regresi.**
`test_regresi_left_outer_join_didukung` di `tests/test_tambahan.py`.

**Peran AI.**
AI menemukan ketidaksesuaian ini saat mencocokkan `_join()` dengan grammar di `SPESIFIKASI.md`  bagian 3. Diverifikasi dengan test regresi di atas dan pemeriksaan manual pada parser lama (error diharapkan `JOIN`, ditemukan `'OUTER'`).