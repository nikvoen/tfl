from tabulate import tabulate
import numpy as np
from service import check_membership, check_equivalence


class ObservationTable:
    def __init__(self, letters):
        self.A = letters
        self.S = np.array(["", "L", "R"])
        self.E = np.array([""])
        self._T = {0: np.array([0]), 1: np.array([0]), 2: np.array([0])}
        self.pointer = 1
        self.extended_table = 2

    def add_prefix(self, new_prefix):
        self.S = np.append(self.S, new_prefix)
        new_row = np.zeros(len(self.E), dtype=int)

        for i in range(len(self.E)):
            new_row[i] = check_membership(new_prefix + self.E[i])

        self._T[len(self.S) - 1] = new_row.copy()

    def extend_table(self):
        while self.pointer < self.extended_table:
            for letter in self.A:
                self.add_prefix(self.S[self.pointer] + letter)
                self.compare()
            self.pointer += 1

    def extend_suffixes(self, string):
        for i in range(len(string) - 1, -1, -1):
            suffix = string[i:]
            if suffix not in self.E:
                self.E = np.append(self.E, suffix)

                for key in self._T:
                    value = check_membership(self.S[key] + suffix)
                    self._T[key] = np.append(self._T[key], value)

    # Проверка совпадения строки из расширенной части с основной частью таблицы
    def is_row_unique(self, index):
        for j in range(0, self.extended_table):
            if np.array_equal(self._T[index], self._T[j]):
                return False
        return True

    # Перенос строки из расширенной в основную часть таблицы
    def move_row_to_main(self, index):
        row = self._T[index].copy()
        prefix = self.S[index]

        if index > self.extended_table:
            for i in range(index, self.extended_table, -1):
                self._T[i] = self._T[i - 1].copy()
                self.S[i] = self.S[i - 1]

        self._T[self.extended_table] = row.copy()
        self.S[self.extended_table] = prefix
        self.extended_table += 1

    # Проверка на полноту
    def compare(self):
        i = self.extended_table
        while self.extended_table < len(self.S):
            if self.is_row_unique(i):
                self.move_row_to_main(i)
            i += 1

    def __str__(self):
        output_table = [[""] + ["ε"] + list(self.E)[1:]]
        for i, s in enumerate(self.S):
            row = [s] + list(self._T[i])
            output_table.append(row)
        output_table[1][0] = "ε"
        output_table.insert(self.extended_table + 1, ["+"])

        return tabulate(output_table, headers="firstrow", tablefmt="github")


alphabet = list("EWNS")
table = ObservationTable(alphabet)
table.compare()

# Отправляем таблицу в МАТ
response = check_equivalence(table)

while response != "null":
    # Добавить контпример в таблицу
    table.extend_suffixes(response)

    # Проверка на полноту
    table.compare()

    # Расширение таблицы
    table.extend_table()

    # Отправляем таблицу в МАТ
    response = check_equivalence(table)
