import duckdb
import pandas as pd
import numpy as np
import os

def haversine_mesafe(lat1, lon1, lat2, lon2):
    # iki cografi koordinat arasindaki mesafeyi kilometre cinsinden hesaplayan formul
    r = 6371  # dunya yariçapi (km)
    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    delta_phi = np.radians(lat2 - lat1)
    delta_lambda = np.radians(lon2 - lon1)
    
    a = np.sin(delta_phi/2)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda/2)**2
    mesafe = r * (2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a)))
    return np.round(mesafe, 2)

def model_girdilerini_olustur():
    print("veritabanina baglaniliyor ve SQL sorgulari calistiriliyor...")
    conn = duckdb.connect("olist_network.db")
    
    # 1. SQL ile eyalet bazli talebi (teslim edilmis siparislerdeki urun sayisi) buluyoruz
    talep_sorgusu = """
    select 
        c.customer_state as eyalet,
        count(oi.order_item_id) as talep
    from customers c
    join orders o on c.customer_id = o.customer_id
    join order_items oi on o.order_id = oi.order_id
    where o.order_status = 'delivered'
    group by c.customer_state
    order by talep desc
    """
    talep_df = conn.execute(talep_sorgusu).df()
    
    # 2. SQL ile her eyaletin ortalama merkez koordinatini (enlem, boylam) buluyoruz
    koordinat_sorgusu = """
    select 
        geolocation_state as eyalet,
        avg(geolocation_lat) as enlem,
        avg(geolocation_lng) as boylam
    from geolocation
    group by geolocation_state
    """
    koordinat_df = conn.execute(koordinat_sorgusu).df()
    conn.close()
    
    # sql'den gelen iki tabloyu eyalet ismine gore pythonda birlestiriyoruz
    veri_df = pd.merge(talep_df, koordinat_df, on='eyalet', how='inner')
    
    # 3. python ile 27x27 boyutunda bir mesafe matrisi olusturuyoruz
    print("koordinatlar uzerinden mesafe matrisi hesaplaniyor...")
    eyaletler = veri_df['eyalet'].tolist()
    mesafe_matrisi = pd.DataFrame(index=eyaletler, columns=eyaletler)
    
    for i in range(len(veri_df)):
        for j in range(len(veri_df)):
            eyalet1 = veri_df.iloc[i]
            eyalet2 = veri_df.iloc[j]
            mesafe = haversine_mesafe(eyalet1['enlem'], eyalet1['boylam'], 
                                      eyalet2['enlem'], eyalet2['boylam'])
            mesafe_matrisi.iloc[i, j] = mesafe
            
    # sonuclari optimizasyon modelinin okumasi icin data klasorune kaydediyoruz
    veri_df.to_csv("data/talep_ve_koordinat.csv", index=False)
    mesafe_matrisi.to_csv("data/mesafe_matrisi.csv")
    
    print(f"✓ islem tamam! toplam {len(eyaletler)} eyalet icin talep ve mesafe verileri 'data' klasorune kaydedildi.")

if __name__ == "__main__":
    model_girdilerini_olustur()