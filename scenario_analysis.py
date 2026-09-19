import pandas as pd
import gurobipy as gp
from gurobipy import GRB

def senaryo_analizini_coz():
    print("veriler yukleniyor...")
    talep_df = pd.read_csv("data/talep_ve_koordinat.csv")
    mesafe_df = pd.read_csv("data/mesafe_matrisi.csv", index_col=0) 

    eyaletler = talep_df['eyalet'].tolist()
    # bu senaryoda talepleri normal birakiyoruz, sokumuz maliyet uzerinden olacak
    talepler = dict(zip(talep_df['eyalet'], talep_df['talep']))

    # --- YENİ SENARYO PARAMETRELERİ ---
    sabit_depo_maliyeti = 500000  
    maksimum_kapasite = 20000  
    
    # İLK AŞAMA (YORUMA ALINDI): Normal dönemdeki nakliye masrafı
    # birim_nakliye_maliyeti = 0.5  

    # ŞİMDİKİ AŞAMA (AKTİF KOD): Yakıt şoku senaryosu! Nakliye maliyeti 3 katına çıktı.
    birim_nakliye_maliyeti = 1.5  

    # 1. gurobi modelini baslat
    m = gp.Model("Olist_Maliyet_Soku_Senaryosu")
    m.setParam('OutputFlag', 0) 

    # 2. karar degiskenleri
    y = m.addVars(eyaletler, vtype=GRB.BINARY, name="depo_ac")
    x = m.addVars(eyaletler, eyaletler, vtype=GRB.CONTINUOUS, name="gonderim")

    # 3. kisitlar
    for i in eyaletler:
        m.addConstr(gp.quicksum(x[i, j] for j in eyaletler) == talepler[i])

    for j in eyaletler:
        m.addConstr(gp.quicksum(x[i, j] for i in eyaletler) <= maksimum_kapasite * y[j])

    # 4. amac fonksiyonu
    toplam_sabit = gp.quicksum(sabit_depo_maliyeti * y[j] for j in eyaletler)
    toplam_nakliye = gp.quicksum(birim_nakliye_maliyeti * mesafe_df.loc[i, j] * x[i, j] for i in eyaletler for j in eyaletler)
    m.setObjective(toplam_sabit + toplam_nakliye, GRB.MINIMIZE)

    # 5. modeli coz
    print(f"senaryo: yakit soku! birim nakliye maliyeti {birim_nakliye_maliyeti} olarak guncellendi.")
    print("model cozuluyor...\n")
    m.optimize()

    # 6. raporlama
    if m.Status == GRB.OPTIMAL:
        print("--- YAKIT ŞOKU SENARYOSU SONUCU ---")
        print(f"Yeni toplam minimum maliyet: {m.ObjVal:,.2f}")
        
        acilan_depolar = [j for j in eyaletler if y[j].X > 0.5]
        print(f"\nİhtiyaç duyulan yeni depo sayısı: {len(acilan_depolar)}")
        
        for j in acilan_depolar:
            toplam_gonderim = sum(x[i, j].X for i in eyaletler)
            doluluk_orani = (toplam_gonderim / maksimum_kapasite) * 100
            print(f"- {j} eyaleti: {toplam_gonderim:,.0f} siparis (doluluk: %{doluluk_orani:.1f})")
            
if __name__ == "__main__":
    senaryo_analizini_coz()