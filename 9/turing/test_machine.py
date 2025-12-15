from loader import load_transitions
from machine import TuringMachine


def test_inverter():
    # Создаем простую машину-инвертор
    transitions = {
        ('q0', '0'): ('1', 'R', 'q0'),
        ('q0', '1'): ('0', 'R', 'q0'),
        ('q0', '_'): ('_', 'S', 'halt'),
    }

    # Преобразуем в нужный формат
    from machine import Transition
    formatted_transitions = {}
    for (state, read), (write, move, next_state) in transitions.items():
        formatted_transitions[(state, read)] = Transition(write, move, next_state)

    # Тестируем
    tm = TuringMachine(formatted_transitions, "1010")
    result = tm.run()

    print(f"Вход: 1010")
    print(f"Ожидаемый результат: 0101")
    print(f"Фактический результат: {result}")
    print(f"Совпадает: {result == '0101'}")


if __name__ == "__main__":
    test_inverter()