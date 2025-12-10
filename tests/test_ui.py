from app.ui import get_main_keyboard_labels


def test_main_keyboard_labels_structure():
    labels = get_main_keyboard_labels()
    assert isinstance(labels, list)
    assert all(isinstance(row, list) for row in labels)
    assert labels[0] == ["🎙️ Обрати голос", "ℹ️ Допомога"]
    assert labels[1] == ["🎚️ Стиль/Темп"]

