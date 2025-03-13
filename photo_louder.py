import os
import json

with open("apartments.json", "r+", encoding="utf-8") as f:
    apartments = json.load(f)

    for apt in apartments:
        folder_path = f"photos/{apt['id']}/"  # Папка с фото для каждой квартиры
        apt["photo"] = sorted(
            os.path.join(folder_path, f)
            for f in os.listdir(folder_path)
            if f.lower().endswith((".jpg", ".jpeg", ".png"))
        )

    f.seek(0)
    json.dump(apartments, f, ensure_ascii=False, indent=4)
    f.truncate()

print("Фотографии обновлены в JSON!")
