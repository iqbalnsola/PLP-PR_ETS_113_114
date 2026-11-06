# Kartu Desain

Tuliskan lima keputusan desain penting dalam pekerjaan kalian. Untuk tiap keputusan, sebutkan
alternatif yang ditolak dan alasannya. Contoh topik (boleh memilih yang lain):

- bagaimana parser membedakan `*` sebagai "semua kolom" dan sebagai perkalian;
- di mana dan bagaimana presedensi `AND`/`OR` dinyatakan;
- mengapa error recovery berhenti di `;`, bukan di keyword `SELECT` berikutnya;
- urutan pencarian scope dan akibatnya pada shadowing serta correlated subquery;
- mengapa kolom tanpa qualifier hanya dilihat di scope terdalam, dan apa kelemahannya;
- bagaimana implementasi `INSERT ... SELECT` atau komentar blok kalian.

| No | Keputusan | Alternatif yang ditolak | Alasan |
| --- | --- | --- | --- |
| 1 | Error recovery berhenti dan lanjut tepat setelah `;` (`_synchronize()` membuang token sampai `SEMICOLON` ikut terbuang). | Berhenti di keyword awal statement berikutnya (`SELECT`, `INSERT`, dst.). | `SELECT` juga muncul di dalam subquery, jadi parser bisa berhenti di tengah statement yang masih rusak dan melaporkan error ganda. Spesifikasi bagian 6 juga menetapkan `;` sebagai batas. |
| 2 | Pencarian qualifier naik dari `self.scope` lewat rantai `parent`, dan entri pertama yang ditemukan dipakai. | Mengumpulkan rantai scope ke list lalu membaliknya (cara lama), atau hanya mencari di scope terdalam. | Naik lewat `parent` menghasilkan shadowing yang benar dan tetap mendukung correlated subquery. Hanya mencari di scope terdalam membuat subquery tidak bisa merujuk alias luar. |
| 3 | | | |
| 4 | | | |
| 5 | | | |
