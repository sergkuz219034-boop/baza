import json
import time
import urllib.request
import urllib.error
import sys

# Обеспечиваем корректный вывод кириллицы в консоли Windows
sys.stdout.reconfigure(encoding='utf-8')

TOKEN = "y0__xDopN2KBxiEx0Agh4HDkBcwyrHZ-QfXdpydrCsrSLXFLwcIuZc88lDDHQ"
ENDPOINT = "https://api.direct.yandex.com/v4/json/"

def api_call(method, param):
    data = {
        "method": method,
        "param": param,
        "token": TOKEN
    }
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(data, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        response = urllib.request.urlopen(req)
        return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code}")
        print(e.read().decode("utf-8"))
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

# Базисы для первоначальной аналитики работы на складе Ozon
phrases = [
    "работа склад озон", 
    "вакансии озон комплектовщик", 
    "работа на складе", 
    "озон склад сборщик заказов"
]
print(f"Отправляем запросы в Вордстат: {phrases}")

# Создаем отчет
report_params = {
    "Phrases": phrases,
    "GeoID": [225] # Россия
}

result = api_call("CreateNewWordstatReport", report_params)

if result and "data" in result:
    report_id = result["data"]
    print(f"Отчет успешно поставлен в очередь. ID отчета: {report_id}")
    
    # Ожидаем завершения отчета (Yandex API обычно формирует его в течение 10-60 сек)
    for _ in range(12):
        time.sleep(5)
        print("Проверяем готовность отчета...")
        status = api_call("GetWordstatReportList", [])
        if status and "data" in status:
            ready = False
            for r in status["data"]:
                if r["ReportID"] == report_id and r["StatusReport"] == "Done":
                    ready = True
                    break
            
            if ready:
                print("Отчет сформирован! Получаем данные...")
                report_data = api_call("GetWordstatReport", report_id)
                
                # Сохраняем в файл чтоб удобно было читать дальше
                with open("wordstat_results.json", "w", encoding="utf-8") as f:
                    json.dump(report_data, f, ensure_ascii=False, indent=2)
                
                print("Данные успешно сохранены в wordstat_results.json")
                break
            else:
                print("Сервер Яндекса еще собирает данные (ожидание)...")
else:
    print(f"Не удалось создать отчет. Ответ API: {result}")
