frappe.provide("trade_mvp");

$(document).ready(function () {
    const tradeRoles = [
        "Trade - Sales Executive",
        "Trade - Purchase Executive",
        "Trade - Warehouse Staff",
        "Trade - Accountant",
        "Trade - Manager",
    ];

    const isTradeUser = tradeRoles.some((r) => frappe.user_roles.includes(r));
    if (!isTradeUser) return;

    document.body.classList.add("trade-minimal");

    frappe.after_ajax(function () {
        $('[data-label="Help"]').closest(".nav-item").hide();
        $('[data-label="Explore"]').closest(".nav-item").hide();
    });
});
