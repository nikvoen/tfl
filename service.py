import requests


print("Establishing a connection...")
session = requests.Session()


def export_to_json(table):
    main_prefixes = ["e"] + table.S[1:table.extended_table].tolist()
    non_main_prefixes = table.S[table.extended_table:].tolist()
    suffixes = ["e"] + table.E[1:].tolist()

    table_values = [str(value) for row in table._T.values() for value in row]
    table_str = "".join(table_values)

    data = {
        "main_prefixes": " ".join(main_prefixes),
        "complementary_prefixes": " ".join(non_main_prefixes),
        "suffixes": " ".join(suffixes),
        "table": table_str
    }

    return data


def create_maze(width, height, walls, exits):
    url = "http://localhost:8080/generate_graph"
    data = {
        "width": width,
        "height": height,
        "pr_of_break_wall": walls,
        "num_of_finish_edge": exits
    }

    try:
        response = session.post(url, json=data)
        if response.status_code == 200:
            return True
        else:
            print("Error sending maze data:", response.status_code)
            return False
    except requests.RequestException as e:
        print("Request failed:", e)
        return False


# Отправка всей таблицы
def check_equivalence(table):
    url = "http://localhost:8080/check_table"
    table_json = export_to_json(table)

    try:
        response = session.post(url, json=table_json)

        if response.status_code == 200:
            answer = response.text

            if answer != "true":
                print(f'Counterexample: {answer}')
                return answer
            else:
                print(table)
                print('Win')
                return answer
        else:
            print("Error sending table:", response.status_code)
            print(table_json)
            return None
    except requests.RequestException as e:
        print("Request failed:", e)
        return None


# Отправка слова
def check_membership(string):
    url = "http://localhost:8080/check_membership"
    headers = {"Content-Type": "application/json"}

    try:
        response = session.post(url, data=string, headers=headers)
        if response.status_code == 200:
            result = response.content
            return int(result)
        else:
            print("Error sending word:", response.status_code)
            return ""
    except requests.RequestException as e:
        print("Request failed:", e)
        return ""
