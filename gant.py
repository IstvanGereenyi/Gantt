import streamlit as strx
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

# Streamlit oldal alapbeállításai
strx.set_page_config(page_title="Gantt Chart Editor 2026", layout="wide")

# --- JELENLEGI IDŐ BEÁLLÍTÁSA (2026) ---
MAI_DATUM = pd.Timestamp.now().normalize()

def get_shifted_date(days_from_today):
    return (MAI_DATUM + pd.Timedelta(days=days_from_today)).strftime('%Y-%m-%d')

# --- INITIALIZATION (Csak a legelső betöltéskor fut le) ---
if 'tasks_df' not in strx.session_state:
    strx.session_state.tasks_df = pd.DataFrame([
        {"Task": "TSK M", "Department": "IT",   "Start": get_shifted_date(12), "End": get_shifted_date(15), "Completion": 0.0},
        {"Task": "TSK N", "Department": "MKT",  "Start": get_shifted_date(12), "End": get_shifted_date(14), "Completion": 0.0},
        {"Task": "TSK L", "Department": "ENG",  "Start": get_shifted_date(5),  "End": get_shifted_date(8),  "Completion": 0.0},
        {"Task": "TSK K", "Department": "PROD", "Start": get_shifted_date(4),  "End": get_shifted_date(8),  "Completion": 0.0},
        {"Task": "TSK J", "Department": "PROD", "Start": get_shifted_date(-1), "End": get_shifted_date(12), "Completion": 0.0},
        {"Task": "TSK H", "Department": "FIN",  "Start": get_shifted_date(-5), "End": get_shifted_date(-3), "Completion": 1.0},
        {"Task": "TSK I", "Department": "MKT",  "Start": get_shifted_date(-5), "End": get_shifted_date(0),  "Completion": 0.4},
        {"Task": "TSK G", "Department": "FIN",  "Start": get_shifted_date(-6), "End": get_shifted_date(-2), "Completion": 0.7},
        {"Task": "TSK F", "Department": "MKT",  "Start": get_shifted_date(-7), "End": get_shifted_date(-6), "Completion": 1.0},
        {"Task": "TSK E", "Department": "ENG",  "Start": get_shifted_date(-10),"End": get_shifted_date(4),  "Completion": 0.5},
        {"Task": "TSK D", "Department": "FIN",  "Start": get_shifted_date(-11),"End": get_shifted_date(-4), "Completion": 1.0},
        {"Task": "TSK C", "Department": "IT",   "Start": get_shifted_date(-12),"End": get_shifted_date(-2), "Completion": 0.9},
        {"Task": "TSK B", "Department": "MKT",  "Start": get_shifted_date(-14),"End": get_shifted_date(-9), "Completion": 1.0},
        {"Task": "TSK A", "Department": "MKT",  "Start": get_shifted_date(-18),"End": get_shifted_date(-13),"Completion": 1.0}
    ])

if 'project_title' not in strx.session_state:
    strx.session_state.project_title = "AKTUÁLIS PROJEKT - 2026"

if 'colors' not in strx.session_state:
    strx.session_state.colors = {"MKT": "#E64646", "FIN": "#E69646", "ENG": "#34D05C", "PROD": "#34D0C3", "IT": "#3475D0"}

if 'labels' not in strx.session_state:
    strx.session_state.labels = {"MKT": "Marketing", "FIN": "Finance", "ENG": "Engineering", "PROD": "Production", "IT": "IT"}


# --- ELRENDEZÉS ---
col_left, col_right = strx.columns([1, 1.2])

with col_left:
    strx.header("📊 Adatok és Beállítások")
    
    # Projekt cím mentése
    strx.session_state.project_title = strx.text_input("Projekt címe:", strx.session_state.project_title)
    
    strx.subheader("Feladatok listája")
    strx.caption("Kattints duplán a cellákra a szerkesztéshez! Új sort alul, kijelölt sort a 'Del' gombbal törölhetsz.")
    
    # BIZTOS MENTÉS: Közvetlenül a session_state-hez kötjük az editor kulcsát
    edited_df = strx.data_editor(
        strx.session_state.tasks_df,
        num_rows="dynamic",
        use_container_width=True,
        key="tasks_df_editor",  # Ez a kulcs automatikusan szinkronizálja a session_state.tasks_df-et!
        column_config={
            "Department": strx.column_config.SelectboxColumn("Department", options=["MKT", "FIN", "ENG", "PROD", "IT"]),
            "Completion": strx.column_config.NumberColumn("Completion", min_value=0.0, max_value=1.0, format="%.2f"),
            "Start": strx.column_config.TextColumn("Start (YYYY-MM-DD)"),
            "End": strx.column_config.TextColumn("End (YYYY-MM-DD)")
        }
    )

    # Színek és feliratok mentése egyedi key-ekkel
    strx.subheader("Részlegek testreszabása")
    depts = ["MKT", "FIN", "ENG", "PROD", "IT"]
    c1, c2 = strx.columns(2)
    for i, dept in enumerate(depts):
        target_col = c1 if i % 2 == 0 else c2
        with target_col:
            strx.session_state.labels[dept] = strx.text_input(f"{dept} név:", strx.session_state.labels[dept], key=f"lbl_{dept}")
            strx.session_state.colors[dept] = strx.color_picker(f"{dept} szín:", strx.session_state.colors[dept], key=f"clr_{dept}")

with col_right:
    strx.header("📈 Gantt Diagram")
    
    try:
        # A diagramhoz a friss, mentett állapotot olvassuk be az editorból
        df = edited_df.copy()
        
        # Tisztítjuk az üres vagy félbehagyott sorokat a hibák elkerülésére
        df = df.dropna(subset=['Start', 'End', 'Task'])
        df = df[df['Task'].astype(str).str.strip() != ""]
        
        if not df.empty:
            df['Start'] = pd.to_datetime(df['Start'])
            df['End'] = pd.to_datetime(df['End'])
            df['Completion'] = pd.to_numeric(df['Completion']).fillna(0.0)
            
            proj_start = df.Start.min()
            df['start_num'] = (df.Start - proj_start).dt.days
            df['end_num'] = (df.End - proj_start).dt.days
            df['days_start_to_end'] = df.end_num - df.start_num
            df['current_num'] = (df.days_start_to_end * df.Completion)
            df['color'] = df.apply(lambda r: strx.session_state.colors.get(str(r['Department']), '#808080'), axis=1)

            current_num = (MAI_DATUM - proj_start).days
        else:
            proj_start = MAI_DATUM
            current_num = 0

        color_dict = strx.session_state.colors
        label_dict = strx.session_state.labels
        project_title = strx.session_state.project_title

        # Matplotlib kirajzolás
        plt.rcParams['figure.facecolor'] = '#fafafa'
        fig, (ax, ax1) = plt.subplots(2, figsize=(10, 7), gridspec_kw={'height_ratios':[6, 1]})
        ax.set_facecolor('#ffffff')

        if not df.empty:
            # Csíkok rajzolása
            ax.barh(df.Task, df.current_num, left=df.start_num, color=df.color)
            ax.barh(df.Task, df.days_start_to_end, left=df.start_num, color=df.color, alpha=0.3)

            # Százalékok és nevek felírása
            for idx, row in df.reset_index(drop=True).iterrows():
                ax.text(row.end_num + 0.2, idx, f"{int(row.Completion*100)}%", va='center', alpha=0.8, fontsize=9)
                ax.text(row.start_num - 0.2, idx, row.Task, va='center', ha='right', alpha=0.8, fontsize=9)
                
                if current_num > row.start_num:
                    expected_end = min(current_num, row.end_num)
                    ax.plot([row.start_num, expected_end], [idx - 0.35, idx - 0.35], color='black', linewidth=1.5, alpha=0.7)

        # MAI piros vonal
        ax.axvline(x=current_num, color='#E64646', linestyle='--', linewidth=2, alpha=0.8)

        ax.set_axisbelow(True)
        ax.xaxis.grid(color='gray', linestyle='dashed', alpha=0.2, which='both')

        # Alsó tengely generálása
        max_days = max(df['end_num'].max(), current_num + 3) if not df.empty else 10
        xticks = np.arange(0, max_days + 1, max(3, max_days // 10))
        if current_num not in xticks and current_num >= 0:
            xticks = np.sort(np.append(xticks, current_num))

        date_range = pd.date_range(proj_start, periods=max_days + 15)
        xticks_labels = date_range.strftime("%m/%d").tolist()
        
        labels_built = []
        for tick in xticks:
            if tick == current_num:
                labels_built.append(f"MA\n({xticks_labels[tick]})")
            else:
                labels_built.append(xticks_labels[tick])

        ax.set_xticks(xticks)
        ax.set_xticklabels(labels_built)
        
        for label in ax.get_xticklabels():
            if "MA" in label.get_text():
                label.set_color('#E64646')
                label.set_weight('bold')

        ax.set_yticks([])

        # Felső naptári hetek skála
        ax_top = ax.twiny()
        ax.set_xlim(0, max_days + 1)
        ax_top.set_xlim(0, max_days + 1)

        monday_indices = []
        week_labels = []
        for i, d in enumerate(date_range[:max_days + 1]):
            if d.dayofweek == 0 or i == 0:
                if not monday_indices or (i - monday_indices[-1] >= 4):
                    monday_indices.append(i)
                    week_labels.append(f"Week {d.isocalendar()[1]}")

        ax_top.set_xticks(monday_indices, minor=True)
        major_positions = [monday_indices[i] + ((monday_indices[i+1] if i+1 < len(monday_indices) else max_days + 1) - monday_indices[i]) / 2 for i in range(len(monday_indices))]
        ax_top.set_xticks(major_positions, minor=False)
        ax_top.set_xticklabels(week_labels, ha='center', minor=False)
        ax_top.tick_params(which='major', color='w')
        ax_top.tick_params(which='minor', length=6, color='k')

        for axis in [ax, ax_top]:
            axis.spines['right'].set_visible(False)
            axis.spines['left'].set_visible(False)
            axis.spines['top'].set_visible(False)

        plt.suptitle(project_title, fontsize=14, fontweight='bold', color='#333333')

        # Jelmagyarázat
        used_depts = df['Department'].unique() if not df.empty else []
        legend_elements = [Patch(facecolor=color, label=label_dict[dept]) for dept, color in color_dict.items() if dept in used_depts]
        legend_elements.append(Line2D([0], [0], color='#E64646', linestyle='--', linewidth=2, label='Jelenlegi nap (MA)'))
        legend_elements.append(Line2D([0], [0], color='black', linewidth=1.5, label='Elvárt szint (időarányos)'))

        if legend_elements:
            ax1.legend(handles=legend_elements, loc='upper center', ncol=3, frameon=False, fontsize=9)
        
        for spine in ax1.spines.values(): spine.set_visible(False)
        ax1.set_xticks([])
        ax1.set_yticks([])

        plt.tight_layout()
        strx.pyplot(fig)
        plt.close(fig)
        
    except Exception as e:
        strx.info("Add meg a hiányzó adatokat vagy javítsd a dátum formátumot (YYYY-MM-DD) a diagram frissüléséhez!")