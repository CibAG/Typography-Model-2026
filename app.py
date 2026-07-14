import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import json
import os
import sys

# Настройка путей для EXE
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
        self.title("Типография 2026: Financial Optimizer")
        self.geometry("1350x900")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.saved_values = self.load_data()

        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # ЛЕВАЯ ПАНЕЛЬ
        self.left_panel = ctk.CTkScrollableFrame(self.main_frame, width=460)
        self.left_panel.pack(side="left", fill="y", padx=(0, 20))

        # --- НАЗВАНИЕ ПРЕДПРИЯТИЯ ---
        ctk.CTkLabel(self.left_panel, text="0. НАЗВАНИЕ ПРЕДПРИЯТИЯ", font=("Arial", 18, "bold"), text_color="#edad2b").pack(pady=(0,10))
        self.create_input("Название:", "", "enterprise_name", width=200)

        # --- НАЛОГОВЫЙ РЕЖИМ ---
        ctk.CTkLabel(self.left_panel, text="1. НАЛОГОВЫЙ РЕЖИМ", font=("Arial", 18, "bold"), text_color="#edad2b").pack(pady=(0,10))
        self.tax_mode = ctk.StringVar(value=self.saved_values.get("tax_mode", "ОСН (с НДС 20%)"))
        self.tax_menu = ctk.CTkOptionMenu(self.left_panel, 
                                         values=["ОСН (с НДС 20%)", "УСН (6% от выручки)"], 
                                         variable=self.tax_mode, 
                                         command=lambda _: self.calculate())
        self.tax_menu.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(self.left_panel, text="*УСН считает 6% налога от всей выручки", font=("Arial", 11, "italic")).pack()

        ctk.CTkLabel(self.left_panel, text="2. ПАРАМЕТРЫ ПРОИЗВОДСТВА", font=("Arial", 18, "bold"), text_color="#3b8ed0").pack(pady=10)
        self.create_input("Себестоимость (%)", "60", "cost_pct")
        self.create_input("Целевая чистая прибыль", "1000", "target_profit")

        ctk.CTkLabel(self.left_panel, text="3. ПЕРСОНАЛ (ФОТ)", font=("Arial", 18, "bold"), text_color="#3b8ed0").pack(pady=10)
        self.create_input("Зарплата на руки (Net)", "22400", "salary_net")
        self.create_input("ФСЗН (35%)", "0", "fszn", readonly=True)
        self.create_input("Подоходный (13%)", "0", "income_tax", readonly=True)

        ctk.CTkLabel(self.left_panel, text="4. ПРОЧИЕ РАСХОДЫ", font=("Arial", 18, "bold"), text_color="#3b8ed0").pack(pady=10)
        self.create_input("Аренда + Комм", "12500", "rent")
        self.create_input("Лизинги/Кредиты", "4900", "loans")
        self.create_input("Бухгалтерия/Банк", "2100", "other_fixed")

        self.btn_calc = ctk.CTkButton(self.left_panel, text="РАССЧИТАТЬ", command=self.calculate, height=50, font=("Arial", 16, "bold"))
        self.btn_calc.pack(pady=25)

        self.result_text = ctk.CTkTextbox(self.left_panel, width=420, height=280, font=("Consolas", 14))
        self.result_text.pack(pady=10)

        # ПРАВАЯ ПАНЕЛЬ
        self.canvas_frame = ctk.CTkFrame(self.main_frame)
        self.canvas_frame.pack(side="right", fill="both", expand=True)
        self.fig, self.ax = plt.subplots(figsize=(7, 6), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.canvas_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.auto_calculate_taxes()
        self.calculate()

    def create_input(self, label_text, default_val, var_name, readonly=False, width=120):
        frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(frame, text=label_text, width=200, anchor="w").pack(side="left")
        sv = tk.StringVar(value=str(self.saved_values.get(var_name, default_val)))
        entry = ctk.CTkEntry(frame, width=width, textvariable=sv, state="readonly" if readonly else "normal")
        if var_name == "salary_net": sv.trace_add("write", self.auto_calculate_taxes)
        entry.pack(side="right")
        setattr(self, var_name, entry)

    def auto_calculate_taxes(self, *args):
        try:
            net = float(self.salary_net.get().replace(",", "."))
            gross = net / 0.86
            self.update_readonly(self.fszn, f"{(gross * 0.35):.2f}")
            self.update_readonly(self.income_tax, f"{(gross * 0.13):.2f}")
        except (ValueError, ZeroDivisionError): pass

    def update_readonly(self, field, val):
        field.configure(state="normal"); field.delete(0, tk.END); field.insert(0, val); field.configure(state="readonly")

    def load_data(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f: return json.load(f)
            except (json.JSONDecodeError, OSError): return {}
        return {}

    def calculate(self):
        try:
            mode = self.tax_mode.get()
            keys = ["cost_pct", "target_profit", "salary_net", "fszn", "income_tax", "rent", "loans", "other_fixed"]
            vals = {k: float(getattr(self, k).get().replace(",", ".")) for k in keys}
            
            # Сохранение
            save_dict = {k: getattr(self, k).get() for k in keys}
            save_dict["tax_mode"] = mode
            save_dict["enterprise_name"] = self.enterprise_name.get()
            with open(CONFIG_FILE, "w", encoding="utf-8") as f: json.dump(save_dict, f, indent=4)

            enterprise = self.enterprise_name.get().strip()
            if enterprise:
                self.title(f"{enterprise} | Financial Optimizer")

            # Расчет ФОТ + налоги
            staff_total = vals["salary_net"] + vals["fszn"] + vals["income_tax"] + (vals["salary_net"]/0.86 * 0.006)
            fc = staff_total + vals["rent"] + vals["loans"] + vals["other_fixed"]
            
            margin_pct = 1 - (vals["cost_pct"] / 100)

            if "ОСН" in mode:
                nds_f = 1.2
                bep = (fc / margin_pct) * nds_f
                # Для прибыли при ОСН используем коэффициент 0.8 (налог на прибыль 20%)
                goal = ((fc + (vals["target_profit"] / 0.8)) / margin_pct) * nds_f
            else:
                # УСН 6%: Маржа уменьшается на налог от выручки
                effective_margin = margin_pct - 0.06
                bep = fc / effective_margin
                goal = (fc + vals["target_profit"]) / effective_margin

            # МОДУЛЬ 4: ЗАПАС ФИНАНСОВОЙ ПРОЧНОСТИ
            safety_margin = ((goal - bep) / goal) * 100
            if safety_margin < 10:
                status, color = "КРИТИЧЕСКИЙ (Риск убытка)", "#ff4c4c"
            elif safety_margin < 25:
                status, color = "УДОВЛЕТВОРИТЕЛЬНО", "#edad2b"
            else:
                status, color = "ВЫСОКИЙ (Стабильно)", "#4caf50"

            self.result_text.delete("1.0", tk.END)
            header = f"ПРЕДПРИЯТИЕ: {enterprise}\n" if enterprise else ""
            res = (f"{header}"
                   f"РЕЖИМ: {mode}\n"
                   f"ЗАТРАТЫ НА ПЕРСОНАЛ: {int(staff_total):,} BYN\n"
                   f"ПОСТОЯННЫЕ (ИТОГО): {int(fc):,} BYN\n"
                   f"------------------------------\n"
                   f"ТОЧКА НУЛЯ: {int(bep):,} BYN\n"
                   f"ЦЕЛЬ ВЫРУЧКИ: {int(goal):,} BYN\n"
                   f"------------------------------\n"
                   f"ЗАПАС ПРОЧНОСТИ: {safety_margin:.1f}%\n"
                   f"СТАТУС: {status}")
            self.result_text.insert("1.0", res.replace(",", " "))

            # График
            self.ax.clear()
            self.fig.patch.set_facecolor('#1a1a1a'); self.ax.set_facecolor('#1a1a1a')
            x = np.linspace(0, goal * 1.5, 100)
            cur_margin = margin_pct if "ОСН" in mode else effective_margin
            # Приведение выручки к базе без НДС для графика при ОСН
            # Для ОСН кривая отражает ЧИСТУЮ прибыль (после налога на прибыль 20%),
            # чтобы красная точка целевой прибыли лежала на линии графика
            nds_div = 1.2 if "ОСН" in mode else 1
            profit_factor = 0.8 if "ОСН" in mode else 1
            y = (((x / nds_div) * cur_margin) - fc) * profit_factor
            self.ax.plot(x, y, color='#00aaff', lw=3)
            self.ax.axhline(0, color='white', lw=1)
            self.ax.axvline(bep, color='#ff9500', ls='--')
            
            # --- ВОЗВРАЩАЕМ И ПОДПИСЫВАЕМ ТОЧКУ ЦЕЛЕВОЙ ПРИБЫЛИ ---
            # Рисуем красную точку
            self.ax.scatter([goal], [vals["target_profit"]], color='red', s=120, zorder=5)
            
            # Добавляем краткую подпись
            self.ax.annotate(f"ЧИСТ.ПРИБЫЛЬ\n{int(vals['target_profit']):,} BYN".replace(",", " "), 
                             xy=(goal, vals["target_profit"]), 
                             xytext=(20, 10), # Смещение текста относительно точки
                             textcoords='offset points',
                             color='white',
                             fontweight='bold',
                             fontsize=11,
                             arrowprops=dict(arrowstyle="->", color='white', connectionstyle="arc3,rad=.2"))
            
            self.ax.tick_params(colors='white')
            # Настройка сетки для красоты
            self.ax.grid(color='#444444', linestyle='--', linewidth=0.5)
            self.canvas.draw()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Проверьте правильность ввода чисел! {e}")

    def on_closing(self):
        plt.close('all'); self.destroy()

if __name__ == "__main__":
    app = PrintingApp(); app.mainloop()