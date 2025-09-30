#!/usr/bin/env python3
"""
fittracker_modern.py
Modern red & black themed fitness tracker using ttkbootstrap.

- Requires: ttkbootstrap, matplotlib
- Run: python fittracker_modern.py
- Data files: workouts.json, nutrition.json (created in same folder)
"""

import json, os, uuid
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import messagebox, simpledialog
from tkinter import ttk
from ttkbootstrap import Style
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ---------- Files ----------
WORKOUT_FILE = "workouts.json"
NUTRITION_FILE = "nutrition.json"

# ---------- Simple JSON helpers ----------
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

# ---------- Data ----------
workouts = load_json(WORKOUT_FILE, {"sessions": []})
nutrition = load_json(NUTRITION_FILE, {"foods": {}, "meals": []})

# ---------- Utilities ----------
def make_id():
    return uuid.uuid4().hex

def today_str():
    return datetime.now().strftime("%Y-%m-%d")

def pretty_ts(ts=None):
    if not ts: ts = datetime.now().isoformat()
    return ts.replace("T", " ")[:19]

# ---------- App ----------
class FitTrackerModern:
    def __init__(self, root):
        # ttkbootstrap style - darkly
        self.style = Style(theme="darkly")
        self.root = root
        self.root.title("FitTracker — Modern")
        self.root.geometry("1000x650")

        # Notebook (tabs)
        self.nb = ttk.Notebook(root, style="Dark.TNotebook")
        self.nb.pack(expand=True, fill="both", padx=10, pady=10)

        # Tabs
        self.tab_workout = ttk.Frame(self.nb)
        self.tab_nutrition = ttk.Frame(self.nb)
        self.tab_reports = ttk.Frame(self.nb)
        self.nb.add(self.tab_workout, text="Workout")
        self.nb.add(self.tab_nutrition, text="Nutrition")
        self.nb.add(self.tab_reports, text="Reports")

        # Build tabs
        self.build_workout_tab()
        self.build_nutrition_tab()
        self.build_reports_tab()

    # ---------------- Workout Tab ----------------
    def build_workout_tab(self):
        left = ttk.Frame(self.tab_workout, padding=8)
        left.pack(side="left", fill="y")
        right = ttk.Frame(self.tab_workout, padding=8)
        right.pack(side="right", expand=True, fill="both")

        ttk.Label(left, text="Sessions", font=("Arial", 14)).pack(anchor="w", pady=(0,6))
        self.session_list = tk.Listbox(left, width=32, height=25, bg="#0f0f0f", fg="white", selectbackground="#5a1a1a")
        self.session_list.pack(pady=4)
        self.session_list.bind("<<ListboxSelect>>", lambda e: self.on_session_select())

        btn_add = ttk.Button(left, text="Add Session", bootstyle="danger-outline", command=self.add_session)
        btn_add.pack(fill="x", pady=6)
        btn_edit = ttk.Button(left, text="Edit Session", bootstyle="secondary", command=self.edit_session)
        btn_edit.pack(fill="x", pady=6)
        btn_delete = ttk.Button(left, text="Delete Session", bootstyle="danger", command=self.delete_session)
        btn_delete.pack(fill="x", pady=6)

        # Right: session detail
        ttk.Label(right, text="Session Details", font=("Arial", 14)).pack(anchor="w")
        self.session_header = ttk.Label(right, text="Select a session", font=("Arial", 11))
        self.session_header.pack(anchor="w", pady=(4,8))

        cols = ("Exercise", "Weight (kg)", "Reps")
        self.ex_tree = ttk.Treeview(right, columns=cols, show="headings", height=20)
        for c in cols:
            self.ex_tree.heading(c, text=c)
            self.ex_tree.column(c, anchor="center", width=160)
        self.ex_tree.pack(expand=True, fill="both", pady=(0,10))

        ex_btns = ttk.Frame(right)
        ex_btns.pack()
        ttk.Button(ex_btns, text="Add Exercise (best set)", bootstyle="success", command=self.add_exercise).grid(row=0,column=0,padx=6)
        ttk.Button(ex_btns, text="Edit Exercise", bootstyle="secondary", command=self.edit_exercise).grid(row=0,column=1,padx=6)
        ttk.Button(ex_btns, text="Delete Exercise", bootstyle="danger", command=self.delete_exercise).grid(row=0,column=2,padx=6)

        self.refresh_sessions()

    def refresh_sessions(self):
        self.session_list.delete(0, tk.END)
        # sort by date desc then name
        sessions = sorted(workouts["sessions"], key=lambda s: (s.get("date",""), s.get("created_at","")), reverse=True)
        for s in sessions:
            label = f"{s.get('date', s.get('created_at','')[:10])} — {s.get('name','')}"
            self.session_list.insert(tk.END, label)
        # keep original ordering in workouts["sessions"] (no reassign)

    def get_selected_session_index(self):
        sel = self.session_list.curselection()
        if not sel:
            return None
        # mapping: index in listbox -> session in workouts (sorted view)
        listbox_index = sel[0]
        sessions = sorted(workouts["sessions"], key=lambda s: (s.get("date",""), s.get("created_at","")), reverse=True)
        selected = sessions[listbox_index]
        # find its index in original workouts["sessions"]
        for i,s in enumerate(workouts["sessions"]):
            if s["id"] == selected.get("id"):
                return i
        # fallback: if no id (older entries), match by created_at+name
        for i,s in enumerate(workouts["sessions"]):
            if s.get("created_at","")==selected.get("created_at","") and s.get("name","")==selected.get("name",""):
                return i
        return None

    def on_session_select(self):
        idx = self.get_selected_session_index()
        if idx is None:
            self.session_header.config(text="Select a session")
            for iid in self.ex_tree.get_children(): self.ex_tree.delete(iid)
            return
        session = workouts["sessions"][idx]
        header = f"{session.get('date', session.get('created_at','')[:10])} — {session.get('name')}"
        self.session_header.config(text=header)
        # populate exercises
        for iid in self.ex_tree.get_children(): self.ex_tree.delete(iid)
        for ex in session.get("exercises", []):
            self.ex_tree.insert("", tk.END, iid=ex["id"], values=(ex["name"], ex["weight"], ex["reps"]))

    def add_session(self):
        name = simpledialog.askstring("Session name", "Enter session name (e.g., Push):", parent=self.root)
        if name is None: return
        date = simpledialog.askstring("Date", "Enter date (YYYY-MM-DD) or leave blank for today:", parent=self.root) or today_str()
        try:
            # validate
            datetime.strptime(date, "%Y-%m-%d")
        except Exception:
            messagebox.showerror("Invalid date", "Use YYYY-MM-DD")
            return
        session = {"id": make_id(), "name": name, "date": date, "created_at": datetime.now().isoformat(), "exercises": []}
        workouts["sessions"].append(session)
        save_json(WORKOUT_FILE, workouts)
        self.refresh_sessions()

    def edit_session(self):
        idx = self.get_selected_session_index()
        if idx is None:
            messagebox.showinfo("Select", "Select a session first")
            return
        session = workouts["sessions"][idx]
        new_name = simpledialog.askstring("Edit name", "New name (blank to keep):", initialvalue=session.get("name"), parent=self.root)
        if new_name:
            session["name"] = new_name
        new_date = simpledialog.askstring("Edit date", "New date YYYY-MM-DD (blank keep):", initialvalue=session.get("date"), parent=self.root)
        if new_date:
            try:
                datetime.strptime(new_date, "%Y-%m-%d")
                session["date"] = new_date
            except:
                messagebox.showerror("Invalid", "Date not changed")
        save_json(WORKOUT_FILE, workouts)
        self.refresh_sessions()
        self.on_session_select()

    def delete_session(self):
        idx = self.get_selected_session_index()
        if idx is None:
            messagebox.showinfo("Select", "Select a session")
            return
        s = workouts["sessions"][idx]
        if messagebox.askyesno("Confirm", f"Delete session '{s['name']}' on {s['date']}?"):
            workouts["sessions"].pop(idx)
            save_json(WORKOUT_FILE, workouts)
            self.refresh_sessions()
            self.on_session_select()

    def add_exercise(self):
        idx = self.get_selected_session_index()
        if idx is None:
            messagebox.showinfo("Select", "Select a session first")
            return
        name = simpledialog.askstring("Exercise", "Exercise name:", parent=self.root)
        if not name: return
        weight = simpledialog.askfloat("Weight (kg)", "Best set weight (kg):", parent=self.root)
        if weight is None: return
        reps = simpledialog.askinteger("Reps", "Best set reps:", parent=self.root)
        if reps is None: return
        ex = {"id": make_id(), "name": name, "weight": round(float(weight),2), "reps": int(reps)}
        workouts["sessions"][idx].setdefault("exercises", []).append(ex)
        save_json(WORKOUT_FILE, workouts)
        self.on_session_select()

    def edit_exercise(self):
        idx = self.get_selected_session_index()
        if idx is None:
            messagebox.showinfo("Select", "Select a session first")
            return
        session = workouts["sessions"][idx]
        sel = self.ex_tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Select an exercise")
            return
        ex_id = sel[0]
        ex = next((e for e in session.get("exercises", []) if e["id"]==ex_id), None)
        if not ex:
            return
        new_name = simpledialog.askstring("Name", "New name (blank keep):", initialvalue=ex["name"], parent=self.root)
        if new_name: ex["name"] = new_name
        w = simpledialog.askstring("Weight", "Weight (kg) (blank keep):", initialvalue=str(ex["weight"]), parent=self.root)
        if w:
            try: ex["weight"] = round(float(w),2)
            except: messagebox.showerror("Invalid","Weight not changed")
        r = simpledialog.askstring("Reps", "Reps (blank keep):", initialvalue=str(ex["reps"]), parent=self.root)
        if r:
            try: ex["reps"] = int(r)
            except: messagebox.showerror("Invalid","Reps not changed")
        save_json(WORKOUT_FILE, workouts)
        self.on_session_select()

    def delete_exercise(self):
        idx = self.get_selected_session_index()
        if idx is None:
            messagebox.showinfo("Select", "Select a session first")
            return
        session = workouts["sessions"][idx]
        sel = self.ex_tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Select an exercise")
            return
        ex_id = sel[0]
        if messagebox.askyesno("Confirm", "Delete selected exercise?"):
            session["exercises"] = [e for e in session.get("exercises", []) if e["id"]!=ex_id]
            save_json(WORKOUT_FILE, workouts)
            self.on_session_select()

    # ---------------- Nutrition Tab ----------------
    def build_nutrition_tab(self):
        top = ttk.Frame(self.tab_nutrition, padding=8)
        top.pack(side="top", fill="x")
        mid = ttk.Frame(self.tab_nutrition, padding=8)
        mid.pack(side="top", fill="both", expand=True)
        bottom = ttk.Frame(self.tab_nutrition, padding=8)
        bottom.pack(side="bottom", fill="x")

        # Foods tree (with name)
        ttk.Label(top, text="Foods (per 100g)", font=("Arial", 12)).pack(anchor="w", pady=(0,6))
        cols = ("Name","Calories","Protein")
        self.foods_tree = ttk.Treeview(top, columns=cols, show="headings", height=6)
        for c in cols:
            self.foods_tree.heading(c, text=c)
            self.foods_tree.column(c, anchor="center", width=200 if c=="Name" else 120)
        self.foods_tree.pack(expand=True, fill="x")
        self.refresh_foods()

        food_btns = ttk.Frame(top)
        food_btns.pack(pady=6)
        ttk.Button(food_btns, text="Add Food", bootstyle="success-outline", command=self.add_food).grid(row=0,column=0,padx=6)
        ttk.Button(food_btns, text="Edit Food", bootstyle="secondary", command=self.edit_food).grid(row=0,column=1,padx=6)
        ttk.Button(food_btns, text="Delete Food", bootstyle="danger", command=self.delete_food).grid(row=0,column=2,padx=6)

        # Meals area
        ttk.Label(mid, text="Meals (by date)", font=("Arial", 12)).pack(anchor="w", pady=(6,6))
        dframe = ttk.Frame(mid)
        dframe.pack(fill="x", pady=(0,8))
        ttk.Label(dframe, text="Date (YYYY-MM-DD):").pack(side="left", padx=(0,6))
        self.meal_date_var = tk.StringVar(value=today_str())
        ttk.Entry(dframe, textvariable=self.meal_date_var, width=12).pack(side="left")
        ttk.Button(dframe, text="Load", bootstyle="primary", command=self.load_meals_for_date).pack(side="left", padx=6)

        mcols = ("Time","Food","Grams","Calories","Protein")
        self.meals_tree = ttk.Treeview(mid, columns=mcols, show="headings", height=10)
        for c in mcols:
            self.meals_tree.heading(c, text=c)
            self.meals_tree.column(c, anchor="center", width=140)
        self.meals_tree.pack(expand=True, fill="both")

        meal_btns = ttk.Frame(mid)
        meal_btns.pack(pady=8)
        ttk.Button(meal_btns, text="Log Meal", bootstyle="danger", command=self.add_meal).grid(row=0,column=0,padx=6)
        ttk.Button(meal_btns, text="Edit Meal", bootstyle="secondary", command=self.edit_meal).grid(row=0,column=1,padx=6)
        ttk.Button(meal_btns, text="Delete Meal", bootstyle="danger-outline", command=self.delete_meal).grid(row=0,column=2,padx=6)

        # daily totals area
        self.totals_box = tk.Text(bottom, height=4, bg="#0f0f0f", fg="white")
        self.totals_box.pack(fill="x", padx=6, pady=6)
        self.load_meals_for_date()

    def refresh_foods(self):
        for iid in self.foods_tree.get_children(): self.foods_tree.delete(iid)
        for name, data in nutrition["foods"].items():
            self.foods_tree.insert("", tk.END, iid=name, values=(name, data["cal_per_100g"], data["protein_per_100g"]))

    def add_food(self):
        name = simpledialog.askstring("Food name", "Name of food (e.g., Paneer):", parent=self.root)
        if not name: return
        if name in nutrition["foods"]:
            messagebox.showinfo("Exists", "Food exists - use Edit")
            return
        cal = simpledialog.askfloat("Calories per 100g", "Calories per 100g:", parent=self.root)
        if cal is None: return
        prot = simpledialog.askfloat("Protein per 100g", "Protein (g) per 100g:", parent=self.root)
        if prot is None: return
        nutrition["foods"][name] = {"cal_per_100g": round(float(cal),2), "protein_per_100g": round(float(prot),2)}
        save_json(NUTRITION_FILE, nutrition)
        self.refresh_foods()

    def edit_food(self):
        sel = self.foods_tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Select a food")
            return
        name = sel[0]
        cur = nutrition["foods"].get(name, {})
        cal = simpledialog.askfloat("Calories per 100g", "Calories per 100g:", initialvalue=cur.get("cal_per_100g"), parent=self.root)
        if cal is None: return
        prot = simpledialog.askfloat("Protein per 100g", "Protein (g) per 100g:", initialvalue=cur.get("protein_per_100g"), parent=self.root)
        if prot is None: return
        nutrition["foods"][name] = {"cal_per_100g": round(float(cal),2), "protein_per_100g": round(float(prot),2)}
        save_json(NUTRITION_FILE, nutrition)
        self.refresh_foods()
        self.load_meals_for_date()

    def delete_food(self):
        sel = self.foods_tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Select a food")
            return
        name = sel[0]
        if messagebox.askyesno("Confirm", f"Delete food '{name}'? This also removes meals with this food."):
            nutrition["foods"].pop(name, None)
            nutrition["meals"] = [m for m in nutrition["meals"] if m["food"] != name]
            save_json(NUTRITION_FILE, nutrition)
            self.refresh_foods()
            self.load_meals_for_date()

    def load_meals_for_date(self):
        date = self.meal_date_var.get().strip() or today_str()
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except:
            messagebox.showerror("Invalid", "Use YYYY-MM-DD")
            return
        # clear tree
        for iid in self.meals_tree.get_children(): self.meals_tree.delete(iid)
        rows = [m for m in nutrition["meals"] if m.get("date")==date]
        for m in rows:
            self.meals_tree.insert("", tk.END, iid=m["id"], values=(m.get("time"), m.get("food"), m.get("grams"), m.get("calories"), m.get("protein")))
        tot_cal = sum(m.get("calories",0) for m in rows)
        tot_pro = sum(m.get("protein",0) for m in rows)
        self.totals_box.delete("1.0", tk.END)
        self.totals_box.insert(tk.END, f"Date: {date}\nTotal Calories: {round(tot_cal,2)} kcal\nTotal Protein: {round(tot_pro,2)} g")
        save_json(NUTRITION_FILE, nutrition)

    def add_meal(self):
        if not nutrition["foods"]:
            messagebox.showinfo("No foods", "Add foods first")
            return
        date = self.meal_date_var.get().strip() or today_str()
        try: datetime.strptime(date, "%Y-%m-%d")
        except:
            messagebox.showerror("Invalid", "Use YYYY-MM-DD"); return
        # let user pick food via a simple selection dialog listing food names
        foods = list(nutrition["foods"].keys())
        choice = simpledialog.askstring("Food", f"Type food name exactly from: {', '.join(foods)}", parent=self.root)
        if not choice or choice not in nutrition["foods"]:
            messagebox.showerror("Invalid", "Food name not found"); return
        grams = simpledialog.askfloat("Grams", "Enter grams consumed:", parent=self.root)
        if grams is None: return
        f = nutrition["foods"][choice]
        factor = grams/100.0
        cal = round(f["cal_per_100g"] * factor, 2)
        prot = round(f["protein_per_100g"] * factor, 2)
        meal = {
            "id": make_id(),
            "timestamp": datetime.now().isoformat(),
            "date": date,
            "time": datetime.now().strftime("%H:%M:%S"),
            "food": choice,
            "grams": round(float(grams),2),
            "calories": cal,
            "protein": prot
        }
        nutrition["meals"].append(meal)
        save_json(NUTRITION_FILE, nutrition)
        self.load_meals_for_date()

    def edit_meal(self):
        sel = self.meals_tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Select a meal")
            return
        mid = sel[0]
        meal = next((m for m in nutrition["meals"] if m["id"]==mid), None)
        if not meal:
            return
        grams = simpledialog.askfloat("Grams", "Enter grams:", initialvalue=meal.get("grams"), parent=self.root)
        if grams is None: return
        food = meal["food"]
        if food not in nutrition["foods"]:
            messagebox.showerror("Missing", "Food not in DB"); return
        f = nutrition["foods"][food]
        meal["grams"] = round(float(grams),2)
        meal["calories"] = round(f["cal_per_100g"] * (grams/100.0),2)
        meal["protein"] = round(f["protein_per_100g"] * (grams/100.0),2)
        save_json(NUTRITION_FILE, nutrition)
        self.load_meals_for_date()

    def delete_meal(self):
        sel = self.meals_tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Select a meal")
            return
        mid = sel[0]
        if messagebox.askyesno("Confirm", "Delete selected meal?"):
            nutrition["meals"] = [m for m in nutrition["meals"] if m["id"]!=mid]
            save_json(NUTRITION_FILE, nutrition)
            self.load_meals_for_date()

    # ---------------- Reports Tab ----------------
    def build_reports_tab(self):
        top = ttk.Frame(self.tab_reports, padding=8)
        top.pack(side="top", fill="x")
        ttk.Label(top, text="Show trend for last N days:", font=("Arial", 11)).pack(side="left", padx=(0,6))
        self.trend_var = tk.IntVar(value=14)
        ttk.Entry(top, textvariable=self.trend_var, width=6).pack(side="left")
        ttk.Button(top, text="Refresh", bootstyle="primary", command=self.refresh_reports).pack(side="left", padx=8)

        graphs_frame = ttk.Frame(self.tab_reports, padding=8)
        graphs_frame.pack(expand=True, fill="both")

        # Two canvases side-by-side
        self.fig_cal = plt.Figure(figsize=(6,3), dpi=100, facecolor="black")
        self.ax_cal = self.fig_cal.add_subplot(111)
        self.canvas_cal = FigureCanvasTkAgg(self.fig_cal, master=graphs_frame)
        self.canvas_cal.get_tk_widget().pack(side="left", expand=True, fill="both", padx=6, pady=6)

        self.fig_pro = plt.Figure(figsize=(6,3), dpi=100, facecolor="black")
        self.ax_pro = self.fig_pro.add_subplot(111)
        self.canvas_pro = FigureCanvasTkAgg(self.fig_pro, master=graphs_frame)
        self.canvas_pro.get_tk_widget().pack(side="left", expand=True, fill="both", padx=6, pady=6)

        # set dark axis colors once
        for ax in (self.ax_cal, self.ax_pro):
            ax.set_facecolor("black")
            ax.tick_params(colors="white")
            ax.title.set_color("white")
            ax.xaxis.label.set_color("white")
            ax.yaxis.label.set_color("white")

        self.refresh_reports()

    def refresh_reports(self):
        days = max(1, int(self.trend_var.get() or 14))
        dates = []
        cal_vals = []
        pro_vals = []
        for d_i in range(days-1, -1, -1):
            d = (datetime.now().date() - timedelta(days=d_i)).strftime("%Y-%m-%d")
            dates.append(d)
            daily = [m for m in nutrition["meals"] if m.get("date")==d]
            cal_vals.append(sum(m.get("calories",0) for m in daily))
            pro_vals.append(sum(m.get("protein",0) for m in daily))

        # Calories plot (red)
        self.ax_cal.clear()
        self.ax_cal.set_facecolor("black")
        self.ax_cal.plot(dates, cal_vals, marker='o', color="#FF5A5A")
        self.ax_cal.set_title("Calories (last {} days)".format(days))
        self.ax_cal.tick_params(axis='x', rotation=45, colors="white")
        self.ax_cal.tick_params(axis='y', colors="white")
        self.fig_cal.tight_layout()
        self.canvas_cal.draw()

        # Protein plot (blue)
        self.ax_pro.clear()
        self.ax_pro.set_facecolor("black")
        self.ax_pro.plot(dates, pro_vals, marker='o', color="#4FA3FF")
        self.ax_pro.set_title("Protein (g) (last {} days)".format(days))
        self.ax_pro.tick_params(axis='x', rotation=45, colors="white")
        self.ax_pro.tick_params(axis='y', colors="white")
        self.fig_pro.tight_layout()
        self.canvas_pro.draw()

# ---------- Run ----------
if __name__ == "__main__":
    root = tk.Tk()
    app = FitTrackerModern(root)
    root.mainloop()
