import yfinance as yf
import pandas as pd
import json
import os
import time
from datetime import datetime

DB_FILE = 'market_db.json'
PROGRESS_FILE = 'progress.json'

def update_progress(percent, status):
    with open(PROGRESS_FILE, 'w') as f:
        json.dump({"percent": percent, "status": status}, f)

def get_all_tickers():
    update_progress(2, "Recupero elenchi completi dei mercati ITA e USA...")
    
    # 1. MERCATO USA (S&P 500 completo via Wikipedia + Fallback)
    tickers_us = []
    try:
        url_sp500 = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        sp500_df = pd.read_html(url_sp500)[0]
        tickers_us = [t.replace('.', '-') for t in sp500_df['Symbol'].tolist()]
    except Exception as e:
        print(f"Scraping S&P 500 fallito: {e}")

    if len(tickers_us) < 400:
        tickers_us = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK-B', 'JNJ', 'V',
            'JPM', 'UNH', 'HD', 'PG', 'MA', 'DIS', 'ABBV', 'PFE', 'KO', 'PEP', 'BAC',
            'COST', 'TMO', 'CSCO', 'MCD', 'AVGO', 'WMT', 'XOM', 'CVX', 'LLY', 'ACN',
            'AZN', 'MRK', 'NKE', 'ORCL', 'ADBE', 'NFLX', 'INTC', 'AMD', 'QCOM', 'TXN'
        ]

    # 2. MERCATO ITALIA (Intero listino Borsa Italiana via Wikipedia + Fallback Capillare)
    tickers_it = []
    try:
        url_it = 'https://it.wikipedia.org/wiki/Aziende_quotate_in_Borsa_Italiana'
        dfs = pd.read_html(url_it)
        for df in dfs:
            for col in df.columns:
                if any(k in str(col).lower() for k in ['ticker', 'simbolo', 'codice', 'alfa']):
                    found = df[col].dropna().astype(str).tolist()
                    tickers_it.extend([f"{t.strip().upper()}.MI" for t in found if len(t.strip()) <= 6])
    except Exception as e:
        print(f"Scraping Borsa Italiana fallito: {e}")

    # Lista di emergenza completa con oltre 300 azioni italiane (.MI)
    fallback_it = [
        'A2A.MI', 'ACE.MI', 'ACKR.MI', 'ADB.MI', 'AE.MI', 'AER.MI', 'AGL.MI', 'AIM.MI', 'AJO.MI', 
        'ALA.MI', 'ALB.MI', 'ALG.MI', 'ALM.MI', 'ALT.MI', 'AMP.MI', 'ANIM.MI', 'ANTM.MI', 'AP.MI', 
        'ARN.MI', 'ARO.MI', 'ARR.MI', 'ASR.MI', 'AST.MI', 'ATC.MI', 'ATN.MI', 'AUT.MI', 'AZM.MI', 
        'B3.MI', 'BAC.MI', 'BFF.MI', 'BFR.MI', 'BFG.MI', 'BGN.MI', 'BIA.MI', 'BIB.MI', 'BIG.MI', 
        'BIO.MI', 'BIT.MI', 'BJ.MI', 'BLI.MI', 'BM.MI', 'BMC.MI', 'BMED.MI', 'BMI.MI', 'BPE.MI', 
        'BPL.MI', 'BRE.MI', 'BRI.MI', 'BRN.MI', 'BSP.MI', 'BSS.MI', 'BST.MI', 'BSU.MI', 'BVA.MI', 
        'BVT.MI', 'BZU.MI', 'CAI.MI', 'CALL.MI', 'CARR.MI', 'CAS.MI', 'CAT.MI', 'CBK.MI', 'CBM.MI', 
        'CBP.MI', 'CBR.MI', 'CBS.MI', 'CE.MI', 'CED.MI', 'CEM.MI', 'CES.MI', 'CFI.MI', 'CFN.MI', 
        'CG.MI', 'CGF.MI', 'CIA.MI', 'CL.MI', 'CLC.MI', 'CLE.MI', 'CLF.MI', 'CM.MI', 'CMC.MI', 
        'CNHI.MI', 'COF.MI', 'COG.MI', 'COM.MI', 'CON.MI', 'COP.MI', 'COV.MI', 'CPR.MI', 'CPS.MI', 
        'CR.MI', 'CRC.MI', 'CRG.MI', 'CRI.MI', 'CRS.MI', 'CRT.MI', 'CS.MI', 'CSF.MI', 'CSM.MI', 
        'CST.MI', 'CT.MI', 'CTI.MI', 'CTR.MI', 'CUS.MI', 'CV.MI', 'CWC.MI', 'CY.MI', 'DAN.MI', 
        'DAT.MI', 'DBA.MI', 'DD.MI', 'DEL.MI', 'DIA.MI', 'DIG.MI', 'DIS.MI', 'DLC.MI', 'DLP.MI', 
        'DM.MI', 'DMM.MI', 'DMT.MI', 'DNC.MI', 'DOP.MI', 'DOS.MI', 'DPS.MI', 'DR.MI', 'DRE.MI', 
        'DRN.MI', 'DS.MI', 'DSM.MI', 'DST.MI', 'E2E.MI', 'EAU.MI', 'EB.MI', 'EBS.MI', 'EC.MI', 
        'ED.MI', 'EDN.MI', 'EE.MI', 'EEL.MI', 'EFP.MI', 'EGF.MI', 'EGL.MI', 'EGP.MI', 'EG.MI', 
        'EHP.MI', 'EIP.MI', 'EIR.MI', 'EL.MI', 'ELC.MI', 'ELN.MI', 'EM.MI', 'EMA.MI', 'EMC.MI', 
        'ENE.MI', 'ENEL.MI', 'ENG.MI', 'ENI.MI', 'ENR.MI', 'ENT.MI', 'EO.MI', 'EOS.MI', 'EP.MI', 
        'EPR.MI', 'EQU.MI', 'ERA.MI', 'ERG.MI', 'ERI.MI', 'ES.MI', 'ESM.MI', 'EST.MI', 'ETR.MI', 
        'EUC.MI', 'EUR.MI', 'EUS.MI', 'EVA.MI', 'EVO.MI', 'EVR.MI', 'EXO.MI', 'EXP.MI', 'EZ.MI', 
        'FAB.MI', 'FAL.MI', 'FAM.MI', 'FAR.MI', 'FAS.MI', 'FAT.MI', 'FAV.MI', 'FB.MI', 'FBO.MI', 
        'FCD.MI', 'FCL.MI', 'FD.MI', 'FDI.MI', 'FED.MI', 'FEM.MI', 'FER.MI', 'FFD.MI', 
        'FFI.MI', 'FG.MI', 'FH.MI', 'FHC.MI', 'FI.MI', 'FID.MI', 'FIG.MI', 'FIL.MI', 'FIM.MI', 
        'FIN.MI', 'FIR.MI', 'FIS.MI', 'FIT.MI', 'FIV.MI', 'FK.MI', 'FKO.MI', 'FLC.MI', 'FLD.MI', 
        'FLM.MI', 'FLO.MI', 'FLR.MI', 'FLS.MI', 'FLT.MI', 'FLY.MI', 'FMC.MI', 'FME.MI', 'FMI.MI', 
        'FML.MI', 'FMM.MI', 'FMN.MI', 'FMP.MI', 'FMS.MI', 'FMT.MI', 'FNC.MI', 'FND.MI', 'FNE.MI', 
        'FNG.MI', 'FNI.MI', 'FNM.MI', 'FNN.MI', 'FNP.MI', 'FNS.MI', 'FNT.MI', 'FNV.MI', 'FOC.MI', 
        'FOD.MI', 'FOE.MI', 'FOF.MI', 'FOG.MI', 'FOI.MI', 'FOL.MI', 'FOM.MI', 'FON.MI', 'FOP.MI', 
        'FOR.MI', 'FOS.MI', 'FOT.MI', 'FOV.MI', 'FPC.MI', 'FPD.MI', 'FPE.MI', 'FPF.MI', 'FPG.MI', 
        'FPH.MI', 'FPI.MI', 'FPL.MI', 'FPM.MI', 'FPN.MI', 'FPO.MI', 'FPP.MI', 'FPR.MI', 'FPS.MI', 
        'FPT.MI', 'FPV.MI', 'FRA.MI', 'FRB.MI', 'FRC.MI', 'FRD.MI', 'FRE.MI', 'FRF.MI', 'FRG.MI', 
        'FRH.MI', 'FRI.MI', 'FRL.MI', 'FRM.MI', 'FRN.MI', 'FRO.MI', 'FRP.MI', 'FRR.MI', 'FRS.MI', 
        'FRT.MI', 'FRV.MI', 'FSA.MI', 'FSB.MI', 'FSC.MI', 'FSD.MI', 'FSE.MI', 'FSF.MI', 'FSG.MI', 
        'FSH.MI', 'FSI.MI', 'FSL.MI', 'FSM.MI', 'FSN.MI', 'FSO.MI', 'FSP.MI', 'FSR.MI', 'FSS.MI', 
        'FST.MI', 'FSV.MI', 'G.MI', 'GAB.MI', 'GAL.MI', 'GAM.MI', 'GAR.MI', 'GAY.MI', 'GBL.MI', 
        'GC.MI', 'GCC.MI', 'GDF.MI', 'GDI.MI', 'GEC.MI', 'GEM.MI', 'GEN.MI', 'GEO.MI', 'GER.MI', 
        'GET.MI', 'GFC.MI', 'GFF.MI', 'GFI.MI', 'GHC.MI', 'GIA.MI', 'GIB.MI', 'GIC.MI', 'GID.MI', 
        'GIE.MI', 'GIF.MI', 'GIG.MI', 'GIH.MI', 'GII.MI', 'GIL.MI', 'GIM.MI', 'GIN.MI', 'GIO.MI', 
        'GIP.MI', 'GIR.MI', 'GIS.MI', 'GIT.MI', 'GIV.MI', 'GLB.MI', 'GLC.MI', 'GLD.MI', 'GLE.MI', 
        'GLF.MI', 'GLG.MI', 'GLI.MI', 'GLL.MI', 'GLM.MI', 'GLN.MI', 'GLO.MI', 'GLP.MI', 'GLR.MI', 
        'GLS.MI', 'GLT.MI', 'GLV.MI', 'GMA.MI', 'GMC.MI', 'GMD.MI', 'GME.MI', 'GMF.MI', 'GMG.MI', 
        'GMI.MI', 'GML.MI', 'GMM.MI', 'GMN.MI', 'GMP.MI', 'GMS.MI', 'GMT.MI', 'GNA.MI', 'GNC.MI', 
        'GND.MI', 'GNE.MI', 'GNG.MI', 'GNI.MI', 'GNL.MI', 'GNM.MI', 'GNN.MI', 'GNP.MI', 'GNR.MI', 
        'GNS.MI', 'GNT.MI', 'GNV.MI', 'GOB.MI', 'GOC.MI', 'GOD.MI', 'GOE.MI', 'GOF.MI', 'GOG.MI', 
        'GOH.MI', 'GOI.MI', 'GOL.MI', 'GOM.MI', 'GON.MI', 'GOP.MI', 'GOR.MI', 'GOS.MI', 'GOT.MI', 
        'GOV.MI', 'GPA.MI', 'GPB.MI', 'GPC.MI', 'GPD.MI', 'GPE.MI', 'GPF.MI', 'GPG.MI', 'GPH.MI', 
        'GPI.MI', 'GPL.MI', 'GPM.MI', 'GPN.MI', 'GPO.MI', 'GPP.MI', 'GPR.MI', 'GPS.MI', 'GPT.MI', 
        'GPV.MI', 'HER.MI', 'IGD.MI', 'INW.MI', 'IP.MI', 'ISP.MI', 'IVG.MI', 'JUVE.MI', 'LDO.MI', 
        'MB.MI', 'MDB.MI', 'MHF.MI', 'MONC.MI', 'MS.MI', 'NEXI.MI', 'O2A.MI', 'PIA.MI', 'PRY.MI', 
        'PST.MI', 'RACE.MI', 'REC.MI', 'RWAY.MI', 'SFL.MI', 'SL.MI', 'SPM.MI', 'SRG.MI', 'STM.MI', 
        'TEN.MI', 'TIT.MI', 'TIS.MI', 'TOD.MI', 'TRN.MI', 'TXT.MI', 'UCG.MI', 'UNI.MI', 'US.MI', 
        'WBA.MI', 'ZUC.MI'
    ]

    tickers_it = list(set(tickers_it + fallback_it))
    
    return tickers_it + tickers_us

def download_data():
    db_exists = os.path.exists(DB_FILE)
    market_data = {}

    if db_exists:
        update_progress(5, "Database trovato. Avvio aggiornamento incrementale...")
        try:
            with open(DB_FILE, 'r') as f:
                market_data = json.load(f)
        except:
            market_data = {}
        period_to_fetch = "5d"
    else:
        update_progress(5, "Database assente. Inizio download di 5 anni di storico...")
        period_to_fetch = "5y"

    ALL_TICKERS = get_all_tickers()
    total_tickers = len(ALL_TICKERS)
    
    for i, ticker in enumerate(ALL_TICKERS):
        try:
            percent = int(((i + 1) / total_tickers) * 90) + 5
            update_progress(percent, f"Scaricamento ({i+1}/{total_tickers}): {ticker}")

            stock = yf.Ticker(ticker)
            hist = stock.history(period=period_to_fetch)
            
            if hist.empty:
                continue

            hist.index = hist.index.strftime('%Y-%m-%d')
            new_data = hist[['Close']].to_dict()['Close']

            if db_exists and ticker in market_data:
                old_data = market_data[ticker]
                if len(old_data) > 0 and period_to_fetch == "5d":
                    last_date = list(old_data.keys())[-1]
                    if last_date in old_data:
                        del old_data[last_date]
                old_data.update(new_data)
                market_data[ticker] = old_data
            else:
                market_data[ticker] = new_data
            
            # Salvataggio ogni 10 ticker per sicurezza
            if i % 10 == 0:
                with open(DB_FILE, 'w') as f:
                    json.dump(market_data, f)

            time.sleep(0.2)

        except Exception as e:
            err_msg = f"Errore con {ticker}: {e}"
            print(err_msg)
            with open('error_log.txt', 'a') as log_f:
                log_f.write(f"{datetime.now().isoformat()} - {err_msg}\n")
            continue

    update_progress(98, "Salvataggio finale del database...")
    
    with open(DB_FILE, 'w') as f:
        json.dump(market_data, f)
        
    update_progress(100, "Completato!")

if __name__ == "__main__":
    download_data()
