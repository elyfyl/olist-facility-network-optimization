import pandas as pd
import gurobipy as gp
from gurobipy import GRB
import folium
import os

def optimizasyon_ve_haritalama():
    print("veriler okunuyor...")
    talep_df = pd.read_csv("data/talep_ve_koordinat.csv")
    mesafe_df = pd.read_csv("data/mesafe_matrisi.csv", index_col=0)

    eyaletler = talep_df['eyalet'].tolist()
    talepler = dict(zip(talep_df['eyalet'], talep_df['talep']))
    koordinatlar = {row['eyalet']: (row['enlem'], row['boylam']) for _, row in talep_df.iterrows()}

    # parametreler
    sabit_depo_maliyeti = 500000
    birim_nakliye_maliyeti = 0.5
    maksimum_kapasite = 20000  # yeni eklenen kapasite limiti

    # 1. gurobi modelini kur
    m = gp.Model("Olist_Kapasiteli_Ag_Gorsellestirme")
    m.setParam('OutputFlag', 0) 

    y = m.addVars(eyaletler, vtype=GRB.BINARY, name="depo_ac")
    x = m.addVars(eyaletler, eyaletler, vtype=GRB.CONTINUOUS, name="gonderim")

    # kısıt 1: talepler karşılansın
    for i in eyaletler:
        m.addConstr(gp.quicksum(x[i, j] for j in eyaletler) == talepler[i])
        
    # --- KISIT 2: DEPO ÇIKIŞ SINIRI ---
    for j in eyaletler:
        # İLK AŞAMA : Sınırsız kapasite varsayımı.
        # Sadece "depo kapalıysa (y=0) ürün gönderilemez" diyorduk.
        # for i in eyaletler:
        #     m.addConstr(x[i, j] <= talepler[i] * y[j])

        # ŞİMDİKİ AŞAMA: Kapasite sınırı.
        # Bir deponun tüm eyaletlere gönderdiği toplam ürün sayısı, maksimum kapasiteyi aşamaz.
        m.addConstr(gp.quicksum(x[i, j] for i in eyaletler) <= maksimum_kapasite * y[j])

    # amaç fonksiyonu
    toplam_sabit = gp.quicksum(sabit_depo_maliyeti * y[j] for j in eyaletler)
    toplam_nakliye = gp.quicksum(birim_nakliye_maliyeti * mesafe_df.loc[i, j] * x[i, j] for i in eyaletler for j in eyaletler)
    m.setObjective(toplam_sabit + toplam_nakliye, GRB.MINIMIZE)
    
    print("kapasiteli model cözülüyor...")
    m.optimize()

    # 2. atama sonuclarini ayikla
    atamalar = []
    acilan_depolar = [j for j in eyaletler if y[j].X > 0.5]

    for i in eyaletler:
        for j in eyaletler:
            gonderilen = x[i, j].X
            if gonderilen > 0.01: 
                atamalar.append({
                    "talep_eyaleti": i,
                    "tedarikci_depo": j,
                    "gonderilen_miktar": round(gonderilen, 2)
                })

    atama_df = pd.DataFrame(atamalar)
    atama_df.to_csv("data/kapasiteli_depo_atamalari.csv", index=False)

    # 3. folium haritasi
    print("harita ciziliyor...")
    harita = folium.Map(
        location=[-14.2350, -51.9253], 
        zoom_start=4, 
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
        attr='Tiles &copy; Esri'
    )

    for eyalet in eyaletler:
        nokta = koordinatlar[eyalet]
        if eyalet in acilan_depolar:
            folium.Marker(
                location=nokta,
                popup=f"DEPO: {eyalet} (Kapasiteli)",
                icon=folium.Icon(color="red", icon="home")
            ).add_to(harita)
        else:
            folium.CircleMarker(
                location=nokta,
                radius=5,
                color="blue",
                fill=True,
                fill_color="blue",
                popup=f"Talep Noktasi: {eyalet} ({talepler[eyalet]} siparis)"
            ).add_to(harita)

    for _, row in atama_df.iterrows():
        i = row['talep_eyaleti']
        j = row['tedarikci_depo']
        if i != j: 
            cizgi_noktalari = [koordinatlar[j], koordinatlar[i]]
            folium.PolyLine(
                locations=cizgi_noktalari,
                color="orange", 
                weight=2,
                opacity=0.8,
                dash_array="5, 5"
            ).add_to(harita)

    if not os.path.exists("images"):
        os.makedirs("images")

    harita_yolu = "images/capacitated_network_map.html"
    harita.save(harita_yolu)
    print(f"✓ interaktif kapasiteli lojistik haritasi '{harita_yolu}' olarak kaydedildi!")

if __name__ == "__main__":
    optimizasyon_ve_haritalama()