#!/usr/bin/env python3
"""
fittracker_simple.py
Single-file simplified exercise + nutrition tracker.

- Workouts kept for 14 days (workouts.json)
- Nutrition (meals) kept for 7 days (nutrition.json)
- Foods saved forever (foods.json)
- Reports: last 7 days calories & protein (two side-by-side graphs)
- Requires: ttkbootstrap, matplotlib
"""

import json, os, uuid
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
from ttkbootstrap import Style
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ---------- Files & helpers ----------
WORKOUT_FILE = "workouts.json"
NUTR_FILE = "nutrition.json"
FOODS_FILE = "foods.json"

def load_json(fn, default):
    if os.path.exists(fn):
        try:
            with open(fn, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default

def save_json(fn, data):
    with open(fn, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def make_id(): return uuid.uuid4().hex
def today_str(): return datetime.now().strftime("%Y-%m-%d")

# ---------- Load data and prune old entries ----------
workouts = load_json(WORKOUT_FILE, {"sessions": []})
nutrition = load_json(NUTR_FILE, {"meals": []})
foods = load_json(FOODS_FILE, {})  # {name: {"cal": ..., "prot": ...}}

def prune_data():
    # Workouts: keep last 14 days
    cutoff_w = (datetime.now().date() - timedelta(days=14)).strftime("%Y-%m-%d")
    workouts["sessions"] = [s for s in workouts.get("sessions", []) if s.get("date", "") >= cutoff_w]
    # Nutrition (meals): keep last 7 days
    cutoff_n = (datetime.now().date() - timedelta(days=7)).strftime("%Y-%m-%d")
    nutrition["meals"] = [m for m in nutrition.get("meals", []) if m.get("date", "") >= cutoff_n]
    save_json(WORKOUT_FILE, workouts)
    save_json(NUTR_FILE, nutrition)
    save_json(FOODS_FILE, foods)

prune_data()

# ---------- App ----------
class FitSimple:
    def __init__(self, root):
        self.style = Style(theme="superhero")  # dark-ish with red accents
        self.root = root
        root.title("FitTracker — Simple")
        root.geometry("950x600")

        nb = ttk.Notebook(root)
        nb.pack(expand=True, fill="both", padx=8, pady=8)

        self.tab_work = ttk.Frame(nb); nb.add(self.tab_work, text="Workout")
        self.tab_nut = ttk.Frame(nb); nb.add(self.tab_nut, text="Nutrition")
        self.tab_rep = ttk.Frame(nb); nb.add(self.tab_rep, text="Reports")

        self.build_workout_tab()
        self.build_nutrition_tab()
        self.build_reports_tab()

    # ---------- Workout ----------
    def build_workout_tab(self):
        left = ttk.Frame(self.tab_work, width=260)
        left.pack(side="left", fill="y", padx=6, pady=6)
        right = ttk.Frame(self.tab_work)
        right.pack(side="left", expand=True, fill="both", padx=6, pady=6)

        ttk.Label(left, text="Sessions (newest first)").pack(anchor="w")
        self.session_list = tk.Listbox(left, height=25)
        self.session_list.pack(fill="y", expand=True)
        self.session_list.bind("<<ListboxSelect>>", lambda e: self.show_session())

        ttk.Button(left, text="Add Session", command=self.add_session).pack(fill="x", pady=4)
        ttk.Button(left, text="Delete Session", command=self.delete_session).pack(fill="x", pady=4)

        ttk.Label(right, text="Exercises").pack(anchor="w")
        cols = ("Name","Sets","Reps","Weight")
        self.ex_tree = ttk.Treeview(right, columns=cols, show="headings", height=15)
        for c in cols:
            self.ex_tree.heading(c, text=c)
            self.ex_tree.column(c, anchor="center")
        self.ex_tree.pack(expand=True, fill="both")
        btns = ttk.Frame(right); btns.pack(pady=6)
        ttk.Button(btns, text="Add Exercise", command=self.add_ex).grid(row=0,column=0,padx=4)
        ttk.Button(btns, text="Delete Exercise", command=self.del_ex).grid(row=0,column=1,padx=4)

        self.refresh_sessions()

    def refresh_sessions(self):
        self.session_list.delete(0, tk.END)
        sessions = sorted(workouts.get("sessions", []), key=lambda s: (s.get("date",""), s.get("created","")), reverse=True)
        for s in sessions:
            label = f"{s.get('date')} — {s.get('name')}"
            self.session_list.insert(tk.END, label)

    def get_selected_session(self):
        sel = self.session_list.curselection()
        if not sel: return None
        idx = sel[0]
        sessions = sorted(workouts.get("sessions", []), key=lambda s: (s.get("date",""), s.get("created","")), reverse=True)
        return sessions[idx]

    def show_session(self):
        for iid in self.ex_tree.get_children(): self.ex_tree.delete(iid)
        s = self.get_selected_session()
        if not s: return
        for ex in s.get("exercises", []):
            self.ex_tree.insert("", tk.END, values=(ex.get("name"), ex.get("sets"), ex.get("reps"), ex.get("weight")))

    def add_session(self):
        name = simpledialog.askstring("Session", "Name (e.g., Push):", parent=self.root)
        if not name: return
        date = simpledialog.askstring("Date", "Date YYYY-MM-DD (leave blank = today):", parent=self.root) or today_str()
        try: datetime.strptime(date, "%Y-%m-%d")
        except:
            messagebox.showerror("Invalid", "Use YYYY-MM-DD"); return
        session = {"id": make_id(), "name": name, "date": date, "created": datetime.now().isoformat(), "exercises": []}
        workouts.setdefault("sessions", []).append(session)
        save_json(WORKOUT_FILE, workouts)
        prune_data()
        self.refresh_sessions()

    def delete_session(self):
        s = self.get_selected_session()
        if not s:
            messagebox.showinfo("Select", "Select a session first"); return
        if messagebox.askyesno("Confirm", f"Delete {s.get('name')} on {s.get('date')}?"):
            workouts["sessions"] = [x for x in workouts["sessions"] if x.get("id")!=s.get("id")]
            save_json(WORKOUT_FILE, workouts)
            self.refresh_sessions()
            for iid in self.ex_tree.get_children(): self.ex_tree.delete(iid)

    def add_ex(self):
        s = self.get_selected_session()
        if not s:
            messagebox.showinfo("Select", "Select a session first"); return
        name = simpledialog.askstring("Exercise", "Name:", parent=self.root)
        if not name: return
        sets = simpledialog.askinteger("Sets", "Sets (e.g., 3):", parent=self.root, minvalue=1)
        if sets is None: return
        reps = simpledialog.askinteger("Reps", "Reps (e.g., 8):", parent=self.root, minvalue=1)
        if reps is None: return
        weight = simpledialog.askfloat("Weight (kg)", "Weight (kg):", parent=self.root)
        if weight is None: return
        ex = {"id": make_id(), "name": name, "sets": int(sets), "reps": int(reps), "weight": round(float(weight),2)}
        # find session in original list and append
        for sess in workouts["sessions"]:
            if sess.get("id")==s.get("id"):
                sess.setdefault("exercises", []).append(ex)
                break
        save_json(WORKOUT_FILE, workouts)
        self.show_session()

    def del_ex(self):
        s = self.get_selected_session()
        if not s:
            messagebox.showinfo("Select", "Select a session first"); return
        sel = self.ex_tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Select an exercise"); return
        vals = self.ex_tree.item(sel[0])["values"]
        # remove by matching fields (simple)
        for sess in workouts["sessions"]:
            if sess.get("id")==s.get("id"):
                sess["exercises"] = [e for e in sess.get("exercises", []) if not (e.get("name")==vals[0] and e.get("sets")==vals[1] and e.get("reps")==vals[2])]
                break
        save_json(WORKOUT_FILE, workouts)
        self.show_session()

    # ---------- Nutrition ----------
    def build_nutrition_tab(self):
        top = ttk.Frame(self.tab_nut)
        top.pack(side="top", fill="x", padx=6, pady=6)
        mid = ttk.Frame(self.tab_nut)
        mid.pack(expand=True, fill="both", padx=6, pady=6)

        # Foods list (permanent)
        ttk.Label(top, text="Foods (saved forever)").pack(anchor="w")
        self.food_list = tk.Listbox(top, height=6)
        self.food_list.pack(fill="x", expand=True)
        food_row = ttk.Frame(top); food_row.pack(pady=4)
        ttk.Button(food_row, text="Add Food", command=self.add_food).grid(row=0,column=0,padx=4)
        ttk.Button(food_row, text="Delete Food", command=self.del_food).grid(row=0,column=1,padx=4)
        self.refresh_foods()

        # Meals for a date
        date_row = ttk.Frame(mid); date_row.pack(fill="x")
        ttk.Label(date_row, text="Date (YYYY-MM-DD):").pack(side="left")
        self.meal_date = tk.StringVar(value=today_str())
        ttk.Entry(date_row, textvariable=self.meal_date, width=12).pack(side="left", padx=6)
        ttk.Button(date_row, text="Load", command=self.load_meals).pack(side="left", padx=6)

        cols = ("Time","Food","Grams","Calories","Protein")
        self.meals_tree = ttk.Treeview(mid, columns=cols, show="headings", height=12)
        for c in cols:
            self.meals_tree.heading(c, text=c)
            self.meals_tree.column(c, anchor="center")
        self.meals_tree.pack(expand=True, fill="both")

        btns = ttk.Frame(mid); btns.pack(pady=6)
        ttk.Button(btns, text="Log Meal", command=self.log_meal).grid(row=0,column=0,padx=4)
        ttk.Button(btns, text="Delete Meal", command=self.del_meal).grid(row=0,column=1,padx=4)

        self.totals_label = ttk.Label(self.tab_nut, text="")
        self.totals_label.pack(padx=8, pady=4)
        self.load_meals()

    def refresh_foods(self):
        self.food_list.delete(0, tk.END)
        for name, d in sorted(foods.items()):
            self.food_list.insert(tk.END, f"{name} — {d.get('cal')} kcal / {d.get('prot')} g per 100g")

    def add_food(self):
        name = simpledialog.askstring("Food name", "Name (exact):", parent=self.root)
        if not name: return
        if name in foods:
            messagebox.showinfo("Exists", "Food already exists"); return
        cal = simpledialog.askfloat("Calories per 100g", "Calories per 100g:", parent=self.root)
        if cal is None: return
        prot = simpledialog.askfloat("Protein per 100g", "Protein per 100g:", parent=self.root)
        if prot is None: return
        foods[name] = {"cal": round(float(cal),2), "prot": round(float(prot),2)}
        save_json(FOODS_FILE, foods)
        self.refresh_foods()

    def del_food(self):
        sel = self.food_list.curselection()
        if not sel:
            messagebox.showinfo("Select", "Select a food"); return
        line = self.food_list.get(sel[0])
        name = line.split(" — ")[0]
        if messagebox.askyesno("Confirm", f"Delete food '{name}'?"):
            foods.pop(name, None)
            # also remove meals that used this food (optional)
            nutrition["meals"] = [m for m in nutrition.get("meals", []) if m.get("food")!=name]
            save_json(FOODS_FILE, foods)
            save_json(NUTR_FILE, nutrition)
            self.refresh_foods()
            self.load_meals()

    def load_meals(self):
        for iid in self.meals_tree.get_children(): self.meals_tree.delete(iid)
        date = self.meal_date.get().strip() or today_str()
        try: datetime.strptime(date, "%Y-%m-%d")
        except:
            messagebox.showerror("Invalid", "Use YYYY-MM-DD"); return
        rows = [m for m in nutrition.get("meals", []) if m.get("date")==date]
        total_cal = total_pro = 0
        for m in rows:
            self.meals_tree.insert("", tk.END, iid=m.get("id"), values=(m.get("time"), m.get("food"), m.get("grams"), m.get("calories"), m.get("protein")))
            total_cal += m.get("calories",0); total_pro += m.get("protein",0)
        self.totals_label.config(text=f"Date: {date}    Total Calories: {round(total_cal,2)} kcal    Total Protein: {round(total_pro,2)} g")
        save_json(NUTR_FILE, nutrition)

    def log_meal(self):
        if not foods:
            messagebox.showinfo("No foods", "Add foods first"); return
        date = self.meal_date.get().strip() or today_str()
        try: datetime.strptime(date, "%Y-%m-%d")
        except:
            messagebox.showerror("Invalid", "Use YYYY-MM-DD"); return
        # pick food name by exact typing (keeps UI tiny)
        choice = simpledialog.askstring("Food", f"Type food name exactly (from saved foods):", parent=self.root)
        if not choice or choice not in foods:
            messagebox.showerror("Invalid", "Food not found"); return
        grams = simpledialog.askfloat("Grams", "Enter grams consumed:", parent=self.root)
        if grams is None: return
        f = foods[choice]
        factor = grams / 100.0
        cal = round(f["cal"] * factor, 2)
        prot = round(f["prot"] * factor, 2)
        meal = {
            "id": make_id(),
            "date": date,
            "time": datetime.now().strftime("%H:%M:%S"),
            "food": choice,
            "grams": round(float(grams),2),
            "calories": cal,
            "protein": prot
        }
        nutrition.setdefault("meals", []).append(meal)
        save_json(NUTR_FILE, nutrition)
        prune_data()
        self.load_meals()

    def del_meal(self):
        sel = self.meals_tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Select a meal"); return
        mid = sel[0]
        if messagebox.askyesno("Confirm", "Delete selected meal?"):
            nutrition["meals"] = [m for m in nutrition.get("meals", []) if m.get("id")!=mid]
            save_json(NUTR_FILE, nutrition)
            self.load_meals()

    # ---------- Reports ----------
    def build_reports_tab(self):
        top = ttk.Frame(self.tab_rep); top.pack(fill="x", padx=6, pady=6)
        ttk.Label(top, text="Last 7 days (Calories / Protein)").pack(anchor="w")
        graph_frame = ttk.Frame(self.tab_rep); graph_frame.pack(expand=True, fill="both", padx=6, pady=6)

        # Two matplotlib figures side-by-side
        self.fig = plt.Figure(figsize=(9,4), dpi=100, facecolor="#222222")
        self.ax_cal = self.fig.add_subplot(121)
        self.ax_pro = self.fig.add_subplot(122)
        for ax in (self.ax_cal, self.ax_pro):
            ax.set_facecolor("#222222")
            ax.tick_params(colors="white")
            ax.title.set_color("white")
            ax.xaxis.label.set_color("white")
            ax.yaxis.label.set_color("white")

        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.get_tk_widget().pack(expand=True, fill="both")
        ttk.Button(self.tab_rep, text="Refresh", command=self.refresh_reports).pack(pady=6)
        self.refresh_reports()

    def refresh_reports(self):
        days = 7
        dates = []
        cal_vals = []
        pro_vals = []
        for d_i in range(days-1, -1, -1):
            d = (datetime.now().date() - timedelta(days=d_i)).strftime("%Y-%m-%d")
            dates.append(d)
            daily = [m for m in nutrition.get("meals", []) if m.get("date")==d]
            cal_vals.append(sum(m.get("calories",0) for m in daily))
            pro_vals.append(sum(m.get("protein",0) for m in daily))

        # plot calories
        self.ax_cal.clear()
        self.ax_cal.bar(dates, cal_vals)
        self.ax_cal.set_title("Calories (last 7 days)")
        self.ax_cal.tick_params(axis='x', rotation=45, colors="white")

        # plot protein
        self.ax_pro.clear()
        self.ax_pro.bar(dates, pro_vals)
        self.ax_pro.set_title("Protein (g) (last 7 days)")
        self.ax_pro.tick_params(axis='x', rotation=45, colors="white")

        self.fig.tight_layout()
        self.canvas.draw()

# ---------- Run ----------
if __name__ == "__main__":
    root = tk.Tk()
    app = FitSimple(root)
    root.mainloop()
