INCLUDED_APPS = [
    "state",
    "stop_reasons"
]

URL_ROUTING = [
    ("state/", "state.urls"),
    ("events/", "state.event_urls"),
    ("machines/", "state.machine_urls"),
    ("reasons/", "stop_reasons.urls")
]
