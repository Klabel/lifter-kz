"""Выгрузка отчётов из Google Analytics 4 (только чтение).

Запуск:
    analytics/.venv/bin/python analytics/ga_report.py            # последние 28 дней
    analytics/.venv/bin/python analytics/ga_report.py 90         # последние 90 дней

Ключ служебного аккаунта лежит ВНЕ репозитория; путь можно переопределить
переменной окружения GA_KEY. Номер ресурса — GA_PROPERTY.
"""
import os
import sys

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange, Dimension, Filter, FilterExpression, Metric, OrderBy, RunReportRequest,
)
from google.oauth2 import service_account

KEY = os.environ.get(
    "GA_KEY",
    "/Users/roman/Documents/проекты/lifter/gen-lang-client-0057655613-53b31b7f3a11.json",
)
PROPERTY = os.environ.get("GA_PROPERTY", "519377236")
DAYS = int(sys.argv[1]) if len(sys.argv) > 1 else 28

creds = service_account.Credentials.from_service_account_file(
    KEY, scopes=["https://www.googleapis.com/auth/analytics.readonly"]
)
client = BetaAnalyticsDataClient(credentials=creds)


def contact_filter():
    return FilterExpression(filter=Filter(
        field_name="eventName",
        in_list_filter=Filter.InListFilter(values=["phone_click", "whatsapp_click"]),
    ))


def report(title, dims, mets, limit=25, order_metric=None, desc=True, flt=None, order_dim=None):
    req = RunReportRequest(
        property=f"properties/{PROPERTY}",
        date_ranges=[DateRange(start_date=f"{DAYS}daysAgo", end_date="today")],
        dimensions=[Dimension(name=d) for d in dims],
        metrics=[Metric(name=m) for m in mets],
        limit=limit,
        dimension_filter=flt,
    )
    if order_dim:
        req.order_bys = [OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name=order_dim))]
    elif mets:
        req.order_bys = [OrderBy(metric=OrderBy.MetricOrderBy(metric_name=order_metric or mets[0]), desc=desc)]
    try:
        res = client.run_report(req)
    except Exception as e:  # noqa: BLE001 — показываем ошибку и идём дальше
        print(f"\n## {title}\nОШИБКА: {e}")
        return
    print(f"\n## {title}  (строк: {res.row_count})")
    print(" | ".join(dims + mets))
    for row in res.rows:
        vals = [v.value for v in row.dimension_values]
        for v in row.metric_values:
            try:
                f = float(v.value)
                vals.append(f"{f:.2f}" if not f.is_integer() else str(int(f)))
            except ValueError:
                vals.append(v.value)
        print(" | ".join(vals))


print(f"# GA4 ресурс {PROPERTY}, последние {DAYS} дней")

report("Итого", [], ["sessions", "activeUsers", "newUsers", "engagementRate",
                     "averageSessionDuration", "screenPageViews", "eventCount", "keyEvents"])
report("По дням", ["date"], ["sessions", "activeUsers"], limit=120, order_dim="date")
report("Каналы", ["sessionDefaultChannelGroup"],
       ["sessions", "engagementRate", "averageSessionDuration", "keyEvents"])
report("Источник / канал", ["sessionSourceMedium"],
       ["sessions", "engagementRate", "averageSessionDuration", "keyEvents"])
report("Кампании Google Ads", ["sessionCampaignName"],
       ["sessions", "engagementRate", "keyEvents"])
report("Поисковые запросы Ads", ["sessionGoogleAdsQuery"], ["sessions", "keyEvents"])
report("Страницы входа", ["landingPage"],
       ["sessions", "engagementRate", "bounceRate", "averageSessionDuration", "keyEvents"])
report("Страницы", ["pagePath"],
       ["screenPageViews", "activeUsers", "userEngagementDuration"])
report("Устройства", ["deviceCategory"],
       ["sessions", "engagementRate", "averageSessionDuration", "keyEvents"])
report("Города", ["city"], ["sessions", "engagementRate", "keyEvents"])
report("События", ["eventName"], ["eventCount", "totalUsers"], limit=50)
report("Контакты по страницам", ["eventName", "pagePath"], ["eventCount"], flt=contact_filter())
report("Контакты по источникам", ["eventName", "sessionSourceMedium"], ["eventCount"], flt=contact_filter())
report("Контакты по устройствам", ["eventName", "deviceCategory"], ["eventCount"], flt=contact_filter())
report("Контакты по дням", ["date", "eventName"], ["eventCount"], limit=200, flt=contact_filter(), order_dim="date")
report("Ключевые события", ["eventName"], ["keyEvents"], order_metric="keyEvents")
# Разделение WhatsApp на запчасти / сервис / шины.
# Работает после регистрации пользовательского параметра wa_type в GA (Администратор → Специальные определения).
report("WhatsApp по типам", ["customEvent:wa_type"], ["eventCount"], flt=FilterExpression(filter=Filter(
    field_name="eventName", string_filter=Filter.StringFilter(value="whatsapp_click"))))
