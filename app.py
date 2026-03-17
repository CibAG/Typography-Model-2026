import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import json
import os
import sys

# Настройка путей
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(BASE_DIR, "settings.json")

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class PrintingApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Типография 2026: Финансовая модель")
        self.geometry("1250x850")
        
        # Правильный перехват закрытия
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.saved_values = self.load_data()

        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # ЛЕВАЯ ПАНЕЛЬ
        self.left_panel = ctk.CTkScrollableFrame(self.main_frame, width=420)
        self.left_panel.pack(side="left", fill="y", padx=(0, 20))

        ctk.CTkLabel(self.left_panel, text="ПАРАМЕТРЫ МОДЕЛИ", font=("Arial", 18, "bold"), text_color="#3b8ed0").pack(pady=10)
        self.create_input("НДС (%)", "20", "nds_pct")
        self.create_input("Себестоимость (%)", "60", "cost_pct")
        self.create_input("Целевая чистая прибыль", "1000", "target_profit")

        ctk.CTkLabel(self.left_panel, text="Персонал и Налоги (ФОТ)", font=("Arial", 18, "bold"), text_color="#3b8ed0").pack(pady=10)
        self.create_input("Зарплата на руки", "22400", "salary_net")
        self.create_input("Уплата ФСЗН", "0", "fszn", readonly=True)
        self.create_input("Уплата подоходного", "0", "income_tax", readonly=True)
        self.create_input("Уплата белгосстрах", "0", "bgs", readonly=True)

        ctk.CTkLabel(self.left_panel, text="Офис и Финансы", font=("Arial", 18, "bold"), text_color="#3b8ed0").pack(pady=10)
        self.create_input("Бухгалтерия", "1500", "accounting")
        self.create_input("Аренда + Коммуналка", "12500", "rent")
        self.create_input("Лизинг BYD", "2500", "leasing_byd")
        self.create_input("Лизинг BESTUNE", "1500", "leasing_belyash")
        self.create_input("Кредиты", "900", "credit_costs")
        self.create_input("Банк", "300", "bank_services")
        self.create_input("Прочие затраты", "300", "other_costs")

        self.btn_calc = ctk.CTkButton(self.left_panel, text="РАССЧИТАТЬ", command=self.calculate, height=50, font=("Arial", 16, "bold"))
        self.btn_calc.pack(pady=25)

        self.result_text = ctk.CTkTextbox(self.left_panel, width=350, height=220, font=("Consolas", 14))
        self.result_text.pack(pady=10)

        # ПРАВАЯ ПАНЕЛЬ
        self.canvas_frame = ctk.CTkFrame(self.main_frame)
        self.canvas_frame.pack(side="right", fill="both", expand=True)
        self.fig, self.ax = plt.subplots(figsize=(7, 6), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.canvas_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.auto_calculate_taxes()
        self.calculate()

    def on_closing(self):
        plt.close('all')
        self.quit()
        self.destroy()
        sys.exit()

    def create_input(self, label_text, default_val, var_name, readonly=False):
        frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(frame, text=label_text, width=220, anchor="w").pack(side="left")
        
        sv = tk.StringVar(value=str(self.saved_values.get(var_name, default_val)))
        entry = ctk.CTkEntry(frame, width=120, textvariable=sv, state="readonly" if readonly else "normal")
        
        if var_name == "salary_net":
            sv.trace_add("write", self.auto_calculate_taxes)
        
        entry.pack(side="right")
        setattr(self, var_name, entry)

    def auto_calculate_taxes(self, *args):
        try:
            val_str = self.salary_net.get().replace(",", ".")
            if not val_str: return
            net = float(val_str)
            # Расчет грязной зарплаты исходя из 0.86 (100% - 13% - 1%)
            gross = net / 0.86
            
            f_worker = gross * 0.01
            f_employer = gross * 0.34
            inc_tax = gross * 0.13
            bgs_val = gross * 0.006

            self.update_field(self.fszn, f"{(f_employer + f_worker):.2f}")
            self.update_field(self.income_tax, f"{inc_tax:.2f}")
            self.update_field(self.bgs, f"{bgs_val:.2f}")
        except: pass

    def update_field(self, field, val):
        field.configure(state="normal")
        field.delete(0, tk.END)
        field.insert(0, val)
        field.configure(state="readonly")

    def load_data(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f: return json.load(f)
            except: return {}
        return {}

    def calculate(self):
        try:
            keys = ["nds_pct", "cost_pct", "target_profit", "salary_net", "fszn", "income_tax", "bgs", 
                    "accounting", "rent", "leasing_byd", "leasing_belyash", "credit_costs", "bank_services", "other_costs"]
            
            vals = {k: float(getattr(self, k).get().replace(",", ".")) for k in keys}
            
            # Суммарные затраты на персонал
            total_staff = vals["salary_net"] + vals["fszn"] + vals["income_tax"] + vals["bgs"]
            
            # Постоянные расходы
            fc = (total_staff + vals["accounting"] + vals["rent"] + 
                  vals["leasing_byd"] + vals["leasing_belyash"] + 
                  vals["credit_costs"] + vals["bank_services"] + vals["other_costs"])
            
            nds_f = 1 + (vals["nds_pct"] / 100)
            margin = 1 - (vals["cost_pct"] / 100)
            
            bep = (fc / margin) * nds_f
            goal = ((fc + (vals["target_profit"] / 0.8)) / margin) * nds_f

            self.result_text.delete("1.0", tk.END)
            res = (f"ЗАТРАТЫ НА ПЕРСОНАЛ: {int(total_staff):,} BYN\n"
                   f"ПОСТОЯННЫЕ (ВСЕГО): {int(fc):,} BYN\n"
                   f"------------------------------\n"
                   f"ТОЧКА НУЛЯ: {int(bep):,} BYN\n"
                   f"ЦЕЛЬ ВЫРУЧКИ: {int(goal):,} BYN\n\n"
                   f"Прибыль: {int(vals['target_profit']):,} BYN").replace(",", " ")
            self.result_text.insert("1.0", res)

            self.ax.clear()
            self.fig.patch.set_facecolor('#1a1a1a')
            self.ax.set_facecolor('#1a1a1a')
            x = np.linspace(0, goal * 1.5, 100)
            y = ((x / nds_f * margin) - fc) * 0.8
            self.ax.plot(x, y, color='#00aaff', lw=3)
            self.ax.axhline(0, color='white', lw=1)
            self.ax.axvline(bep, color='#ff9500', linestyle='--')
            self.ax.scatter([goal], [vals["target_profit"]], color='red', s=100)
            self.ax.tick_params(colors='white')
            self.canvas.draw()
        except: messagebox.showerror("Ошибка", "Проверьте ввод чисел!")

if __name__ == "__main__":
    app = PrintingApp()
    app.mainloop()