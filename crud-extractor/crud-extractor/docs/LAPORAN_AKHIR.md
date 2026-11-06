# Laporan Akhir

## 1. Hasil evaluasi

Tempel keluaran `python evaluate.py` setelah `data/ground_truth.csv` dilengkapi.

```text
Dievaluasi: audit.sql, campuran_error.sql, laporan_penjualan.sql, pemeliharaan.sql (27 triple)

Metode   Precision  Recall     F1
parser        1.00    1.00   1.00
regex         0.65    0.81   0.72

[regex]
  salah ditemukan (FP): ('audit.sql', 16, 'sesi', 'R')
  salah ditemukan (FP): ('campuran_error.sql', 4, 'pesanan', 'R')
  salah ditemukan (FP): ('campuran_error.sql', 8, 'keranjang', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'pelanggan', 'D')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'pelanggan', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'pesanan', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'rahasia', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 15, 'pesanan', 'R')
  salah ditemukan (FP): ('pemeliharaan.sql', 2, 'crm.alamat', 'R')
  salah ditemukan (FP): ('pemeliharaan.sql', 2, 'crm.pelanggan', 'R')
  salah ditemukan (FP): ('pemeliharaan.sql', 2, 'pelanggan_lama', 'U')
  salah ditemukan (FP): ('pemeliharaan.sql', 15, 'crm.alamat', 'R')
  terlewat (FN):       ('audit.sql', 2, 'pesanan', 'R')
  terlewat (FN):       ('laporan_penjualan.sql', 3, 'pelanggan', 'R')
  terlewat (FN):       ('laporan_penjualan.sql', 3, 'pesanan', 'R')
  terlewat (FN):       ('pemeliharaan.sql', 3, 'crm.alamat', 'R')
  terlewat (FN):       ('pemeliharaan.sql', 3, 'crm.pelanggan', 'R')
```

## 2. Tiga kasus di mana regex salah

Untuk tiap kasus: SQL-nya, kesalahan regex, dan mengapa parser benar (kaitkan dengan konsep
lexing, parsing, atau resolusi).

1. **Kata Kunci SQL di Dalam Komentar (Kaitannya dengan Konsep Lexing/Scanning):**
   - **Potongan SQL (`laporan_penjualan.sql` baris 2 & `pemeliharaan.sql` baris 2):**
     ```sql
     -- DELETE FROM pelanggan   (baris ini komentar, bukan perintah)
     ```
     dan
     ```sql
     /* Skrip pemeliharaan data pelanggan.
        Catatan lama: UPDATE pelanggan_lama sudah tidak dipakai. */
     ```
   - **Kesalahan regex:**
     Ketika pola regex `\bDELETE\s+FROM\s+([A-Za-z_]\w*)` dan `\bUPDATE\s+([A-Za-z_]\w*)` dijalankan, ia mencocokkan teks yang berada di dalam komentar baris (`--`) maupun komentar blok (`/* ... */`). Akibatnya, regex menghasilkan False Positive: `('laporan_penjualan.sql', 2, 'pelanggan', 'D')` dan `('pemeliharaan.sql', 2, 'pelanggan_lama', 'U')`. Selain itu, pencarian awal statement (`_START`) salah mengira baris komentar tersebut sebagai awal dari query baru, sehingga nomor baris statement berikutnya ikut tergeser.
   - **Mengapa parser benar:**
     Mengacu pada *Crafting Interpreters Bab 4 (Scanning)*, tahap pertama pipeline kompilasi adalah *lexical analysis* di mana teks sumber diubah menjadi deretan token bermakna. Pemindai leksikal (`crud/lexer.py`) membuang seluruh karakter komentar (baik komentar satu baris yang diawali `--` maupun komentar blok multi-baris `/* ... */` pada TODO T3) sebagai *whitespace/trivia*. Karakter tersebut tidak pernah diubah menjadi token `KEYWORD`, sehingga parser tidak pernah melihat perintah `DELETE` atau `UPDATE` palsu tersebut. Parser dengan benar mengenali bahwa statement sesungguhnya baru dimulai pada baris 3.

2. **Kata Kunci SQL di Dalam String Literal (Kaitannya dengan Konsep Lexing dan AST Parsing):**
   - **Potongan SQL (`laporan_penjualan.sql` baris 6):**
     ```sql
     WHERE o.status = 'LUNAS' AND o.catatan <> 'FROM rahasia'
     ```
   - **Kesalahan regex:**
     Regex menggunakan pola `\bFROM\s+([A-Za-z_]\w*)` untuk menangkap tabel yang dibaca (operasi `R`). Karena regex tidak membedakan batas literal string, ia mencocokkan teks `'FROM rahasia'` yang berada di dalam tanda kutip tunggal sebagai klausul `FROM` yang membaca tabel `rahasia`. Regex secara keliru mengeluarkan `('laporan_penjualan.sql', 2, 'rahasia', 'R')` (False Positive).
   - **Mengapa parser benar:**
     Pada fase scanning (Bab 4), fungsi `_string()` di lexer mengenali pembatas tanda kutip dan mengonsumsi seluruh isi teks `'FROM rahasia'` sebagai satu token nilai literal string murni bertipe `TokenType.STRING`. Kata `FROM` di dalamnya tidak diperlakukan sebagai token `KEYWORD`. Selanjutnya pada fase parsing (Bab 6), parser membentuk simpul ekspresi `ast.Literal(value="FROM rahasia")` yang menjadi anak dari operator biner `<>` pada klausa `WHERE`. Analyzer yang menelusuri simpul AST hanya mencari nama tabel pada simpul `TableRef` atau subquery, sehingga isi string literal tidak pernah dianggap sebagai tabel.

3. **Statement Mengandung Kesalahan Sintaks (Kaitannya dengan Konsep Parsing dan Error Recovery):**
   - **Potongan SQL (`campuran_error.sql` baris 4):**
     ```sql
     SELECT id nama, FROM pesanan;
     ```
   - **Kesalahan regex:**
     Regex tidak memvalidasi keabsahan struktur tata bahasa (*syntax analysis*). Regex hanya melihat kemunculan pola `FROM pesanan` di dalam teks dan langsung mengekstraksi `('campuran_error.sql', 4, 'pesanan', 'R')` (False Positive). Padahal menurut `SPESIFIKASI.md` bagian 5, statement yang gagal di-parse tidak boleh dihitung ke dalam matriks CRUD.
   - **Mengapa parser benar:**
     Mengacu pada *Crafting Interpreters Bab 6 (Parsing Expressions)*, parser recursive descent memvalidasi aliran token terhadap aturan tata bahasa (*grammar rules*). Ketika parser membaca koma `,` diikuti langsung oleh keyword `FROM`, parser mendeteksi pelanggaran aturan grammar proyeksi kolom dan melempar `ParseError` (`Baris 4, kolom 17: diharapkan ekspresi, ditemukan 'FROM'`). Sesuai mekanisme *panic mode error recovery* (Bab 6 & `SPESIFIKASI.md` bagian 6), fungsi `_synchronize()` membuang seluruh token statement rusak tersebut hingga tanda titik koma `;` berikutnya, dan statement tersebut tidak dimasukkan ke dalam daftar statement valid `script.statements`. Analyzer hanya memproses statement yang valid pada AST, sehingga tabel `pesanan` pada baris yang rusak ini tidak dihitung.

## 3. Batas pendekatan kami

Minimal tiga hal yang **tidak bisa** ditangani dengan benar oleh tool ini meskipun semua bug
sudah diperbaiki. Untuk tiap batas: contoh SQL atau situasinya, akibatnya pada CRUD matrix,
dan informasi apa yang dibutuhkan untuk mengatasinya.

1. **Ambiguitas Kolom Tanpa Qualifier pada Multi-Table Query Tanpa Akses Skema Fisik:**
   - **Contoh SQL / Situasi:**
     ```sql
     SELECT id, total FROM pelanggan p JOIN pesanan o ON p.id = o.pelanggan_id;
     ```
     Query menggabungkan dua tabel atau lebih, namun kolom yang diproyeksikan (`total`) tidak diberi prefiks qualifier/alias tabel.
   - **Akibat pada CRUD matrix / analisis kolom:**
     Sesuai aturan `SPESIFIKASI.md` bagian 4.3 dan implementasi `crud/resolver.py`, jika scope terdalam memuat lebih dari satu entitas tabel (tabel `p` dan `o`), resolver tidak dapat menebak secara spekulatif kolom `total` milik tabel mana. Resolver menandai kolom dengan `resolved = None` dan memunculkan warning diagnostik `kolom 'total' ambigu tanpa skema`. Akibatnya, pada pelaporan detail penggunaan kolom (`--kolom`), kolom `total` tidak dapat dipetakan ke tabel `pesanan`.
   - **Informasi yang dibutuhkan:**
     Dibutuhkan **Katalog Skema Database (Database Catalog / Schema Metadata DDL)** yang memuat daftar nama kolom fisik dari setiap tabel yang ada di basis data, sehingga resolver dapat memeriksa keberadaan nama kolom pada kamus skema tabel terkait.

2. **Konstruksi SQL Lanjutan di Luar Tata Bahasa Statis (CTE `WITH`, `UNION`, dan `MERGE`):**
   - **Contoh SQL / Situasi:**
     ```sql
     WITH rekap AS (
         SELECT pelanggan_id, SUM(total) AS omzet FROM pesanan GROUP BY pelanggan_id
     )
     SELECT p.nama, r.omzet FROM pelanggan p JOIN rekap r ON p.id = r.pelanggan_id;
     ```
   - **Akibat pada CRUD matrix:**
     Sesuai `SPESIFIKASI.md` bagian 9, fitur CTE (`WITH`), `UNION`, dan `MERGE` berada di luar lingkup (*out of scope*) grammar saat ini. Ketika parser recursive descent membaca token awal `WITH`, parser langsung gagal dengan `ParseError` karena hanya mengantisipasi empat perintah utama (`SELECT`, `INSERT`, `UPDATE`, `DELETE`). Akibatnya, seluruh statement dibuang oleh pemulihan error recovery, dan operasi baca (`R`) pada tabel `pesanan` maupun `pelanggan` sama sekali tidak terdeteksi (False Negative).
   - **Informasi / komponen yang dibutuhkan:**
     Dibutuhkan **Perluasan Tata Bahasa (Grammar Extension)** pada parser untuk mendukung aturan sintaksis `with_clause` dan `union_stmt`, simpul AST baru (`ast.CTE`, `ast.SetOp`), serta kemampuan resolver untuk mendaftarkan nama CTE sebagai *temporary view scope* lokal.

3. **Dynamic SQL dan Eksekusi String Runtime (`EXECUTE` / Stored Procedure):**
   - **Contoh SQL / Situasi:**
     ```sql
     EXECUTE 'UPDATE ' || nama_tabel || ' SET status = ''SELESAI'' WHERE id = ' || id_target;
     ```
   - **Akibat pada CRUD matrix:**
     Tool ini beroperasi secara *static analysis* murni terhadap teks query statis. Sintaks perintah dinamis `EXECUTE` tidak dikenali oleh grammar, dan nama tabel target berada di dalam variabel string (`nama_tabel`) yang baru bernilai saat program dieksekusi di DBMS. Akibatnya, operasi mutasi `U` pada tabel target tidak dapat diekstraksi ke dalam matriks CRUD (False Negative).
   - **Informasi yang dibutuhkan:**
     Dibutuhkan **analisis dinamis (Runtime Tracing / Query Log Monitoring)** atau *taint analysis & data-flow analysis* dari kode aplikasi pemanggil untuk merekonstruksi dan mengevaluasi string SQL sebelum diteruskan ke database engine.

## 4. Pembagian kerja

Siapa mengerjakan apa, dan bagaimana kalian memastikan keduanya memahami seluruh kode.
