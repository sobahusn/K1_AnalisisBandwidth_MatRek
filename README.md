# K1_AnalisisBandwidth_MatRek

Aplikasi web interaktif berbasis Python dan Streamlit untuk Mini Research Matematika Rekayasa **Kelompok 1**: analisis total transfer data jaringan berdasarkan luas di bawah kurva laju bandwidth terhadap waktu $B(t)$.

## Konteks Masalah & Tujuan

Laju transfer data jaringan berubah terhadap waktu mengikuti beban trafik. Jika laju transfer dinyatakan sebagai fungsi $B(t)$, total volume data yang berpindah selama selang waktu $[a, b]$ adalah luas daerah di bawah kurva:

$$V_{\text{total}} = \int_{a}^{b} B(t)\,dt$$

Tujuan proyek ini adalah membangun model fungsi kontinu $B(t)$, menghitung akumulasi total transfer data (MB/GB) secara analitis, dan membandingkannya dengan pendekatan numerik Python (Aturan Trapesium dan Simpson).

## Pemetaan Alur Kerja & Hasil yang Diharapkan

| Hasil yang Diharapkan                      | Implementasi di Aplikasi                                                            |
| :----------------------------------------- | :---------------------------------------------------------------------------------- |
| Tabel data bandwidth                       | `pages/1_Eksplorasi_Data.py` (editor tabel & unggah CSV/XLSX)                       |
| Grafik laju transfer terhadap waktu        | `pages/2_Model_Integral.py` & `core/plotting.py`                                    |
| Model fungsi kontinu $B(t)$                | `pages/2_Model_Integral.py` & `core/fitting.py`                                     |
| Hasil total transfer data (MB/GB)          | `pages/2_Model_Integral.py` & `core/calculus.py`                                    |
| Kode Python & validasi numerik             | `pages/4_Simulasi_Skenario.py` (Analitis vs. Trapesium & Simpson)                   |
| Penjelasan makna luas & keterbatasan model | `pages/0_Beranda.py`, `pages/4_Simulasi_Skenario.py`, & `pages/5_Ekspor_Laporan.py` |

## Transparansi Sumber Data (Simulasi vs. Data Nyata)

Sesuai pedoman etika akademik, seluruh berkas di folder `data/` diklasifikasikan secara eksplisit:

| Berkas                        | Kategori                     | Keterangan & Sumber                                                                                                                                                 |
| :---------------------------- | :--------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `data/simulasi_panduan.csv`   | **Data Simulasi**            | 7 titik waktu sintetik untuk verifikasi perhitungan manual dan model polinomial.                                                                                    |
| `data/dataset_publik_isp.csv` | **Data Simulasi / Cuplikan** | 13 titik pola trafik harian 24 jam. _(Ganti dengan data mentah dari Chorus/M-Lab/CESNET dan cantumkan tautan resminya di sini saat digunakan untuk laporan akhir)._ |
| `data/pengukuran_lokal.csv`   | **Data Contoh Pengukuran**   | 11 titik sampel unduhan lokal. Untuk data nyata perangkat sendiri, gunakan fitur **3. Live Capture** (`psutil`).                                                    |

## Interpretasi Satuan & Keterbatasan Model

- **Makna luas di bawah kurva:** Jika $B(t)$ bersatuan `MB/s` dan $t$ dalam `detik`, hasil integral langsung bersatuan `MB`. Jika $B(t)$ dalam `Mbps` dan $t$ dalam `detik`, hasil integral bersatuan `Megabit (Mb)` lalu dibagi `8` untuk memperoleh `MB` (konvensi desimal: $1\text{ GB} = 1000\text{ MB}$).
- **Keterbatasan model:** Regresi polinomial mengasumsikan laju transfer kontinu, berisiko _overfitting_ pada derajat tinggi, dan tidak sah digunakan untuk ekstrapolasi jauh di luar rentang pengamatan $[a, b]$.

## Etika Akademik & Reproduksibilitas

- Seluruh perhitungan analitis (SymPy) dan numerik (SciPy) dapat diverifikasi ulang langsung dari kode sumber di folder `core/`.
- Data simulasi dan data hasil pengukuran langsung dipisahkan secara tegas tanpa fabrikasi hasil pengukuran.

## Instalasi dan Menjalankan Aplikasi

```bash
cd K1_AnalisisBandwidth_MatRek
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```
