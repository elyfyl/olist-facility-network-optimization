import duckdb
import os

def veritabanini_hazirla():
    db_name = "olist_network.db"
    conn = duckdb.connect(db_name)
    
    print("DuckDB bağlantısı kuruldu. Optimizasyon parametre tabloları hazırlanıyor...")

    veri_klasoru = "data"

    tables = {
        "customers": "olist_customers_dataset.csv",
        "orders": "olist_orders_dataset.csv",
        "order_items": "olist_order_items_dataset.csv",
        "products": "olist_products_dataset.csv",
        "geolocation": "olist_geolocation_dataset.csv"  # Aday depolar ve mesafe hesabı için kritik
    }

    # Döngü ile tüm dosyaları SQL tablolarına dönüştür
    for table_name, file_name in tables.items():
        # Klasör yolu ile dosya adını birleştiriyoruz (Örn: data/olist_customers_dataset.csv)
        dosya_yolu = os.path.join(veri_klasoru, file_name)
        
        if os.path.exists(dosya_yolu):
            print(f"[{table_name}] tablosu oluşturuluyor...")
            sql_query = f"""
                CREATE OR REPLACE TABLE {table_name} AS 
                SELECT * FROM read_csv_auto('{dosya_yolu}');
            """
            conn.execute(sql_query)
            print(f"✓ [{table_name}] başarıyla aktarıldı.")
        else:
            print(f"HATA: '{dosya_yolu}' bulunamadı. Lütfen CSV'nin '{veri_klasoru}' klasöründe olduğundan emin ol.")

    conn.close()
    print("Veri aktarımı tamamlandı. Tesis yeri seçimi (Facility Location) modeli için veritabanı hazır!")

if __name__ == "__main__":
    veritabanini_hazirla()