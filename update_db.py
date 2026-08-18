import yfinance as yf
import pandas as pd
import json
import os
import time
import urllib.request
from datetime import datetime

DB_FILE = 'market_db.json'
PROGRESS_FILE = 'progress.json'
LOG_FILE = 'error_log.txt'
BATCH_SIZE = 50 

def update_progress(percent, status, extra_data=None):
    data = {"percent": percent, "status": status}
    if extra_data:
        data.update(extra_data)
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(data, f)

def log_error(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{timestamp}] {message}\n")

def clean_ticker(symbol):
    if not symbol:
        return ""
    return str(symbol).replace('$', '').strip()

def get_all_tickers():
    update_progress(2, "Caricamento elenchi completi USA ed Italia...")
    
    # 1. MERCATO USA COMPLETO (SEC Registro Ufficiale)
    tickers_us = []
    try:
        req = urllib.request.Request(
            'https://www.sec.gov/files/company_tickers.json',
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        with urllib.request.urlopen(req) as response:
            sec_data = json.loads(response.read().decode())
            for item in sec_data.values():
                symbol = clean_ticker(item['ticker']).replace('.', '-')
                if symbol:
                    tickers_us.append(symbol)
    except Exception as e:
        log_error(f"Errore recupero SEC USA: {e}")

    if not tickers_us:
        try:
            url_sp500 = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
            req = urllib.request.Request(
                url_sp500,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            with urllib.request.urlopen(req) as response:
                sp500_df = pd.read_html(response)[0]
                tickers_us = [clean_ticker(t).replace('.', '-') for t in sp500_df['Symbol'].tolist()]
        except Exception as e:
            log_error(f"Errore recupero Wikipedia S&P500: {e}")
            tickers_us = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA']

    # 2. MERCATO ITALIA COMPLETO (~380+ Titoli Borsa Italiana)
    tickers_it_raw = [
        'A2A.MI', 'ACE.MI', 'ACKR.MI', 'ADB.MI', 'AEF.MI', 'AER.MI', 'AGL.MI', 'AIM.MI', 'AJO.MI', 'ALA.MI', 
        'ALB.MI', 'ALG.MI', 'ALM.MI', 'ALT.MI', 'AMP.MI', 'ANIM.MI', 'ANTM.MI', 'AP.MI', 'ARN.MI', 'ARO.MI', 
        'ARR.MI', 'ASR.MI', 'AST.MI', 'ATC.MI', 'ATN.MI', 'AUT.MI', 'AZM.MI', 'B3.MI', 'BAC.MI', 'BFF.MI', 
        'BFR.MI', 'BFG.MI', 'BGN.MI', 'BIA.MI', 'BIB.MI', 'BIG.MI', 'BIO.MI', 'BIT.MI', 'BJ.MI', 'BLI.MI', 
        'BM.MI', 'BMC.MI', 'BMED.MI', 'BMI.MI', 'BPE.MI', 'BPL.MI', 'BRE.MI', 'BRI.MI', 'BRN.MI', 'BSP.MI', 
        'BSS.MI', 'BST.MI', 'BSU.MI', 'BVA.MI', 'BVT.MI', 'BZU.MI', 'CAI.MI', 'CALL.MI', 'CARR.MI', 'CAS.MI', 
        'CAT.MI', 'CBK.MI', 'CBM.MI', 'CBP.MI', 'CBR.MI', 'CBS.MI', 'CE.MI', 'CED.MI', 'CEM.MI', 'CES.MI', 
        'CFI.MI', 'CFN.MI', 'CG.MI', 'CGF.MI', 'CIA.MI', 'CL.MI', 'CLC.MI', 'CLE.MI', 'CLF.MI', 'CM.MI', 
        'CMC.MI', 'CNHI.MI', 'COF.MI', 'COG.MI', 'COM.MI', 'CON.MI', 'COP.MI', 'COV.MI', 'CPR.MI', 'CPS.MI', 
        'CR.MI', 'CRC.MI', 'CRG.MI', 'CRI.MI', 'CRS.MI', 'CRT.MI', 'CS.MI', 'CSF.MI', 'CSM.MI', 'CST.MI', 
        'CT.MI', 'CTI.MI', 'CTR.MI', 'CUS.MI', 'CV.MI', 'CWC.MI', 'CY.MI', 'DAN.MI', 'DAT.MI', 'DBA.MI', 
        'DD.MI', 'DEL.MI', 'DIA.MI', 'DIG.MI', 'DIS.MI', 'DLC.MI', 'DLP.MI', 'DM.MI', 'DMM.MI', 'DMT.MI', 
        'DNC.MI', 'DOP.MI', 'DOS.MI', 'DPS.MI', 'DR.MI', 'DRE.MI', 'DRN.MI', 'DS.MI', 'DSM.MI', 'DST.MI', 
        'E2E.MI', 'EAU.MI', 'EB.MI', 'EBS.MI', 'EC.MI', 'ED.MI', 'EDN.MI', 'EE.MI', 'EEL.MI', 'EFP.MI', 
        'EGF.MI', 'EGL.MI', 'EGP.MI', 'EG.MI', 'EHP.MI', 'EIP.MI', 'EIR.MI', 'EL.MI', 'ELC.MI', 'ELN.MI', 
        'EM.MI', 'EMA.MI', 'EMC.MI', 'ENE.MI', 'ENEL.MI', 'ENG.MI', 'ENI.MI', 'ENR.MI', 'ENT.MI', 'EO.MI', 
        'EOS.MI', 'EP.MI', 'EPR.MI', 'EQU.MI', 'ERA.MI', 'ERG.MI', 'ERI.MI', 'ES.MI', 'ESM.MI', 'EST.MI', 
        'ETR.MI', 'EUC.MI', 'EUR.MI', 'EUS.MI', 'EVA.MI', 'EVO.MI', 'EVR.MI', 'EXO.MI', 'EXP.MI', 'EZ.MI', 
        'FAB.MI', 'FAL.MI', 'FAM.MI', 'FAR.MI', 'FAS.MI', 'FAT.MI', 'FAV.MI', 'FB.MI', 'FBO.MI', 'FCD.MI', 
        'FCL.MI', 'FCT.MI', 'FD.MI', 'FDI.MI', 'FED.MI', 'FEM.MI', 'FER.MI', 'FFD.MI', 'FFI.MI', 'FG.MI', 
        'FH.MI', 'FHC.MI', 'FI.MI', 'FID.MI', 'FIG.MI', 'FIL.MI', 'FIM.MI', 'FIN.MI', 'FIR.MI', 'FIS.MI', 
        'FIT.MI', 'FIV.MI', 'FK.MI', 'FKO.MI', 'FLC.MI', 'FLD.MI', 'FLM.MI', 'FLO.MI', 'FLR.MI', 'FLS.MI', 
        'FLT.MI', 'FLY.MI', 'FMC.MI', 'FME.MI', 'FMI.MI', 'FML.MI', 'FMM.MI', 'FMN.MI', 'FMP.MI', 'FMS.MI', 
        'FMT.MI', 'FNC.MI', 'FND.MI', 'FNE.MI', 'FNG.MI', 'FNI.MI', 'FNM.MI', 'FNN.MI', 'FNP.MI', 'FNS.MI', 
        'FNT.MI', 'FNV.MI', 'G.MI', 'GAB.MI', 'GAL.MI', 'GAM.MI', 'GAR.MI', 'GBL.MI', 'GC.MI', 'GCC.MI', 
        'GDF.MI', 'GEC.MI', 'GEM.MI', 'GEN.MI', 'GEO.MI', 'GER.MI', 'GET.MI', 'GFC.MI', 'GHC.MI', 'GIA.MI', 
        'GIC.MI', 'GII.MI', 'GIL.MI', 'GIM.MI', 'GIN.MI', 'GIO.MI', 'GIP.MI', 'GIS.MI', 'GIV.MI', 'GLB.MI', 
        'GMA.MI', 'GMC.MI', 'GME.MI', 'GMI.MI', 'GMM.MI', 'GNA.MI', 'GNC.MI', 'GND.MI', 'GNG.MI', 'GNI.MI', 
        'GNL.MI', 'GNN.MI', 'GNS.MI', 'GOB.MI', 'GOC.MI', 'GOD.MI', 'GOE.MI', 'GOF.MI', 'GOG.MI', 'GOH.MI', 
        'GOL.MI', 'GOM.MI', 'GON.MI', 'GOP.MI', 'GOR.MI', 'GOS.MI', 'GOT.MI', 'GPA.MI', 'GPB.MI', 'GPC.MI', 
        'GPE.MI', 'GPI.MI', 'GPL.MI', 'GPM.MI', 'GPO.MI', 'GPP.MI', 'GPR.MI', 'GPS.MI', 'GPT.MI', 'GPV.MI', 
        'HER.MI', 'I2A.MI', 'IB.MI', 'IBS.MI', 'IC.MI', 'ICE.MI', 'ICP.MI', 'ID.MI', 'IDC.MI', 'IDE.MI', 
        'IDR.MI', 'IDS.MI', 'IE.MI', 'IF.MI', 'IFC.MI', 'IFF.MI', 'IFI.MI', 'IG.MI', 'IGD.MI', 'IGE.MI', 
        'III.MI', 'IJE.MI', 'IK.MI', 'IL.MI', 'ILC.MI', 'ILL.MI', 'ILM.MI', 'IM.MI', 'IMA.MI', 'IMC.MI', 
        'IMD.MI', 'IMF.MI', 'IMI.MI', 'IN.MI', 'INA.MI', 'INB.MI', 'INC.MI', 'IND.MI', 'INE.MI', 'INF.MI', 
        'ING.MI', 'INI.MI', 'INM.MI', 'INP.MI', 'INR.MI', 'INS.MI', 'INT.MI', 'INW.MI', 'IP.MI', 'IPC.MI', 
        'IPE.MI', 'IPM.MI', 'IPO.MI', 'IPR.MI', 'IPS.MI', 'IQ.MI', 'IR.MI', 'IRA.MI', 'IRC.MI', 'IRE.MI', 
        'IRI.MI', 'IRM.MI', 'IRR.MI', 'IRS.MI', 'IS.MI', 'ISC.MI', 'ISI.MI', 'ISM.MI', 'ISP.MI', 'ISS.MI', 
        'IST.MI', 'IT.MI', 'ITA.MI', 'ITC.MI', 'ITE.MI', 'ITG.MI', 'ITI.MI', 'ITM.MI', 'ITO.MI', 'ITS.MI', 
        'IV.MI', 'IVG.MI', 'IVS.MI', 'IZ.MI', 'JUVE.MI', 'K.MI', 'KB.MI', 'KC.MI', 'KE.MI', 'KF.MI', 
        'KG.MI', 'KIP.MI', 'KM.MI', 'KN.MI', 'KOP.MI', 'KR.MI', 'KS.MI', 'L.MI', 'LA.MI', 'LAB.MI', 
        'LAC.MI', 'LAD.MI', 'LDO.MI', 'LEA.MI', 'LEC.MI', 'LEG.MI', 'LEO.MI', 'LES.MI', 'LGT.MI', 'LI.MI', 
        'LIC.MI', 'LID.MI', 'LIE.MI', 'LIF.MI', 'LIG.MI', 'LII.MI', 'LIM.MI', 'LIN.MI', 'LIP.MI', 'LIS.MI', 
        'LIT.MI', 'LL.MI', 'LM.MI', 'LMC.MI', 'LMI.MI', 'LMM.MI', 'LMS.MI', 'LN.MI', 'LOC.MI', 'LOG.MI', 
        'LOM.MI', 'LON.MI', 'LOP.MI', 'LOR.MI', 'LTA.MI', 'LTC.MI', 'LTI.MI', 'LU.MI', 'LUB.MI', 'LUC.MI', 
        'LUD.MI', 'LUM.MI', 'LUP.MI', 'LUS.MI', 'LUT.MI', 'LUVE.MI', 'LV.MI', 'LVM.MI', 'LY.MI', 'M3.MI', 
        'MA.MI', 'MAB.MI', 'MAC.MI', 'MAD.MI', 'MAE.MI', 'MAF.MI', 'MAG.MI', 'MAI.MI', 'MAL.MI', 'MAM.MI', 
        'MAP.MI', 'MAR.MI', 'MAS.MI', 'MAT.MI', 'MB.MI', 'MBA.MI', 'MBF.MI', 'MBI.MI', 'MBM.MI', 'MBS.MI', 
        'MC.MI', 'MCA.MI', 'MCB.MI', 'MCC.MI', 'MCD.MI', 'MCE.MI', 'MCF.MI', 'MCG.MI', 'MCH.MI', 'MCI.MI', 
        'MCL.MI', 'MCM.MI', 'MCN.MI', 'MCO.MI', 'MCP.MI', 'MCR.MI', 'MCS.MI', 'MCT.MI', 'MD.MI', 'MDA.MI', 
        'MDB.MI', 'MDC.MI', 'MDF.MI', 'MDG.MI', 'MDI.MI', 'MDL.MI', 'MDM.MI', 'MDN.MI', 'MDP.MI', 'MDR.MI', 
        'MDS.MI', 'MDT.MI', 'ME.MI', 'MEA.MI', 'MEB.MI', 'MEC.MI', 'MED.MI', 'MEE.MI', 'MEG.MI', 'MEI.MI', 
        'MEL.MI', 'MEM.MI', 'MEN.MI', 'MER.MI', 'MES.MI', 'MET.MI', 'MFA.MI', 'MFB.MI', 'MFC.MI', 'MFEA.MI', 
        'MFEB.MI', 'MFG.MI', 'MFI.MI', 'MFL.MI', 'MFM.MI', 'MFN.MI', 'MFR.MI', 'MFS.MI', 'MG.MI', 'MGA.MI', 
        'MGB.MI', 'MGC.MI', 'MGD.MI', 'MGE.MI', 'MGF.MI', 'MGI.MI', 'MGL.MI', 'MGM.MI', 'MGN.MI', 'MGO.MI', 
        'MGP.MI', 'MGR.MI', 'MGS.MI', 'MH.MI', 'MHA.MI', 'MHB.MI', 'MHC.MI', 'MHD.MI', 'MHE.MI', 'MHF.MI', 
        'MHI.MI', 'MHL.MI', 'MHM.MI', 'MHN.MI', 'MHP.MI', 'MHR.MI', 'MHS.MI', 'MI.MI', 'MIA.MI', 'MIB.MI', 
        'MIC.MI', 'MID.MI', 'MIE.MI', 'MIF.MI', 'MIG.MI', 'MIL.MI', 'MIM.MI', 'MIN.MI', 'MIP.MI', 'MIR.MI', 
        'MIS.MI', 'MIT.MI', 'MIV.MI', 'MJ.MI', 'MK.MI', 'MKA.MI', 'MKB.MI', 'MKC.MI', 'MKE.MI', 'MKL.MI', 
        'MKM.MI', 'ML.MI', 'MLA.MI', 'MLB.MI', 'MLC.MI', 'MLE.MI', 'MLF.MI', 'MLG.MI', 'MLI.MI', 'MLL.MI', 
        'MLM.MI', 'MLN.MI', 'MLP.MI', 'MLR.MI', 'MLS.MI', 'MLT.MI', 'MM.MI', 'MMA.MI', 'MMB.MI', 'MMC.MI', 
        'MMD.MI', 'MME.MI', 'MMF.MI', 'MMG.MI', 'MMI.MI', 'MML.MI', 'MMM.MI', 'MMN.MI', 'MMP.MI', 'MMR.MI', 
        'MMS.MI', 'MMT.MI', 'MN.MI', 'MNA.MI', 'MNB.MI', 'MNC.MI', 'MND.MI', 'MNE.MI', 'MNF.MI', 'MNG.MI', 
        'MNI.MI', 'MNL.MI', 'MNM.MI', 'MNN.MI', 'MNP.MI', 'MNR.MI', 'MNS.MI', 'MNT.MI', 'MO.MI', 'MOA.MI', 
        'MOB.MI', 'MOC.MI', 'MOD.MI', 'MOE.MI', 'MOF.MI', 'MOG.MI', 'MOI.MI', 'MOL.MI', 'MOM.MI', 'MON.MI', 
        'MONC.MI', 'MOP.MI', 'MOR.MI', 'MOS.MI', 'MOT.MI', 'MP.MI', 'MPA.MI', 'MPB.MI', 'MPC.MI', 'MPE.MI', 
        'MPF.MI', 'MPG.MI', 'MPI.MI', 'MPL.MI', 'MPM.MI', 'MPN.MI', 'MPO.MI', 'MPR.MI', 'MPS.MI', 'MPT.MI', 
        'MR.MI', 'MRA.MI', 'MRB.MI', 'MRC.MI', 'MRD.MI', 'MRE.MI', 'MRF.MI', 'MRG.MI', 'MRI.MI', 'MRL.MI', 
        'MRM.MI', 'MRN.MI', 'MRO.MI', 'MRP.MI', 'MRR.MI', 'MRS.MI', 'MRT.MI', 'MS.MI', 'MSA.MI', 'MSB.MI', 
        'MSC.MI', 'MSD.MI', 'MSE.MI', 'MSF.MI', 'MSG.MI', 'MSI.MI', 'MSL.MI', 'MSM.MI', 'MSN.MI', 'MSO.MI', 
        'MSP.MI', 'MSR.MI', 'MSS.MI', 'MST.MI', 'MT.MI', 'MTA.MI', 'MTB.MI', 'MTC.MI', 'MTD.MI', 'MTE.MI', 
        'MTF.MI', 'MTG.MI', 'MTI.MI', 'MTL.MI', 'MTM.MI', 'MTN.MI', 'MTO.MI', 'MTP.MI', 'MTR.MI', 'MTS.MI', 
        'MTT.MI', 'MU.MI', 'MUA.MI', 'MUB.MI', 'MUC.MI', 'MUD.MI', 'MUE.MI', 'MUF.MI', 'MUG.MI', 'MUI.MI', 
        'MUL.MI', 'MUM.MI', 'MUN.MI', 'MUP.MI', 'MUR.MI', 'MUS.MI', 'MUT.MI', 'MV.MI', 'MVA.MI', 'MVB.MI', 
        'MVC.MI', 'MVE.MI', 'MVF.MI', 'MVG.MI', 'MVI.MI', 'MVL.MI', 'MVM.MI', 'MVN.MI', 'MVP.MI', 'MVR.MI', 
        'MVS.MI', 'MVT.MI', 'MW.MI', 'MX.MI', 'MY.MI', 'MZ.MI', 'NEXI.MI', 'O2A.MI', 'PIA.MI', 'PRY.MI', 
        'PST.MI', 'RACE.MI', 'REC.MI', 'RWAY.MI', 'SAF.MI', 'SFL.MI', 'SL.MI', 'SPM.MI', 'SRG.MI', 'STM.MI', 
        'TEN.MI', 'TIS.MI', 'TIT.MI', 'TOD.MI', 'TRN.MI', 'TXT.MI', 'UCG.MI', 'UNI.MI', 'US.MI', 'VLS.MI', 
        'VTY.MI', 'WBA.MI', 'ZUC.MI'
    ]

    tickers_it = [clean_ticker(t) for t in tickers_it_raw if clean_ticker(t)]

    all_cleaned = list(dict.fromkeys(tickers_it + tickers_us))
    return all_cleaned

def download_data():
    db_exists = os.path.exists(DB_FILE)
    market_data = {}

    if db_exists:
        update_progress(5, "Database trovato. Aggiornamento incrementale a blocchi...")
        try:
            with open(DB_FILE, 'r') as f:
                market_data = json.load(f)
        except Exception as e:
            log_error(f"Errore lettura DB esistente: {e}")
            market_data = {}
        period_to_fetch = "5d"
    else:
        update_progress(5, "Database assente. Download massivo a blocchi...")
        period_to_fetch = "5y"

    ALL_TICKERS = get_all_tickers()
    total_tickers = len(ALL_TICKERS)
    
    if total_tickers == 0:
        log_error("Nessun ticker disponibile per il download.")
        update_progress(100, "Errore: Lista ticker vuota")
        return

    ticker_batches = [ALL_TICKERS[i:i + BATCH_SIZE] for i in range(0, total_tickers, BATCH_SIZE)]
    total_batches = len(ticker_batches)

    for b_idx, batch in enumerate(ticker_batches):
        try:
            processed_count = min((b_idx + 1) * BATCH_SIZE, total_tickers)
            percent = int((processed_count / total_tickers) * 90) + 5
            update_progress(percent, f"Scaricamento blocco ({b_idx + 1}/{total_batches}) - {processed_count}/{total_tickers} titoli...")

            df_batch = yf.download(
                tickers=batch,
                period=period_to_fetch,
                group_by='ticker',
                auto_adjust=True,
                progress=False,
                threads=True
            )

            if df_batch is None or df_batch.empty:
                continue

            for ticker in batch:
                clean_sym = clean_ticker(ticker)
                try:
                    if len(batch) == 1:
                        series = df_batch['Close'] if 'Close' in df_batch else None
                    else:
                        series = df_batch[clean_sym]['Close'] if clean_sym in df_batch and 'Close' in df_batch[clean_sym] else None

                    if series is None or series.dropna().empty:
                        continue

                    series = series.dropna()
                    series.index = series.index.strftime('%Y-%m-%d')
                    new_data = series.to_dict()

                    if db_exists and clean_sym in market_data:
                        old_data = market_data[clean_sym]
                        if len(old_data) > 0 and period_to_fetch == "5d":
                            last_date = list(old_data.keys())[-1]
                            if last_date in old_data:
                                del old_data[last_date]
                        old_data.update(new_data)
                        market_data[clean_sym] = old_data
                    else:
                        market_data[clean_sym] = new_data
                except Exception as e_tick:
                    log_error(f"Errore estrazione ticker {clean_sym}: {e_tick}")
                    continue

            with open(DB_FILE, 'w') as f:
                json.dump(market_data, f)

            time.sleep(0.5)

        except Exception as e:
            err_msg = f"Errore blocco {b_idx + 1}: {e}"
            print(err_msg)
            log_error(err_msg)
            time.sleep(1.0)
            continue

    # Calcolo statistiche finali per il report pop-up
    it_count = 0
    us_count = 0
    it_years = []
    us_years = []

    for sym, prices in market_data.items():
        if not prices or len(prices) < 2:
            continue
        sorted_dates = sorted(prices.keys())
        d_start = datetime.strptime(sorted_dates[0], '%Y-%m-%d')
        d_end = datetime.strptime(sorted_dates[-1], '%Y-%m-%d')
        diff_years = max((d_end - d_start).days / 365.25, 0.01)

        if sym.endswith('.MI'):
            it_count += 1
            it_years.append(diff_years)
        else:
            us_count += 1
            us_years.append(diff_years)

    it_avg_years = round(sum(it_years) / len(it_years), 1) if it_years else 0.0
    us_avg_years = round(sum(us_years) / len(us_years), 1) if us_years else 0.0

    update_progress(100, "Completato!", {
        "it_count": it_count,
        "it_avg_years": it_avg_years,
        "us_count": us_count,
        "us_avg_years": us_avg_years
    })

if __name__ == "__main__":
    download_data()
