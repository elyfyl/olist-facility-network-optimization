import pandas as pd
import gurobipy as gp
from gurobipy import GRB

def tesis_yeri_modelini_coz():
    print("Veriler yükleniyor...")
    talep_df = pd.read_csv("data/talep_ve_koordinat.csv")
    mesafe_df = pd.read_csv("data/mesafe_matrisi.csv", index_col=0) # index_col=0 satır isimlerini eyalet yapar

    # Eyalet listesini ve talep sözlüğünü oluşturuyoruz
    eyaletler = talep_df['eyalet'].tolist()
    talepler = dict(zip(talep_df['eyalet'], talep_df['talep']))

    # Senaryo Parametreleri (analizler bu parametreler üzerinden yapılacak) 
    sabit_depo_maliyeti = 500000  # Her bir deponun kurulum maliyeti
    birim_nakliye_maliyeti = 0.5  # 1 birim ürünü 1 km taşımanın maliyeti
    maksimum_kapasite = 20000  # YENİ: Bir deponun işleyebileceği maksimum sipariş

    # 1. Gurobi Modelini Başlat
    m = gp.Model("Olist_Tesis_Yeri_Secimi")

    # 2. Karar Değişkenlerini Tanımla
    # y[j]: j eyaletine depo açılırsa 1, açılmazsa 0
    y = m.addVars(eyaletler, vtype=GRB.BINARY, name="depo_ac")

    # x[i, j]: j deposundan i eyaletine gönderilen ürün miktarı
    x = m.addVars(eyaletler, eyaletler, vtype=GRB.CONTINUOUS, name="gonderim")

    # 3. Kısıtları Ekle
    print("Model kısıtları ve amaç fonksiyonu oluşturuluyor...")
    
    # Kısıt 1: Her eyaletin (i) talebi tam olarak karşılanmalıdır
    for i in eyaletler:
        m.addConstr(gp.quicksum(x[i, j] for j in eyaletler) == talepler[i], name=f"talep_karsilama_{i}")

    # Kısıt 2: Mantıksal kısıt - Kapalı depodan gönderim yapılamaz
    # j deposundan tüm i eyaletlerine çıkan ürünlerin toplamı, o deponun kapasitesini aşamaz.
    # Eğer y[j] = 0 ise (depo açılmazsa), kapasite de 0 olur ve gönderim yapılamaz.
    for j in eyaletler:
        m.addConstr(gp.quicksum(x[i, j] for i in eyaletler) <= maksimum_kapasite * y[j], name=f"kapasite_siniri_{j}")
   
    # 4. Amaç Fonksiyonunu Belirle (Maliyet Minimizasyonu)
    toplam_sabit_maliyet = gp.quicksum(sabit_depo_maliyeti * y[j] for j in eyaletler)
    toplam_nakliye_maliyeti = gp.quicksum(birim_nakliye_maliyeti * mesafe_df.loc[i, j] * x[i, j] for i in eyaletler for j in eyaletler)

    m.setObjective(toplam_sabit_maliyet + toplam_nakliye_maliyeti, GRB.MINIMIZE)

    # 5. Modeli Çöz
    print("Optimizasyon başlatılıyor...\n")
    m.optimize()

# 6. Detaylı Sonuç Raporlama
    if m.Status == GRB.OPTIMAL:
        print("\n--- KAPASİTELİ MODEL OPTİMAL ÇÖZÜMÜ ---")
        print(f"Toplam Minimum Maliyet: {m.ObjVal:,.2f}")
        
        acilan_depolar = [j for j in eyaletler if y[j].X > 0.5]
        print(f"\nAçılması Önerilen Depolar ({len(acilan_depolar)} adet) ve Doluluk Oranları:")
        
        for j in acilan_depolar:
            # İlgili depodan çıkan toplam ürün miktarını hesapla
            toplam_gonderim = sum(x[i, j].X for i in eyaletler)
            doluluk_orani = (toplam_gonderim / maksimum_kapasite) * 100
            print(f"- {j} Eyaleti: {toplam_gonderim:,.0f} sipariş (Doluluk: %{doluluk_orani:.1f})")
                
    else:
        print("Optimal çözüm bulunamadı. Model durumu:", m.Status)

if __name__ == "__main__":
    tesis_yeri_modelini_coz()