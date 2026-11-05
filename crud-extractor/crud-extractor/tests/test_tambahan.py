"""Test tambahan buatan kelompok.

Isi dengan:
1. Satu test regresi untuk setiap bug yang kalian perbaiki (gagal sebelum perbaikan,
   lulus sesudahnya). Beri nama yang menjelaskan bug-nya.
2. Lima test kasus tepi, masing-masing dengan komentar singkat mengapa kasus itu berisiko.
"""
import pytest
from crud.lexer import LexError, Token, TokenType as T, tokenize


# ==============================================================================
# 1. TEST REGRESI BUG LEXER
# ==============================================================================

def test_regresi_keyword_case_insensitive_dan_ident():
    """Bug: Keyword huruf kecil/campuran tidak dinormalisasi ke UPPERCASE dan
    salah dikenali sebagai IDENT. SPESIFIKASI.md 2.2."""
    toks = tokenize("select DISTINCT From WhErE selection fromage")
    # Keyword harus dinormalisasi ke huruf besar
    assert toks[0].type == T.KEYWORD and toks[0].value == "SELECT"
    assert toks[1].type == T.KEYWORD and toks[1].value == "DISTINCT"
    assert toks[2].type == T.KEYWORD and toks[2].value == "FROM"
    assert toks[3].type == T.KEYWORD and toks[3].value == "WHERE"
    # Kata yang hanya diawali keyword harus tetap IDENT
    assert toks[4].type == T.IDENT and toks[4].value == "selection"
    assert toks[5].type == T.IDENT and toks[5].value == "fromage"


def test_regresi_operator_maximal_munch_tidak_sama_dengan():
    """Bug: Operator <> dipecah menjadi dua token (< lalu >) alih-alih satu token OP.
    SPESIFIKASI.md 2.5."""
    toks = tokenize("a <> b")
    assert [t.type for t in toks[:3]] == [T.IDENT, T.OP, T.IDENT]
    assert [t.value for t in toks[:3]] == ["a", "<>", "b"]


def test_regresi_string_escape_quote():
    """Bug: Dua kutip berturut-turut ('') memotong string sebelum waktunya.
    Seharusnya merepresentasikan satu karakter kutip di dalam string. SPESIFIKASI.md 2.4."""
    toks = tokenize("'O''Brien' ''''")
    assert toks[0].type == T.STRING and toks[0].value == "O'Brien"
    assert toks[1].type == T.STRING and toks[1].value == "'"


def test_regresi_komentar_blok_todo_t3():
    """TODO(T3): Komentar blok /* ... */ belum didukung dan melempar LexError.
    Harus diabaikan dan melacak posisi baris dengan benar. SPESIFIKASI.md 2.3."""
    src = "/* baris 1\n   baris 2 * bintang */ SELECT id"
    toks = tokenize(src)
    assert len(toks) == 3  # SELECT, id, EOF
    assert toks[0].type == T.KEYWORD and toks[0].value == "SELECT"
    assert toks[0].line == 2


# ==============================================================================
# 2. TEST KASUS TEPI (EDGE CASES)
# ==============================================================================

# Kasus tepi 1: String tidak ditutup karena diakhiri escape quote tepat sebelum EOF.
# Berisiko: Lexer bisa saja terkecoh menganggap kutip terakhir sebagai penutup string.
def test_kasus_tepi_string_escape_tidak_ditutup_eof():
    with pytest.raises(LexError) as exc_info:
        tokenize("'teks tidak berujung''")
    assert exc_info.value.line == 1 and exc_info.value.col == 1


# Kasus tepi 2: Komentar blok yang tidak ditutup sampai EOF.
# Berisiko: Lexer masuk loop tanpa henti atau lupa melempar LexError sesuai SPESIFIKASI 2.3.
def test_kasus_tepi_komentar_blok_tidak_ditutup():
    with pytest.raises(LexError) as exc_info:
        tokenize("SELECT 1; /* komentar tanpa penutup...")
    assert exc_info.value.line == 1 and exc_info.value.col == 11


# Kasus tepi 3: String kosong murni ('').
# Berisiko: Logika escape bisa salah mengonsumsi kutip kedua dan menunggu kutip penutup ketiga.
def test_kasus_tepi_string_kosong():
    toks = tokenize("''")
    assert toks[0].type == T.STRING and toks[0].value == ""


# Kasus tepi 4: Komentar blok dengan deretan bintang berurutan (/*** ... ***/).
# Berisiko: Karakter bintang ganda bisa membingungkan deteksi pasangan '* /'.
def test_kasus_tepi_komentar_blok_bintang_berurutan():
    toks = tokenize("/*** header komentar ***/ SELECT")
    assert toks[0].type == T.KEYWORD and toks[0].value == "SELECT"


# Kasus tepi 5: Operator berhimpitan tanpa spasi (a<>b<=c).
# Berisiko: Maximal munch gagal membedakan identifier dengan operator jika tidak ada pemisah whitespace.
def test_kasus_tepi_operator_menempel():
    toks = tokenize("a<>b<=c")
    assert [t.value for t in toks if t.type != T.EOF] == ["a", "<>", "b", "<=", "c"]

# ==============================================================================
# 3. TEST REGRESI PARSER
# ==============================================================================

from crud import ast_nodes as ast
from crud.parser import parse_sql

def test_regresi_insert_select_didukung():
    script = parse_sql("INSERT INTO arsip (id) SELECT id FROM pesanan")
    assert script.errors == []
    stmt = script.statements[0]
    assert isinstance(stmt.query, ast.Select) and stmt.values == []

def test_regresi_error_recovery_sampai_titik_koma():
    script = parse_sql("SELECT FROM; SELECT id FROM t; DELETE FROM x")
    assert len(script.errors) == 1
    assert len(script.statements) == 2

def test_regresi_presedensi_and_lebih_tinggi_dari_or():
    where = parse_sql("SELECT a FROM t WHERE a = 1 OR b = 2 AND c = 3").statements[0].where
    assert where.op == "OR" and where.right.op == "AND"

def test_regresi_left_outer_join_didukung():
    script = parse_sql("SELECT a FROM t LEFT OUTER JOIN u ON u.x = t.x")
    assert script.errors == []
    assert script.statements[0].joins[0].kind == "LEFT"
