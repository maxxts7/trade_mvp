app_name = "trade_mvp"
app_title = "Trade MVP"
app_publisher = "Trade"
app_description = "Import/export trading app built on ERPNext"
app_email = "admin@trade.local"
app_license = "MIT"

app_include_js = "/assets/trade_mvp/js/trade_mvp.js"
app_include_css = "/assets/trade_mvp/css/trade_mvp.css"

after_install = "trade_mvp.setup.after_install"

boot_session = "trade_mvp.setup.filter_bootinfo_for_trade_users"

doc_events = {
    "Sales Order": {
        "validate": "trade_mvp.setup.check_credit_limit"
    }
}

fixtures = [
    {"dt": "Role", "filters": [["name", "like", "Trade%"]]},
    {"dt": "Custom Field", "filters": [["module", "=", "Trade MVP"]]},
    {"dt": "Workspace", "filters": [["module", "=", "Trade MVP"]]},
    {"dt": "Workflow", "filters": [["name", "like", "Trade%"]]},
]
