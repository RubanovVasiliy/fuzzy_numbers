import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# Функция для построения графика
def plot_membership_function(alpha_levels, left, right, title, ax):
    y_asse = alpha_levels + list(reversed(alpha_levels))
    x_asse = left + list(reversed(right))
    ax.plot(x_asse, y_asse, label=f'{title}')
    ax.fill_betweenx(alpha_levels, left, right, alpha=0.2)
    ax.set_xlabel('x')
    ax.set_ylabel('μ(x)')
    ax.set_title(title)
    ax.legend()
    ax.grid(True)


def sort_by_column(tree, col, reverse):
    values = [(tree.set(k, col), k) for k in tree.get_children('')]
    values.sort(reverse=reverse)
    for index, (val, k) in enumerate(values):
        tree.move(k, '', index)
    tree.heading(col, command=lambda: sort_by_column(tree, col, not reverse))


def is_sorted_list(lst, reverse=False):
    return all(lst[i] <= lst[i + 1] for i in range(len(lst) - 1)) if not reverse else all(
        lst[i] >= lst[i + 1] for i in range(len(lst) - 1))


# Приведение к одинаковому количеству α-срезов
def interpolate_intervals(alpha_levels, intervals, common_alpha_levels):
    def interpolate(alpha1, alpha2, val1, val2, alpha):
        return val1 + (val2 - val1) * ((alpha - alpha1) / (alpha2 - alpha1))

    interpolated_intervals = []

    for alpha in common_alpha_levels:
        if alpha in alpha_levels:
            # If alpha is already in alpha_levels, no need to interpolate
            idx = alpha_levels.index(alpha)
            interpolated_intervals.append(intervals[idx])
        else:
            # Find the two alpha levels between which we need to interpolate
            for i in range(len(alpha_levels) - 1):
                if alpha_levels[i] < alpha < alpha_levels[i + 1]:
                    lower_alpha = alpha_levels[i]
                    upper_alpha = alpha_levels[i + 1]
                    lower_interval = intervals[i]
                    upper_interval = intervals[i + 1]

                    lower_bound = interpolate(lower_alpha, upper_alpha, lower_interval[0], upper_interval[0], alpha)
                    upper_bound = interpolate(lower_alpha, upper_alpha, lower_interval[1], upper_interval[1], alpha)

                    interpolated_intervals.append([lower_bound, upper_bound])
                    break

    return interpolated_intervals



def compare_fuzzy_numbers(intervals, operator):
    if operator == '>':
        return all(left_a < left_b and right_a > right_b for (alpha, left_a, right_a), (_, left_b, right_b) in intervals)
    elif operator == '>=':
        return all(left_a <= left_b and right_a >= right_b for (alpha, left_a, right_a), (_, left_b, right_b) in intervals)
    elif operator == '<':
        return all(left_a > left_b and right_a < right_b for (alpha, left_a, right_a), (_, left_b, right_b) in intervals)
    elif operator == '<=':
        return all(left_a >= left_b and right_a <= right_b for (alpha, left_a, right_a), (_, left_b, right_b) in intervals)
    elif operator == '==':
        return all(left_a == left_b and right_a == right_b for (alpha, left_a, right_a), (_, left_b, right_b) in intervals)
    elif operator == '!=':
        return any(left_a != left_b or right_a != right_b for (alpha, left_a, right_a), (_, left_b, right_b) in intervals)
    else:
        return False


class FuzzyNumberApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Калькулятор нечетких множеств")
        self.geometry("875x530")
        self.resizable(width=False, height=False)

        self.create_widgets()
        self.create_table_bindings()
        self.create_plot_area()

    def create_widgets(self):
        self.frames = {
            'A': ttk.LabelFrame(self, text="Множество A"),
            'B': ttk.LabelFrame(self, text="Множество B"),
            'Operations': ttk.LabelFrame(self, text="Операции"),
            'C': ttk.LabelFrame(self, text="Множество C"),

            'Compare': ttk.LabelFrame(self, text="Сравнение"),
            'Swap': ttk.LabelFrame(self, text="A и B"),
            'Actions': ttk.LabelFrame(self, text="Действия"),
            'Plot': ttk.LabelFrame(self, text="График")
        }

        self.frames['A'].grid(row=0, column=0, padx=10, pady=5)
        self.frames['B'].grid(row=1, column=0, padx=10, pady=5)
        self.frames['Operations'].grid(row=2, column=0, padx=10, pady=5)
        self.frames['C'].grid(row=3, column=0, padx=10, pady=5)
        self.frames['Compare'].grid(row=0, column=1, padx=10, pady=5)
        self.frames['Swap'].grid(row=1, column=1, padx=10, pady=5)
        self.frames['Actions'].grid(row=3, column=1, padx=10, pady=5)
        self.frames['Plot'].grid(row=0, column=2, rowspan=4, padx=10, pady=10)

        self.table_a = self.create_table(self.frames['A'], ["α lvl", "нижняя", "верхняя"])
        self.table_b = self.create_table(self.frames['B'], ["α lvl", "нижняя", "верхняя"])
        self.table_c = self.create_table(self.frames['C'], ["α lvl", "нижняя", "верхняя"])

        self.table_a.grid(row=0, column=0, padx=5, pady=5)
        self.table_b.grid(row=0, column=0, padx=5, pady=5)
        self.table_c.grid(row=0, column=0, padx=5, pady=5)

        self.add_table_entries(self.table_a, [(0, 1, 9), (0.5, 2, 8), (1, 3, 4)])
        self.add_table_entries(self.table_b, [(0, 1, 9), (0.2, 2, 7), (0.5, 3, 6), (1, 4, 5)])
        self.add_table_entries(self.table_c, [])

        self.create_buttons()

    def create_buttons(self):
        self.buttons = {
            'PlotA': ttk.Button(self.frames['Actions'], text="Построить A", command=self.plot_a),
            'PlotB': ttk.Button(self.frames['Actions'], text="Построить B", command=self.plot_b),
            'PlotC': ttk.Button(self.frames['Actions'], text="Построить C", command=self.plot_c),
            'Clear': ttk.Button(self.frames['Plot'], text="Очистить график", command=self.clear_plot),

            'Add': ttk.Button(self.frames['Operations'], text="+", command=lambda: self.calculate(self.add), width=5),
            'Sub': ttk.Button(self.frames['Operations'], text="-", command=lambda: self.calculate(self.sub), width=5),
            'Mult': ttk.Button(self.frames['Operations'], text="*", command=lambda: self.calculate(self.mult), width=5),
            'Div': ttk.Button(self.frames['Operations'], text="/", command=lambda: self.calculate(self.div), width=5),

            'Compare': ttk.Button(self.frames['Compare'], text="Сравнить", command=self.compare, width=15),
            'Great': ttk.Button(self.frames['Compare'], text=">", command=self.dummy_compare, width=5),
            'GreatEq': ttk.Button(self.frames['Compare'], text=">=", command=self.dummy_compare, width=5),
            'Less': ttk.Button(self.frames['Compare'], text="<", command=self.dummy_compare, width=5),
            'LessEq': ttk.Button(self.frames['Compare'], text="<=", command=self.dummy_compare, width=5),
            'Eq': ttk.Button(self.frames['Compare'], text="=", command=self.dummy_compare, width=5),
            'NotEq': ttk.Button(self.frames['Compare'], text="!=", command=self.dummy_compare, width=5),
            'Swap': ttk.Button(self.frames['Swap'], text="Поменять", command=self.switch_tables_values),
        }

        self.buttons['PlotA'].grid(row=0, column=0, pady=5)
        self.buttons['PlotB'].grid(row=1, column=0, pady=5)
        self.buttons['PlotC'].grid(row=2, column=0, pady=5)
        self.buttons['Clear'].grid(row=1, column=0, pady=5)

        self.buttons['Add'].grid(row=0, column=0, pady=5, padx=4)
        self.buttons['Sub'].grid(row=0, column=1, pady=5, padx=5)
        self.buttons['Mult'].grid(row=0, column=2, pady=5, padx=5)
        self.buttons['Div'].grid(row=0, column=3, pady=5, padx=4)

        self.buttons['Compare'].grid(row=0, column=0, pady=5, padx=4, columnspan=2, sticky='ew')
        self.buttons['Great'].grid(row=1, column=0, pady=5, padx=4)
        self.buttons['GreatEq'].grid(row=1, column=1, pady=5, padx=4)
        self.buttons['Less'].grid(row=2, column=0, pady=5, padx=4)
        self.buttons['LessEq'].grid(row=2, column=1, pady=5, padx=4)
        self.buttons['Eq'].grid(row=3, column=0, pady=5, padx=4)
        self.buttons['NotEq'].grid(row=3, column=1, pady=5, padx=4)
        self.buttons['Swap'].grid(row=0, column=0, pady=5, padx=4)


    # Ограничение на постройку графика
        self.plot_name_list = []
        self.table_c_name='C'
        self.table_a_name = 'Нечеткое число A'
        self.table_b_name = 'Нечеткое число B'
        self.table_c_name_add = '(+)Нечеткое число C'
        self.table_c_name_sub = '(-) Нечеткое число C'
        self.table_c_name_mult = '(*) Нечеткое число C'
        self.table_c_name_div = '(/) Нечеткое число C'

        self.add = '+'
        self.sub = '-'
        self.mult = '*'
        self.div = '/'

    def create_table_bindings(self):
        self.table_a.bind("<Double-1>", lambda event, table=self.table_a: self.edit_cell(event, table))
        self.table_b.bind("<Double-1>", lambda event, table=self.table_b: self.edit_cell(event, table))
        self.table_c.bind("<Double-1>", lambda event, table=self.table_c: self.edit_cell(event, table))

    def create_plot_area(self):
        self.figure, self.ax = plt.subplots(figsize=(5, 4))
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.frames['Plot'])
        self.canvas.get_tk_widget().grid(row=0, column=0)

    def align_alpha_levels(self, data_a, data_b):
        def get_alpha_levels_intervals(data):
            a_levels = []
            int = []
            for (a, l, r) in data:
                a_levels.append(a)
                int.append([l, r])
            return a_levels, int

        common_alpha_levels = sorted(list(set([row[0] for row in data_a] + [row[0] for row in data_b])))

        if len(data_a) < len(data_b):
            alpha_levels, intervals = get_alpha_levels_intervals(data_a)
        else:
            alpha_levels, intervals = get_alpha_levels_intervals(data_b)

        interpolated_intervals = interpolate_intervals(alpha_levels, intervals, common_alpha_levels)
        for (alpha, interval) in zip(common_alpha_levels, interpolated_intervals):
            interval.insert(0, alpha)

        if len(data_a) < len(data_b):
            for row in self.table_a.get_children():
                self.table_a.delete(row)
            for entry in interpolated_intervals:
                self.table_a.insert('', 'end', values=entry)
            return interpolated_intervals, data_b
        else:
            for row in self.table_b.get_children():
                self.table_b.delete(row)
            for entry in interpolated_intervals:
                self.table_b.insert('', 'end', values=entry)
            return data_a, interpolated_intervals

    def create_table(self, parent, columns):
        tree = ttk.Treeview(parent, columns=columns, show='headings', height=4)
        for col in columns:
            tree.heading(col, text=col, command=lambda _col=col: sort_by_column(tree, _col, False))
            tree.column(col, width=60)
        return tree

    def add_table_entries(self, table, entries):
        for entry in entries:
            table.insert('', 'end', values=entry)

    def get_table_data(self, table):
        data = []
        for child in table.get_children():
            row = table.item(child)['values']
            try:
                row = [float(row[0]), float(row[1]), float(row[2])]
            except ValueError:
                continue
            data.append(row)
        return data

    def plot_a(self):
        if self.table_a_name in self.plot_name_list:
            return
        self.plot_set(self.table_a, self.table_a_name)
        self.plot_name_list.append(self.table_a_name)

    def plot_b(self):
        if self.table_b_name in self.plot_name_list:
            return
        self.plot_set(self.table_b, self.table_b_name)
        self.plot_name_list.append(self.table_b_name)

    def plot_c(self):
        if self.table_c_name in self.plot_name_list:
            return
        self.plot_set(self.table_c, self.table_c_name)
        self.plot_name_list.append(self.table_c_name)

    def plot_set(self, table, title):
        data = self.get_table_data(table)
        if not data:
            messagebox.showerror("Ошибка", f"Некорректные данные в таблице {title[-1]}")
            return
        data.sort()
        alpha_levels = [row[0] for row in data]
        left = [row[1] for row in data]
        right = [row[2] for row in data]
        if not is_sorted_list(left):
            messagebox.showerror("Ошибка", "Не является выпуклой функцией")
            return
        if not is_sorted_list(right, True):
            messagebox.showerror("Ошибка", "Не является выпуклой функцией")
            return
        plot_membership_function(alpha_levels, left, right, title, self.ax)
        self.canvas.draw()

    def clear_plot(self):
        self.ax.clear()
        self.canvas.draw()
        self.plot_name_list.clear()

    def edit_cell(self, event, table):
        row_id = table.identify_row(event.y)
        column = table.identify_column(event.x)
        if row_id and column:
            cell_value = table.set(row_id, column)
            column_index = int(column[1:]) - 1

            def on_save():
                new_value = entry.get()
                if column_index == 0:
                    try:
                        new_value = float(new_value)
                        if new_value > 1 or new_value < 0:
                            tk.messagebox.showerror("Ошибка", "Значения должны быть в диапазоне от 0 до 1")
                            top.destroy()
                            return
                    except ValueError:
                        tk.messagebox.showerror("Ошибка", "Значение α должно быть числом")
                        top.destroy()
                        return
                else:
                    try:
                        new_value = float(new_value)
                        if new_value > 100 or new_value < -100 or new_value == 0:
                            tk.messagebox.showerror("Ошибка","Значения должны быть в диапазоне от 0 до 100, не включая 0")
                            top.destroy()
                            return
                    except ValueError:
                        tk.messagebox.showerror("Ошибка", "Значения нижней и верхней границ должны быть целыми числами")
                        top.destroy()
                        return

                table.set(row_id, column, new_value)
                top.destroy()

            top = tk.Toplevel(self)
            top.title("Редактирование ячейки")
            tk.Label(top, text="Новое значение:").pack(padx=10, pady=10)
            entry = tk.Entry(top)
            entry.pack(padx=10, pady=10)
            entry.insert(0, cell_value)
            tk.Button(top, text="Сохранить", command=on_save).pack(padx=10, pady=10)
            entry.focus_set()

    # Функции арифметических операций

    def calculate(self, operation):
        data_a = self.get_table_data(self.table_a)
        data_b = self.get_table_data(self.table_b)
        aligned_a, aligned_b = self.align_alpha_levels(data_a, data_b)

        result = []
        if operation == self.add:
            result = [[alpha, left_a + left_b, right_a + right_b] for (alpha, left_a, right_a), (_, left_b, right_b) in zip(aligned_a, aligned_b)]
            self.table_c_name = self.table_c_name_add

        elif operation == self.sub:
            result = [[alpha, left_a - left_b, right_a - right_b] for (alpha, left_a, right_a), (_, left_b, right_b) in zip(aligned_a, aligned_b)]
            for (_, left_a, right_a) in result:
                if left_a < 0 or right_a < 0:
                    messagebox.showerror("Ошибка", "Значения длжны быть больше нуля")
                    return

            self.table_c_name = self.table_c_name_sub

        elif operation == self.mult:
            result = [[alpha, left_a * left_b, right_a * right_b] for (alpha, left_a, right_a), (_, left_b, right_b) in zip(aligned_a, aligned_b)]
            self.table_c_name = self.table_c_name_mult

        elif operation == self.div:
            try:
                result = [[alpha, left_a / right_b, right_a / left_b] for (alpha, left_a, right_a), (_, left_b, right_b) in zip(aligned_a, aligned_b)]
            except ZeroDivisionError:
                messagebox.showerror("Ошибка", "Деление на ноль")
                return
            self.table_c_name = self.table_c_name_div
        self.display_result(result)

    def display_result(self, result):
        for row in self.table_c.get_children():
            self.table_c.delete(row)
        for entry in result:
            self.table_c.insert('', 'end', values=entry)

    def switch_tables_values(self):
        data_a = self.get_table_data(self.table_a)
        data_b = self.get_table_data(self.table_b)

        for row in self.table_a.get_children():
            self.table_a.delete(row)

        for row in self.table_b.get_children():
            self.table_b.delete(row)

        for entry in data_a:
            self.table_b.insert('', 'end', values=entry)

        for entry in data_b:
            self.table_a.insert('', 'end', values=entry)

    def dummy_compare(self):
        pass

    def compare(self):
        data_a = self.get_table_data(self.table_a)
        data_b = self.get_table_data(self.table_b)

        aligned_a, aligned_b = self.align_alpha_levels(data_a, data_b)
        intervals = list(zip(aligned_a, aligned_b))

        comparison_results = {
            '>': all(left_a < left_b and right_a > right_b for (_, left_a, right_a), (_, left_b, right_b) in intervals),
            '>=': all(left_a <= left_b and right_a >= right_b for (_, left_a, right_a), (_, left_b, right_b) in intervals),
            '<': all(left_a > left_b and right_a < right_b for (_, left_a, right_a), (_, left_b, right_b) in intervals),
            '<=': all(left_a >= left_b and right_a <= right_b for (_, left_a, right_a), (_, left_b, right_b) in intervals),
            '==': all(left_a == left_b and right_a == right_b for (_, left_a, right_a), (_, left_b, right_b) in intervals),
            '!=': any(left_a != left_b or right_a != right_b for (_, left_a, right_a), (_, left_b, right_b) in intervals),
        }
        for op, button in [('>', 'Great'), ('>=', 'GreatEq'), ('<', 'Less'), ('<=', 'LessEq'), ('==', 'Eq'), ('!=', 'NotEq')]:
            if comparison_results[op]:
                self.buttons[button].config(style='Success.TButton')
            else:
                self.buttons[button].config(style='Danger.TButton')


# Запуск приложения
if __name__ == "__main__":
    app = FuzzyNumberApp()
    style = ttk.Style()
    style.configure('Success.TButton', background='green')
    style.map('Success.TButton', background=[('active', 'green')])
    style.configure('Danger.TButton', background='red')
    style.map('Danger.TButton', background=[('active', 'red')])
    app.mainloop()
