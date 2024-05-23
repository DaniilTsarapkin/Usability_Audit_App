import tkinter as tk
from tkinter import ttk
import sqlite3
from tkinter import messagebox
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter.font as tkFont
from datetime import datetime
editing_checklist_flag = 0
delited_checlist_id = 0

def configure_style():
    style = ttk.Style()
    font = tkFont.Font(family="Calibri", size=12, weight="bold")
    style.configure('TButton', background='#222222', foreground='white', font=font)
    style.map('TButton', background=[('active', '#8774e1')])
    style.configure('Close.TButton', background='#828282', foreground='#222222', font=font)
    style.map('Close.TButton', foreground=[('active', 'black')], background=[('active', '#8774e1')])
    style.configure('TLabel', background='#222222', foreground='white', font=font)
    style.configure('TFrame', background='#222222')
    style.configure('TEntry', foreground='#222222', background='#222222', font=font)
    style.configure('TRadiobutton', foreground='white', background='#222222', focuscolor='white', font=font)
    style.map('TRadiobutton', foreground=[('active', '#8774e1')], background=[('active', '#222222')])
    style.configure("Custom.Treeview", background="#222222", foreground="white", font=font)

def close_window(window):
    window.destroy()
    root.deiconify()

def validate_date(date_text):
    try:
        datetime.strptime(date_text, '%d.%m.%Y')
        return True
    except ValueError:
        return False

class UsabilityAuditApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Usability Audit App")
        self.root.geometry("1600x900")
        style = ttk.Style()
        style.theme_use('clam')
        self.root.configure(background='#222222')
        configure_style()
        self.filtered_window = None

        self.conn = sqlite3.connect("usability_audit.db")
        self.cursor = self.conn.cursor()

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS checklists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                product TEXT,
                version TEXT,
                date TEXT,
                comment TEXT 
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS criteria (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                checklist_id INTEGER,
                criterion TEXT,
                evaluation TEXT,
                source TEXT,
                comment TEXT,
                FOREIGN KEY(checklist_id) REFERENCES checklists(id)
            )
        ''')

        self.conn.commit()

        self.create_button = ttk.Button(root, text="Создать чек-лист", width=40, style='TButton',
                                        command=self.create_checklist)
        self.create_button.pack(pady=10)

        self.view_button = ttk.Button(root, text="Просмотреть чек-листы", width=40, style='TButton',
                                      command=self.view_checklists)
        self.view_button.pack(pady=10)

        self.exit_button = ttk.Button(root, text="Выйти", width=40, style='Close.TButton', command=root.destroy)
        self.exit_button.pack(pady=10)

        self.load_checklists()

        root.bind_all("<MouseWheel>", self.on_mousewheel)
        root.bind_all("<Button-4>", self.on_mousewheel)
        root.bind_all("<Button-5>", self.on_mousewheel)

    def load_checklists(self):
        self.cursor.execute("SELECT * FROM checklists")
        checklists = self.cursor.fetchall()

    def create_checklist(self):
        self.create_window = tk.Toplevel(self.root)
        self.create_window.title("Создание чек-листа")
        self.create_window.geometry("1600x900")
        style = ttk.Style()
        style.theme_use('clam')

        self.create_window.configure(background='#222222')
        configure_style()
        root.withdraw()
        self.create_window.protocol("WM_DELETE_WINDOW", lambda: close_window(self.create_window))

        canvas = tk.Canvas(self.create_window, background='#222222')
        canvas.pack(side="left", fill="both", expand=True)

        frame = ttk.Frame(canvas, style='TFrame')
        frame.pack(side="left", fill="both", expand=True)

        frame.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"))
        frame.bind_all("<Button-4>", lambda event: canvas.yview_scroll(-1, "units"))
        frame.bind_all("<Button-5>", lambda event: canvas.yview_scroll(1, "units"))

        canvas.create_window((0, 0), window=frame, anchor="nw")

        scrollbar = ttk.Scrollbar(self.create_window, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=scrollbar.set)

        name_label = ttk.Label(frame, text="Аудитор:", style='TLabel')
        name_label.grid(row=0, column=0, padx=(20, 0), pady=5, sticky='w')
        self.name_entry = ttk.Entry(frame, style='TEntry')
        self.name_entry.grid(row=0, column=1, padx=10, pady=5, sticky='w')

        product_label = ttk.Label(frame, text="Продукт:", style='TLabel')
        product_label.grid(row=1, column=0, padx=(20, 0), pady=5, sticky='w')
        self.product_entry = ttk.Entry(frame, style='TEntry')
        self.product_entry.grid(row=1, column=1, padx=10, pady=5, sticky='w')

        version_label = ttk.Label(frame, text="Версия:", style='TLabel')
        version_label.grid(row=2, column=0, padx=(20, 0), pady=5, sticky='w')
        self.version_entry = ttk.Entry(frame, style='TEntry')
        self.version_entry.grid(row=2, column=1, padx=10, pady=5, sticky='w')

        date_label = ttk.Label(frame, text="Дата (ДД.ММ.ГГГГ):", style='TLabel')
        date_label.grid(row=3, column=0, padx=(20, 0), pady=5, sticky='w')
        self.date_entry = ttk.Entry(frame, style='TEntry')
        self.date_entry.grid(row=3, column=1, padx=10, pady=5, sticky='w')

        add_button = ttk.Button(frame, text="+10", style='TButton',
                                command=lambda: self.add_criterion_entry(frame))
        add_button.grid(row=5, column=0, padx=(20, 0), pady=5, sticky='w')

        remove_button = ttk.Button(frame, text="-1", style='TButton', command=self.remove_criterion_entry)
        remove_button.grid(row=5, column=1, padx=5, pady=5, sticky='w')

        evaluate_button = ttk.Button(frame, text="Оценить", style='TButton', command=self.show_evaluation)
        evaluate_button.grid(row=5, column=2, padx=5, pady=5, sticky='w')

        close_button = ttk.Button(frame, text="Вернуться назад", command=lambda: close_window(self.create_window),
                                  style='Close.TButton')
        close_button.grid(row=5, column=3, columnspan=3, padx=(20, 0), pady=5, sticky='w')

        self.criteria_entries = [self.create_criterion_entry(frame, i + 1) for i in range(30)]

        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    def create_criterion_entry(self, parent, number):
        criterion_frame = ttk.Frame(parent, style='TFrame')
        if ((number - 1) // 10) % 2 == 0:
            if number % 10 == 0:
                criterion_frame.grid(row=6 + number - 1, column=0, columnspan=4, padx=(20, 80), pady=(0, 30),
                                     sticky='w')
            else:
                criterion_frame.grid(row=6 + number - 1, column=0, columnspan=4, padx=(20, 80), pady=5, sticky='w')

        elif ((number - 1) // 10) % 2 == 1:
            if number % 10 == 0:
                criterion_frame.grid(row=6 + number - 11, column=4, columnspan=4, padx=(0, 80), pady=(0, 30),
                                     sticky='w')
            else:
                criterion_frame.grid(row=6 + number - 11, column=4, columnspan=4, padx=(0, 80), pady=5, sticky='w')

        criterion = ttk.Label(criterion_frame, text="Критерий №: ", style='TLabel')
        source = ttk.Label(criterion_frame, text="Источник:", style='TLabel')
        criterion_label_text = f"  {number}: " if number < 10 else f"{number}: "
        criterion_label = ttk.Label(criterion_frame, text=criterion_label_text, style='TLabel')
        criterion_var = tk.StringVar()
        criterion_entry = ttk.Entry(criterion_frame, textvariable=criterion_var, width=35, style='TEntry')
        source_var = tk.StringVar()
        source_entry = ttk.Entry(criterion_frame, textvariable=source_var)

        if (number - 1) % 10 == 0:
            criterion.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky='w')
            source.grid(row=0, column=2, columnspan=4, padx=5, pady=5, sticky='w')
            criterion_label.grid(row=1, column=0, padx=5, pady=5, sticky='w')
            criterion_entry.grid(row=1, column=1, padx=(0, 40), pady=5, sticky='w')
            source_entry.grid(row=1, column=2, padx=(0, 5), pady=5, sticky='w')

        else:
            criterion_label.grid(row=0, column=0, padx=5, pady=5, sticky='w')
            criterion_entry.grid(row=0, column=1, padx=(0, 40), pady=5, sticky='w')
            source_entry.grid(row=0, column=2, padx=(0, 5), pady=5, sticky='w')

        return criterion_frame, criterion_var, source_var

    def add_criterion_entry(self, parent_frame):
        for i in range(10):
            new_number = len(self.criteria_entries) + 1
            criterion_frame, criterion_entry, source_entry = self.create_criterion_entry(parent_frame, new_number)
            self.criteria_entries.append((criterion_frame, criterion_entry, source_entry))

    def remove_criterion_entry(self):
        if len(self.criteria_entries) > 1:
            criterion_frame, _, _ = self.criteria_entries.pop(-1)
            criterion_frame.destroy()

    def show_evaluation(self):
        name = self.name_entry.get()
        product = self.product_entry.get()
        version = self.version_entry.get()
        date = self.date_entry.get()

        if not name or not product or not version or not date:
            messagebox.showwarning("Внимание", "Пожалуйста, заполните все поля.")
            return
        elif not validate_date(date):
            messagebox.showwarning("Внимание", "Пожалуйста, введите корректную дату.")
            return

        self.cursor.execute('''
            INSERT INTO checklists (name, product, version, date) VALUES (?, ?, ?, ?)
        ''', (name, product, version, date))
        self.conn.commit()
        checklist_id = self.cursor.lastrowid

        self.evaluation_window = tk.Toplevel(self.root)
        self.evaluation_window.title("Оценка по критериям")
        self.evaluation_window.geometry("1600x900")
        self.evaluation_window.protocol("WM_DELETE_WINDOW", lambda: close_window(self.evaluation_window))
        style = ttk.Style()
        style.theme_use('clam')
        self.root.configure(background='#222222')
        configure_style()

        eval_canvas = tk.Canvas(self.evaluation_window, background='#222222')
        eval_canvas.pack(side="left", fill="both", expand=True)

        eval_frame = ttk.Frame(eval_canvas, style='TFrame')
        eval_frame.pack(side="left", fill="both", expand=True)

        eval_frame.bind_all("<MouseWheel>",
                            lambda event: eval_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"))
        eval_frame.bind_all("<Button-4>", lambda event: eval_canvas.yview_scroll(-1, "units"))
        eval_frame.bind_all("<Button-5>", lambda event: eval_canvas.yview_scroll(1, "units"))

        eval_canvas.create_window((0, 0), window=eval_frame, anchor="nw")

        eval_scrollbar = ttk.Scrollbar(self.evaluation_window, orient="vertical", command=eval_canvas.yview)
        eval_scrollbar.pack(side="right", fill="y")
        eval_canvas.configure(yscrollcommand=eval_scrollbar.set)

        criterion = ttk.Label(eval_frame, text="Критерий №: ", style='TLabel')
        criterion.grid(row=0, column=0, padx=(20, 0), pady=5, sticky='w')
        grades = ttk.Label(eval_frame, text="Оценки: ", style='TLabel')
        grades.grid(row=0, column=1, columnspan=2, padx=10, pady=5, sticky='w')
        source = ttk.Label(eval_frame, text="Источник:", style='TLabel')
        source.grid(row=0, column=4, padx=10, pady=5, sticky='w')
        comment = ttk.Label(eval_frame, text="Комментарии:", style='TLabel')
        comment.grid(row=0, column=5, padx=10, pady=5, sticky='w')
        comment_label = ttk.Label(eval_frame, text="Общий комментарий:", style='TLabel')
        comment_label.grid(row=0, column=6, padx=10, pady=5, sticky='w')
        self.comment_text = tk.Text(eval_frame, width=50, height=10)
        self.comment_text.grid(row=1, column=6, rowspan=5, columnspan=5, padx=10, pady=5, sticky='nsew')
        save_button = ttk.Button(eval_frame, text="Сохранить", command=lambda: self.save_evaluation(checklist_id))
        save_button.grid(row=6, column=6, padx=10, pady=5, sticky='w')
        close_button = ttk.Button(eval_frame, text="Вернуться назад", command=lambda: self.evaluation_window.destroy(),
                                  style='Close.TButton')
        close_button.grid(row=7, column=6, padx=10, pady=5, sticky='w')

        self.evaluation_vars = []
        for i, (criterion_frame, criterion_entry, source_entry) in enumerate(self.criteria_entries):
            criterion_value = criterion_entry.get().strip()
            source_value = source_entry.get().strip()
            if criterion_value:
                crit_text = f"{i + 1}:   {criterion_value}" if i + 1 < 10 else f"{i + 1}: {criterion_value}"
                criterion_label = ttk.Label(eval_frame, text=crit_text, style='TLabel')
                evaluation_var = tk.StringVar()

                self.cursor.execute("SELECT evaluation, comment FROM criteria WHERE checklist_id=? AND criterion=?",
                                    (checklist_id - 1, criterion_value))

                evaluation_data = self.cursor.fetchone()
                evaluation_value = evaluation_data[0] if evaluation_data else ""
                comment_data = self.cursor.fetchone()
                comment_value = comment_data[0] if comment_data else ""

                evaluation_var = tk.StringVar(value=evaluation_value)
                comment_var = tk.StringVar(value=comment_value)

                yes_radio = ttk.Radiobutton(eval_frame, text="Yes", variable=evaluation_var, value="Yes",
                                            style='TRadiobutton')
                no_radio = ttk.Radiobutton(eval_frame, text="No", variable=evaluation_var, value="No",
                                           style='TRadiobutton')
                partial_radio = ttk.Radiobutton(eval_frame, text="Partial", variable=evaluation_var, value="Partial",
                                                style='TRadiobutton')
                source_label = ttk.Label(eval_frame, text=f"{source_value}", style='TLabel')
                comment_var = tk.StringVar()
                comment_entry = ttk.Entry(eval_frame, textvariable=comment_var, style='TEntry')

                if (i + 1) % 11 == 0:
                    criterion_label.grid(row=i + 1, column=0, padx=(20, 20), pady=(20, 0), sticky='nw')
                    yes_radio.grid(row=i + 1, column=1, padx=10, pady=(20, 0), sticky='n')
                    no_radio.grid(row=i + 1, column=2, padx=10, pady=(20, 0), sticky='n')
                    partial_radio.grid(row=i + 1, column=3, padx=(0, 50), pady=(20, 0), sticky='n')
                    source_label.grid(row=i + 1, column=4, padx=(0, 50), pady=(20, 0), sticky='n')
                    comment_entry.grid(row=i + 1, column=5, padx=(0, 100), pady=(20, 0), sticky='n')
                else:
                    criterion_label.grid(row=i + 1, column=0, padx=(20, 50), pady=5, sticky='w')
                    yes_radio.grid(row=i + 1, column=1, padx=10, pady=5)
                    no_radio.grid(row=i + 1, column=2, padx=10, pady=5)
                    partial_radio.grid(row=i + 1, column=3, padx=(0, 50), pady=5)
                    source_label.grid(row=i + 1, column=4, padx=(0, 50), pady=5)
                    comment_entry.grid(row=i + 1, column=5, padx=(0, 100), pady=5)

                self.evaluation_vars.append((evaluation_var, comment_var))
        deleted_checklist_id = checklist_id - 1
        if not self.evaluation_vars:
            messagebox.showwarning("Внимание", "Необходимо заполнить хотя бы один критерий.")
            self.evaluation_window.destroy()
            return

        eval_frame.bind("<Configure>", lambda e: eval_canvas.configure(scrollregion=eval_canvas.bbox("all")))

    def save_evaluation(self, checklist_id):
        self.cursor.execute("DELETE FROM criteria WHERE checklist_id=?", (checklist_id,))

        all_evaluations_given = any(var[0].get() for var in self.evaluation_vars)

        if not all_evaluations_given:
            messagebox.showwarning("Предупреждение",
                                   "Пожалуйста, выставите хотя бы одну оценку.")
        else:

            for entry, (evaluation, comment) in zip(self.criteria_entries, self.evaluation_vars):
                criterion_value = entry[1].get().strip()
                evaluation_value = evaluation.get()
                comment_value = comment.get()
                source_value = entry[2].get().strip()

                if criterion_value:
                    self.cursor.execute('''
                        INSERT INTO criteria (checklist_id, criterion, evaluation, source, comment) VALUES (?, ?, ?, ?, ?)
                    ''', (checklist_id, criterion_value, evaluation_value, source_value, comment_value))

            overall_comment_value = self.comment_text.get("1.0", "end-1c")

            self.comment_text_value = overall_comment_value

            self.cursor.execute("UPDATE checklists SET comment=? WHERE id=?", (overall_comment_value, checklist_id))
            self.conn.commit()
            messagebox.showinfo("Успешно", "Оценки сохранены успешно.")
            close_window(self.create_window)
            self.evaluation_window.destroy()

            self.one_checklist(
                self.cursor.execute("SELECT * FROM checklists WHERE id=?", (checklist_id,)).fetchone())
        global editing_checklist_flag
        global delited_checlist_id
        if editing_checklist_flag == 1:
            self.delete_checklist(delited_checlist_id, False, True)
            editing_checklist_flag = 0

    def view_checklists(self):
        self.view_window = tk.Toplevel(self.root)
        self.view_window.title("Просмотр чек-листов")
        self.view_window.geometry("1600x900")
        style = ttk.Style()
        style.theme_use('clam')
        self.view_window.configure(background='#222222')
        root.withdraw()
        self.view_window.protocol("WM_DELETE_WINDOW", lambda: close_window(self.view_window))
        view_canvas = tk.Canvas(self.view_window, background='#222222')
        view_canvas.pack(side="left", fill="both", expand=True)

        view_frame = ttk.Frame(view_canvas, style='TFrame')
        view_frame.pack(side="left", fill="both", expand=True)

        view_frame.bind_all("<MouseWheel>",
                            lambda event: view_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"))
        view_frame.bind_all("<Button-4>", lambda event: view_canvas.yview_scroll(-1, "units"))
        view_frame.bind_all("<Button-5>", lambda event: view_canvas.yview_scroll(1, "units"))

        view_canvas.create_window((0, 0), window=view_frame, anchor="nw")

        view_scrollbar = ttk.Scrollbar(self.view_window, orient="vertical", command=view_canvas.yview)
        view_scrollbar.pack(side="right", fill="y")
        view_canvas.configure(yscrollcommand=view_scrollbar.set)

        checklist_label = ttk.Label(view_frame, text="Чек-листы", font=("Calibri", 24, "bold"))
        checklist_label.grid(row=0, column=0, columnspan=3, pady=10, padx=10, sticky="w")
        search_label = ttk.Label(view_frame, text="Поиск чек-листов:", font=("Calibri", 18))
        search_label.grid(row=1, column=5, columnspan=3, pady=10, padx=(40, 0), sticky="w")
        self.search_entry = ttk.Entry(view_frame, style='TEntry')
        self.search_entry.grid(row=2, column=5, columnspan=3, padx=(40, 0), pady=10, sticky="ew")
        search_button = ttk.Button(view_frame, text="Искать", command=self.filter_checklists)
        search_button.grid(row=2, column=8, padx=10, pady=5)
        close_button = ttk.Button(view_frame, text="Вернуться назад", command=lambda: close_window(self.view_window),
                                  style='Close.TButton')
        close_button.grid(row=0, column=8, padx=10, pady=5, sticky='w')

        self.cursor.execute("SELECT * FROM checklists")
        checklists = self.cursor.fetchall()

        for i, checklist in enumerate(checklists):
            checklist_info = f"{checklist[1]} - {checklist[2]} - {checklist[3]} - {checklist[4]}"
            checklist_label = ttk.Label(view_frame, text=checklist_info, style='TLabel')
            checklist_label.grid(row=i + 1, column=0, columnspan=2, pady=5, padx=10, sticky="w")
            view_button = ttk.Button(view_frame, text="Просмотреть", command=lambda c=checklist: self.one_checklist(c))
            view_button.grid(row=i + 1, column=2, pady=5, padx=10, sticky="w")
            delete_button = ttk.Button(view_frame, text="Удалить",
                                       command=lambda c=checklist, w=view_frame: self.delete_checklist(c[0], w),
                                       style='Close.TButton')
            delete_button.grid(row=i + 1, column=3, pady=5, padx=10, sticky="w")

        view_frame.bind("<Configure>", lambda e: view_canvas.configure(scrollregion=view_canvas.bbox("all")))

    def delete_checklist(self, checklist_id, window_to_close, redacting_flag = False):
        self.cursor.execute("DELETE FROM checklists WHERE id=?", (checklist_id,))
        self.conn.commit()
        if not redacting_flag:
            messagebox.showinfo("Успешно", "Чек-лист успешно удален.")

        if window_to_close:
            window_to_close.destroy()

        self.view_checklists()

    def filter_checklists(self):
        search_text = self.search_entry.get().strip().lower()
        self.view_window.destroy()

        self.cursor.execute(
            "SELECT * FROM checklists WHERE LOWER(name) LIKE ? OR LOWER(product) LIKE ? OR LOWER(date) LIKE ?",
            ('%' + search_text + '%', '%' + search_text + '%', '%' + search_text + '%'))
        filtered_checklists = self.cursor.fetchall()

        if self.filtered_window:
            self.filtered_window.destroy()
        self.filtered_window = tk.Toplevel(self.root)
        self.filtered_window.title("Отфильтрованные чек-листы")
        self.filtered_window.geometry("1600x900")
        style = ttk.Style()
        style.theme_use('clam')
        self.filtered_window.configure(background='#222222')
        root.withdraw()
        self.filtered_window.protocol("WM_DELETE_WINDOW", lambda: close_window(self.filtered_window))

        filter_canvas = tk.Canvas(self.filtered_window, background='#222222')
        filter_canvas.pack(side="left", fill="both", expand=True)

        filter_frame = ttk.Frame(filter_canvas, style='TFrame')
        filter_frame.pack(side="left", fill="both", expand=True)

        filter_frame.bind_all("<MouseWheel>",
                              lambda event: filter_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"))
        filter_frame.bind_all("<Button-4>", lambda event: filter_canvas.yview_scroll(-1, "units"))
        filter_frame.bind_all("<Button-5>", lambda event: filter_canvas.yview_scroll(1, "units"))

        filter_canvas.create_window((0, 0), window=filter_frame, anchor="nw")

        filter_scrollbar = ttk.Scrollbar(self.filtered_window, orient="vertical", command=filter_canvas.yview)
        filter_scrollbar.pack(side="right", fill="y")
        filter_canvas.configure(yscrollcommand=filter_scrollbar.set)

        found_label = ttk.Label(filter_frame, text="Найденные чек-листы", font=("Calibri", 24, "bold"))
        found_label.grid(row=0, column=0, columnspan=3, pady=10, padx=10, sticky="w")
        return_all_button = ttk.Button(filter_frame, text="Вернуть все критерии", command=self.return_all_checklists,
                                       style='Close.TButton')
        return_all_button.grid(row=0, column=3, columnspan=5, pady=5, padx=10, sticky="w")

        for i, checklist in enumerate(filtered_checklists):
            checklist_info = f"{checklist[1]} - {checklist[2]} - {checklist[3]} - {checklist[4]}"
            checklist_label = ttk.Label(filter_frame, text=checklist_info, style='TLabel')
            checklist_label.grid(row=i + 1, column=0, columnspan=3, pady=5, padx=10, sticky="w")

            view_button = ttk.Button(filter_frame, text="Просмотреть",
                                     command=lambda c=checklist: self.one_checklist(c))
            view_button.grid(row=i + 1, column=3, pady=5, padx=10, sticky="w")

            delete_button = ttk.Button(filter_frame, text="Удалить",
                                       command=lambda c=checklist: self.delete_checklist(c[0]), style='Close.TButton')
            delete_button.grid(row=i + 1, column=4, pady=5, padx=10, sticky="w")

        filter_frame.bind("<Configure>", lambda e: filter_canvas.configure(scrollregion=filter_canvas.bbox("all")))

    def return_all_checklists(self):
        self.filtered_window.destroy()
        self.view_checklists()

    def one_checklist(self, checklist):

        def edit_checklist():
            checklist_id = checklist[0]

            global editing_checklist_flag
            editing_checklist_flag = 1
            global delited_checlist_id
            delited_checlist_id = checklist_id

            app.cursor.execute("SELECT * FROM checklists WHERE id=?", (checklist_id,))
            checklist_data = app.cursor.fetchone()

            app.create_checklist()

            app.name_entry.insert(0, checklist_data[1])
            app.product_entry.insert(0, checklist_data[2])
            app.version_entry.insert(0, checklist_data[3])
            app.date_entry.insert(0, checklist_data[4])

            app.cursor.execute("SELECT * FROM criteria WHERE checklist_id=?", (checklist_id,))
            criteria_data = app.cursor.fetchall()
            for i, criterion in enumerate(criteria_data):
                if i < len(app.criteria_entries):
                    criterion_frame, criterion_entry, source_entry = app.criteria_entries[i]

                    criterion_entry.set(criterion[2])
                    source_entry.set(criterion[4])
                else:
                    app.add_criterion_entry(app.create_window)
                    criterion_frame, criterion_entry, source_entry = app.criteria_entries[-1]

                    criterion_entry.set(criterion[2])
                    source_entry.set(criterion[4])

            app.cursor.execute("SELECT evaluation, comment FROM criteria WHERE checklist_id=?", (checklist_id,))
            evaluations_comments_data = app.cursor.fetchall()
            for (evaluation, comment), (evaluation_var, comment_var) in zip(evaluations_comments_data,
                                                                            app.evaluation_vars):
                evaluation_var.set(evaluation)
                comment_var.set(comment)

            app.cursor.execute("SELECT comment FROM checklists WHERE id=?", (checklist_id,))
            overall_comment_data = app.cursor.fetchone()
            if overall_comment_data:
                overall_comment_value = overall_comment_data[0]
                app.comment_text.delete(1.0, tk.END)
                app.comment_text.insert(tk.END, overall_comment_value)

        def open_create_window():
            checklist_id = checklist[0]
            app.cursor.execute("SELECT * FROM criteria WHERE checklist_id=?", (checklist_id,))
            criteria_data = app.cursor.fetchall()

            app.create_checklist()

            for i, criterion in enumerate(criteria_data):
                if i < len(app.criteria_entries):
                    criterion_frame, criterion_entry, source_entry = \
                        app.criteria_entries[i]

                    criterion_entry.set(criterion[2])
                    source_entry.set(criterion[4])
                else:
                    app.add_criterion_entry(app.create_window)
                    criterion_frame, criterion_entry, source_entry = \
                        app.criteria_entries[-1]

                    criterion_entry.set(criterion[2])
                    source_entry.set(criterion[4])

            app.name_entry.delete(0, tk.END)
            app.product_entry.delete(0, tk.END)
            app.version_entry.delete(0, tk.END)
            app.date_entry.delete(0, tk.END)

        def plot_pie_chart(yes, no, partial):

            fig = Figure(figsize=(5, 4), dpi=100)
            ax = fig.add_subplot(111)
            ax.set_title('Круговая диаграмма', fontsize=14, fontweight='bold', color='white', fontfamily='Arial')
            fig.patch.set_facecolor('#222222')
            colors = ['green', 'red', 'orange']

            if yes == 0:
                if no > 0:
                    if partial > 0:
                        data = {'Category': ['no', 'partial'], 'Values': [no, partial]}
                    else:
                        data = {'Category': ['no'], 'Values': [no]}
                else:
                    data = {'Category': ['partial'], 'Values': [partial]}
            elif no == 0:
                if partial > 0:
                    data = {'Category': ['yes', 'partial'], 'Values': [yes, partial]}
                else:
                    data = {'Category': ['yes'], 'Values': [yes]}
            elif partial == 0:
                data = {'Category': ['yes', 'no'], 'Values': [yes, no]}
            else:
                data = {'Category': ['yes', 'no', 'partial'], 'Values': [yes, no, partial]}
            df = pd.DataFrame(data)
            ax.pie(df['Values'], labels=df['Category'], autopct='%1.1f%%', startangle=140, colors=colors, shadow=True,
                   textprops={'fontsize': 14, 'fontweight': 'bold', 'color': 'white', 'fontfamily': 'Calibri'})

            canvas_3 = FigureCanvasTkAgg(fig, master=canvas_2)
            canvas_3.draw()

            canvas_3.get_tk_widget().pack()

        def filter_criteria():
            filter_text = filter_entry.get().strip().lower()
            if not filter_text == "":
                reset_button.grid(row=2, column=2, pady=10, sticky='w')

            filtered_criteria = [criterion for criterion in criteria_data if
                                 filter_text in criterion[2].lower() or
                                 (criterion[4] is not None and filter_text in criterion[4].lower()) or
                                 filter_text == criterion[3].lower()]

            criteria_tree.delete(*criteria_tree.get_children())

            for index, criterion in enumerate(filtered_criteria):
                tags = ('evenrow' if index % 2 == 0 else 'oddrow',)
                criteria_tree.insert("", "end", values=(criterion[2], criterion[3], criterion[4], criterion[5]),
                                     tags=tags)

            criteria_tree['height'] = len(filtered_criteria)

            criteria_tree.bind("<MouseWheel>", on_canvas_scroll)
            criteria_tree.bind("<Button-4>", on_canvas_scroll)
            criteria_tree.bind("<Button-5>", on_canvas_scroll)

        view_one = tk.Toplevel(self.root)
        view_one.title(f"Просмотр чек-листа: {checklist[1]}")
        view_one.geometry("1600x900")
        style = ttk.Style()
        style.theme_use('clam')
        view_one.configure(background='#222222')
        configure_style()

        one_canvas = tk.Canvas(view_one, background='#222222')
        one_canvas.pack(side="left", fill="both", expand=True)

        one_frame = ttk.Frame(one_canvas, style='TFrame')
        one_frame.pack(side="left", fill="both", expand=True)

        one_canvas.create_window((0, 0), window=one_frame, anchor="nw")

        scrollbar = ttk.Scrollbar(view_one, orient="vertical", command=one_canvas.yview)
        scrollbar.pack(side="right", fill="y")
        one_canvas.configure(yscrollcommand=scrollbar.set)

        name_label = ttk.Label(one_frame, text="Имя:", style='TLabel')
        name_label.grid(row=0, column=0, padx=10, pady=5, sticky='e')
        name_value = ttk.Label(one_frame, text=checklist[1])
        name_value.grid(row=0, column=1, padx=(0, 40), pady=5, sticky='w')

        product_label = ttk.Label(one_frame, text="Продукт:", style='TLabel')
        product_label.grid(row=1, column=0, padx=10, pady=5, sticky='e')
        product_value = ttk.Label(one_frame, text=checklist[2])
        product_value.grid(row=1, column=1, padx=(0, 40), pady=5, sticky='w')

        version_label = ttk.Label(one_frame, text="Версия продукта:", style='TLabel')
        version_label.grid(row=2, column=0, padx=10, pady=5, sticky='e')
        version_value = ttk.Label(one_frame, text=checklist[3])
        version_value.grid(row=2, column=1, padx=(0, 40), pady=5, sticky='w')

        date_label = ttk.Label(one_frame, text="Дата:", style='TLabel')
        date_label.grid(row=3, column=0, padx=10, pady=5, sticky='e')
        date_value = ttk.Label(one_frame, text=checklist[4])
        date_value.grid(row=3, column=1, padx=(0, 40), pady=5, sticky='w')

        self.cursor.execute("SELECT evaluation, COUNT(*) FROM criteria WHERE checklist_id=? GROUP BY evaluation",
                            (checklist[0],))
        evaluation_counts = self.cursor.fetchall()

        yes_count = sum(count for evaluation, count in evaluation_counts if evaluation == "Yes")
        no_count = sum(count for evaluation, count in evaluation_counts if evaluation == "No")
        partial_count = sum(count for evaluation, count in evaluation_counts if evaluation == "Partial")
        eval_count = yes_count + no_count + partial_count
        evaluation_info = (f"     Yes: {yes_count}    ({round((yes_count / eval_count) * 100, 2)}%)\n"
                           f"      No: {no_count}    ({round((no_count / eval_count) * 100, 2)}%)\n"
                           f"Partial: {partial_count}    ({round((partial_count / eval_count) * 100, 2)}%)")
        evaluation_info_label = ttk.Label(one_frame, text=evaluation_info, style='TLabel')
        evaluation_info_label.grid(row=4, column=0, columnspan=2, pady=5, padx=10, sticky="e")

        canvas_2 = tk.Canvas(one_frame, width=400, height=300, background='#222222')
        canvas_2.grid(row=4, column=2, pady=40, sticky="w")

        plot_pie_chart(yes_count, no_count, partial_count)

        self.cursor.execute("SELECT comment FROM checklists WHERE id=?", (checklist[0],))
        comment_data = self.cursor.fetchone()

        comment_value = comment_data[0] if comment_data is not None else ""
        self.comment_text_value = comment_value
        comment_label = ttk.Label(one_frame, text=f"Комментарий:\n{comment_value}", style='TLabel')
        comment_label.grid(row=5, column=0, columnspan=5, pady=5, padx=10, sticky="w")

        select_template_button = ttk.Button(one_frame, text="Выбрать в качестве шаблона", command=open_create_window,
                                            style='TButton')
        select_template_button.grid(row=0, column=2, padx=10, pady=5, sticky="w")

        close_button = ttk.Button(one_frame, text="Вернуться назад", command=lambda: view_one.destroy(),
                                  style='Close.TButton')
        close_button.grid(row=0, column=2, padx=(0, 40), pady=5, sticky='e')

        redact = ttk.Button(one_frame, text="Редактировать", style='TButton', command=edit_checklist)
        redact.grid(row=1, column=2, padx=10, pady=5, sticky="w")

        self.crit_text = tk.StringVar(value="Просмотр критериев")
        show_criteria_button = ttk.Button(one_frame, textvariable=self.crit_text,
                                          command=lambda: toggle_criteria_table(criteria_table_frame), style='TButton')
        show_criteria_button.grid(row=3, column=2, padx=10, pady=5, sticky="w")

        self.cursor.execute("SELECT * FROM criteria WHERE checklist_id=?", (checklist[0],))
        criteria_data = self.cursor.fetchall()

        criteria_table_frame = ttk.Frame(view_one, style='TFrame')

        criteria_tree = ttk.Treeview(criteria_table_frame, columns=("Criterion", "Evaluation", "Source", "Comment"),
                                     show="headings", style='Custom.Treeview')
        criteria_tree.heading("Criterion", text="Критерий")
        criteria_tree.heading("Evaluation", text="Оценка")
        criteria_tree.heading("Source", text="Источник")
        criteria_tree.heading("Comment", text="Комментарий")

        criteria_tree.tag_configure('oddrow', background='#1a1a1a')
        criteria_tree.tag_configure('evenrow', background='black')

        for index, criterion in enumerate(criteria_data):
            tags = ('evenrow' if index % 2 == 0 else 'oddrow',)
            criteria_tree.insert("", "end", values=(criterion[2], criterion[3], criterion[4], criterion[5]), tags=tags)

        self.cursor.execute("SELECT * FROM criteria WHERE checklist_id=?", (checklist[0],))
        criteria_data = self.cursor.fetchall()
        for criterion in criteria_data:
            criteria_tree.insert("", "end", values=(criterion[2], criterion[3], criterion[4], criterion[5]))

        criteria_tree.grid(row=0, column=0, columnspan=6, pady=20, padx=20, sticky='w')

        filter_text = ttk.Label(criteria_table_frame, text='Поиск критериев: ', style='TLabel')
        filter_text.grid(row=1, column=0, pady=(20, 0), padx=10, sticky='w')
        filter_entry = ttk.Entry(criteria_table_frame, style='TEntry', width=35)
        filter_entry.grid(row=2, column=0, columnspan=2, pady=10, padx=10, sticky='w')
        filter_button = ttk.Button(criteria_table_frame, text="Искать", command=filter_criteria, style='TButton')
        filter_button.grid(row=2, column=1, pady=10, padx=10, sticky='w')

        def reset_view():
            filter_entry.delete(0, tk.END)
            filter_criteria()
            reset_button.grid_remove()

        reset_button = ttk.Button(criteria_table_frame, text="Сбросить", command=reset_view, style='Close.TButton')

        def toggle_criteria_table(frame):
            if frame.winfo_ismapped():
                frame.pack_forget()
                self.crit_text.set("Просмотр критериев")
            else:
                self.crit_text.set("Скрыть критерии")
                criteria_tree.configure(height=len(criteria_data))
                frame.pack(padx=10, pady=10)

        def update_row_colors():
            for i, item in enumerate(criteria_tree.get_children()):
                criteria_tree.item(item, tags=('evenrow' if i % 2 == 0 else 'oddrow',))

        def on_canvas_scroll(event):
            update_row_colors()

        criteria_tree.bind("<MouseWheel>", on_canvas_scroll)
        criteria_tree.bind("<Button-4>", on_canvas_scroll)
        criteria_tree.bind("<Button-5>", on_canvas_scroll)

    def on_mousewheel(self, event):
        if event.num == 4 or event.delta == 120 or event.delta > 0:
            direction = 1
        elif event.num == 5 or event.delta == -120 or event.delta < 0:
            direction = -1
        else:
            direction = 0

        if event.widget.winfo_class() == "Canvas" or event.widget.winfo_class() == "Entry" or event.widget.winfo_class() == "Listbox":
            event.widget.yview_scroll(-1 * direction, "units")
        elif event.widget.winfo_class() == "Toplevel":
            for child in event.widget.winfo_children():
                if child.winfo_class() == "Canvas" or child.winfo_class() == "Entry" or child.winfo_class() == "Listbox":
                    child.yview_scroll(-1 * direction, "units")
                    break

if __name__ == "__main__":
    root = tk.Tk()
    app = UsabilityAuditApp(root)
    root.mainloop()
