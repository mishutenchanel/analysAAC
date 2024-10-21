import matplotlib
import time

matplotlib.use('TkAgg')
import networkx as nx
from sympy import Matrix, linsolve, symbols, zeros
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog, messagebox, Button, Label


class bufer():
    def __init__(self, x):
        self.size = 10
        self.inn = -1
        self.out = -1
        self.value = 0
        self.count_in = 0
        self.count_out = 0
        self.index = x

    def setsize(self, x):
        self.size = x


class uzel():
    def __init__(self, x):
        self.out = []
        self.inn = []
        self.index = x
        self.structure = []
        self.state = 0

    def setout(self, x, y):
        self.out.append([x, y])

    def setinn(self, x, y):
        self.inn.append([x, y])


class system(uzel, bufer):
    def __init__(self, x, y, z):
        self.p_count = x
        self.buf_count = y
        self.b = []
        self.p = []
        self.G = nx.DiGraph()
        self.file = z
        self.state = zeros(1, x + y)

    def create(self):  # создание буферов и компонентов
        for i in range(self.buf_count):
            self.b.append(bufer(i))
        for i in range(self.p_count):
            self.p.append(uzel(i))

    def create_p(self):  # считывание диаграммы переходов для каждого компонента
        with open(self.file, 'r', encoding='utf-8') as file:
            current_list = []
            i = 0
            lines = file.readlines()
            for line in lines[len(self.b) + 2:]:
                line = line.strip()
                if line == "end":
                    if current_list:
                        self.p[i].structure.append(current_list)
                    current_list = []
                    i += 1
                else:
                    current_list.append(line)

    def countinout(self, x):  # подсчет, сколько блоков данных записывается и считывается из буфера х за рабочий цикл
        left_count = 0
        right_count = 0
        for i in range(len(self.p)):
            for j in self.p[i].structure[0][self.p[i].structure[0].index("*") + 1::]:
                left, right = j.split("->")
                left1, left2 = left.split(" ")
                for z in left2.split(","):
                    z = z.replace("b", "")
                    if str(x) == z:
                        left_count += 1

                for z in right.split(","):
                    z = z.replace("b", "")
                    if str(x) == z:
                        right_count += 1
        return [left_count, right_count]

    def createline(self, From, To, buf):  # создание дуг между компонентами и заполнение данных
        count_from = self.countinout(buf)[1]
        count_to = self.countinout(buf)[0]
        self.p[From].setout(To, count_from)
        self.p[To].setinn(From, count_to)
        self.b[buf].inn = From
        self.b[buf].out = To
        self.b[buf].count_in = count_from
        self.b[buf].count_out = count_to

    def cycles(self):  # расчет всех простых циклов
        graph = []
        for i in range(len(self.b)):
            graph.append((self.b[i].inn, self.b[i].out))
        self.G.add_edges_from(graph)

        return list(nx.simple_cycles(self.G))

    def static_analysis(self):  # статический анализ схемы
        cycle = self.cycles()
        m = zeros(len(self.b), len(self.b))  # создание матрицы
        v = zeros(1, len(self.b))
        for i in range(len(cycle)):  # проверка условия для каждого цикла
            cr = 1
            cl = 1
            for j in range(len(cycle[i])):
                for z in range(len(self.b)):
                    if (self.b[z].inn == cycle[i][j]) and (self.b[z].out == cycle[i][(j + 1) % (len(cycle[i]))]):
                        line = z
                        break
                cr = self.b[line].count_in * cr
                cl = self.b[line].count_out * cl
            if (cr != cl):
                return False
        for i in range(len(self.b)):  # составление и решение уравнений для вектора разметки
            m[i, self.b[i].inn] = self.b[i].count_in
            m[i, self.b[i].out] = -self.b[i].count_out
        solution = linsolve((m, v))
        solution = list(solution)[0][:len(self.p):]
        tau = symbols('tau')
        solution_parametric = [expr.subs(symbols('tau0'), tau) for expr in solution]
        for i in range(100):
            tau_value = i + 1
            q = 0
            solution_with_tau = [expr.subs(tau, tau_value) for expr in solution_parametric]
            for j in range(len(solution_with_tau)):
                if solution_with_tau[j] == int(solution_with_tau[j]):
                    q += 1
            if q == len(solution_with_tau):
                return solution_with_tau
        return False

    def showgraph(self):  # графический вывод графа
        pos = nx.planar_layout(self.G)
        plt.figure()
        labels = {i: f'P{i}' for i in self.G.nodes()}
        nx.draw(self.G, pos, labels=labels, with_labels=True, node_size=700, node_color='lightblue', font_size=10,
                font_color='black',
                edge_color='gray')

        def calculate_edge_label_pos(start, end, frac=0.1):
            x = start[0] + (end[0] - start[0]) * frac
            y = start[1] + (end[1] - start[1]) * frac
            return x, y

        for (u, v) in self.G.edges():
            x_start, y_start = pos[u]
            x_end, y_end = pos[v]
            for i in range(len(self.b)):
                if self.b[i].inn == u and self.b[i].out == v:
                    q = i
            label = self.b[q].count_in
            label2 = self.b[q].count_out
            label3 = self.b[q].value
            label4 = self.p[u].state

            label_start_x, label_start_y = calculate_edge_label_pos((x_start, y_start), (x_end, y_end), frac=0.1)

            label_end_x, label_end_y = calculate_edge_label_pos((x_end, y_end), (x_start, y_start), frac=0.1)

            plt.text(label_start_x, label_start_y, f'{label}', horizontalalignment='right', verticalalignment='center',
                     bbox=dict(facecolor='white', alpha=0.6))

            plt.text(label_end_x, label_end_y, f'{label2}', horizontalalignment='left', verticalalignment='center',
                     bbox=dict(facecolor='white', alpha=0.6))

            plt.text(label_end_x / 2 + label_start_x / 2, label_end_y / 2 + label_start_y / 2 + 0.05, f'{label3}',
                     horizontalalignment='left', verticalalignment='center',
                     bbox=dict(alpha=0.6, color='lightgreen', joinstyle='round'))

            plt.text(x_start, y_start + 0.07, f'{label4}',
                     horizontalalignment='left', verticalalignment='center',
                     bbox=dict(alpha=0.6, color='lightgreen', joinstyle='round'))

            plt.text(label_end_x / 2 + label_start_x / 2 - 0.05, label_end_y / 2 + label_start_y / 2, f"buf{q}",
                     bbox=dict(facecolor='red', edgecolor='black', boxstyle='round,pad=0.3'))

        plt.show()

    def step(self, p):  # переход компонента в новое состояние
        s = p.state
        l_ok = False
        r_ok = False
        start_cycle = p.structure[0].index("*")
        x = p.structure[0][:p.structure[0].index("*"):]
        x.extend(p.structure[0][p.structure[0].index("*") + 1::])
        len_cycle = len(p.structure[0][p.structure[0].index("*") + 1::])
        left1, right = x[s].split("->")
        left2, left = left1.split(" ")
        if left == "_":
            l_ok = True
        else:
            for i in left.split(","):
                i = i.replace("b", "")
                if self.b[int(i)].value <= 0:
                    return False
            l_ok = True

        if right == "_":
            r_ok = True
        else:
            for i in right.split(","):
                i = i.replace("b", "")
                if self.b[int(i)].value >= self.b[int(i)].size:
                    r_ok = False
                    return False
            r_ok = True
        if r_ok == True and l_ok == True:
            if s >= start_cycle:
                p.state = start_cycle + (s - start_cycle + 1) % len_cycle
            else:
                p.state += 1
            if left != "_":
                for i in left.split(","):
                    i = i.replace("b", "")
                    self.b[int(i)].value = self.b[int(i)].value - 1
            if right != "_":
                for i in right.split(","):
                    i = i.replace("b", "")
                    self.b[int(i)].value = self.b[int(i)].value + 1
            return True
        return False


def load_file():  # загрузка файла
    file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if file_path:
        file_entry.delete(0, tk.END)
        file_entry.insert(0, file_path)


def start_system():  # запуск программы
    start_time = time.time()
    p_count = 0
    b_count = 0
    file_path = file_entry.get()
    realizebybufer = False
    # проверка вводимых данных
    if not file_path:
        messagebox.showerror("Ошибка", "Загрузите текстовый файл")
        return False
    buffer_size = buffer_size_entry.get()
    system_step = system_step_entry.get()
    try:
        buffer_size = int(buffer_size)
        system_step = int(system_step)
    except:
        end_time=time.time()
        print("time", end_time - start_time)
        messagebox.showerror("Ошибка", "Введите целые числовые значение для размера буфера и шага")
        return False
    if buffer_size <= 0:
        messagebox.showerror("Ошибка", "У буферов должен быть размер")
        return False
    if system_step < 0:
        messagebox.showerror("Ошибка", "Введите неотрицательное значение шага")
        return False
    lines = []
    dinamic = True
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                if "components:" in line:
                    break
                else:
                    if "lines:" not in line:
                        x, y, z = line.split(" ")
                        b_count += 1
                        if int(x) > p_count or int(y) > p_count:
                            p_count = max(int(x), int(y))
                        lines.append([int(x), int(y), int(z)])
        one = system(p_count + 1, b_count, file_path)
        one.create()
        one.create_p()
    except:
        messagebox.showerror("Ошибка", "Неправильная структура файла")
        return False
    state = one.state[:]
    q = 0
    q2 = []
    need_to_up = True
    need_to_show = True
    for i in range(b_count):
        one.createline(lines[i][0], lines[i][1], lines[i][2])
        one.b[i].setsize(buffer_size)

    static = one.static_analysis()
    if not static:
        messagebox.showerror("Результат", "Схема несбалансированная")
        one.showgraph()
        return False
    for i in range(102 + system_step):  # моделирование работы схемы
        if i == system_step and dinamic and need_to_show:
            one.showgraph()
        for j in range(one.p_count):
            one.step(one.p[j])
            one.state[j] = one.p[j].state
        for j in range(one.buf_count):
            one.state[j + one.p_count] = one.b[j].value
        if list(one.state) == state:  # в случае если схема нереализуема пытаемся найти оптимальные размеры буферов
            if need_to_show:
                one.showgraph()
            need_to_show = False
            dinamic = False
            realizebybufer = False
            if q == 2:
                if (i - 1) % b_count not in q2:
                    one.b[(i - 1) % b_count].size += 1
                    q2.append((i - 1) % b_count)
            if q == 1:
                need_to_up = True
            if need_to_up:
                for j in range(b_count):
                    if j not in q2:
                        one.b[j].size += 1
            q = 1
        else:
            if q != 0 and (i % b_count) not in q2 and one.b[i % b_count].size != 1:
                one.b[i % b_count].size -= 1
                q = 2
            if q != 0:
                need_to_up = False
                q = 0
            state = one.state[:]
            realizebybufer = True
    end_time = time.time()
    print("время выполнения: ", end_time - start_time)
    if realizebybufer and not dinamic:  # вывод результатов
        x = []
        for i in range(one.buf_count):
            x.append(one.b[i].size)
        messagebox.showerror("Результат",
                             f"Схема условно нереализуемая, рекомендуемые размеры буферов: {x}")
    if static and dinamic:
        messagebox.showinfo("Результат", f"ААС реализуема, вектор разметки:{static}")

    if not dinamic and not realizebybufer:
        messagebox.showerror("Результат", "Схема нереализуема, так как имеет тупиковое состояние ")


root = tk.Tk()
root.title("Анализ ААС")  # создание начального окна

frame = tk.Frame(root)
frame.pack(padx=10, pady=10)

Label(frame, text="Выберите файл:").grid(row=0, column=0, padx=5, pady=5)
file_entry = tk.Entry(frame, width=50)
file_entry.grid(row=0, column=1, padx=5, pady=5)
Button(frame, text="Обзор", command=load_file).grid(row=0, column=2, padx=5, pady=5)

Label(frame, text="Размер буферов:").grid(row=1, column=0, padx=5, pady=5)
buffer_size_entry = tk.Entry(frame, width=20)
buffer_size_entry.grid(row=1, column=1, padx=5, pady=5)

Label(frame, text="На каком шаге вывести схему:").grid(row=2, column=0, padx=5, pady=5)
system_step_entry = tk.Entry(frame, width=20)
system_step_entry.grid(row=2, column=1, padx=5, pady=5)

Button(frame, text="Запустить", command=start_system).grid(row=3, columnspan=3, pady=10)

root.mainloop()
